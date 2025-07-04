import base64
import datetime
import logging
import urllib

import requests

from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from budgetapp.utils import generate_uuid_hex
from transactions.models import Payee, Transaction


logger = logging.getLogger(__name__)


class Account(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    type = models.CharField(max_length=255)
    on_budget = models.BooleanField(default=True)
    closed = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    balance = models.IntegerField(default=0)
    cleared_balance = models.IntegerField(default=0)
    last_reconciled_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(default=False)
    sfin_id = models.CharField(max_length=255, blank=True, null=True)
    sfin_last_imported_on = models.DateTimeField(blank=True, null=True)
    plaid_access_token = models.CharField(max_length=255, blank=True, null=True)
    plaid_account_id = models.CharField(max_length=255, blank=True, null=True)
    plaid_item_id = models.CharField(max_length=255, blank=True, null=True)
    plaid_account_type = models.CharField(max_length=50, blank=True, null=True)
    plaid_account_subtype = models.CharField(max_length=50, blank=True, null=True)
    plaid_official_name = models.CharField(max_length=255, blank=True, null=True)
    plaid_mask = models.CharField(max_length=10, blank=True, null=True)
    plaid_last_sync = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ["budget", "slug"]

    @property
    def is_debt_account(self):
        """
        Check if this account is a debt account (credit card or loan).
        """
        debt_types = ["credit_card", "loan", "credit", "line_of_credit"]
        return self.type in debt_types

    def __str__(self):
        return str(self.name)

    @property
    def balance_dollars(self):
        return round(self.balance / 1000, 2)


@receiver(pre_save, sender=Account)
def slugify_name(sender, instance, *args, **kwargs):  # pylint: disable=unused-argument
    if not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        n = 1
        while Account.objects.filter(budget=instance.budget, slug=slug).exists():
            slug = f"{base_slug}-{n}"
            n += 1
        instance.slug = slug


class SimpleFINConnection(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    budget = models.OneToOneField("budgets.Budget", on_delete=models.CASCADE)
    access_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SimpleFINConnection for {self.budget.name}"

    @classmethod
    def create_from_setup_token(cls, budget, setup_token):
        """
        Create a new SimpleFINConnection from a setup token.

        Args:
            budget: The Budget instance to associate with this connection
            setup_token: Base64 encoded setup token from SimpleFIN

        Returns:
            The created SimpleFINConnection instance

        Raises:
            ValueError: If the setup token is invalid or the request fails
        """

        try:
            # Check if a connection already exists for this budget
            logger.debug(
                "Checking for existing SimpleFIN connection for budget %s", budget.id
            )
            existing_connection = cls.objects.filter(budget=budget).first()
            if existing_connection:
                logger.debug(
                    "Found existing SimpleFIN connection %s", existing_connection.id
                )
                raise ValueError(
                    "A SimpleFIN connection already exists for this budget"
                )

            # Decode the setup token from base64
            logger.debug("Decoding setup token")
            decoded_token = base64.b64decode(setup_token).decode("utf-8")

            # The decoded token should be a URL
            logger.debug("Decoded token: %s", decoded_token)
            if not decoded_token.startswith("http"):
                logger.debug("Invalid token format - does not start with http")
                raise ValueError("Invalid setup token format")

            # Make a POST request to the decoded URL to get the access URL
            logger.debug("Making POST request to setup token URL")
            response = requests.post(decoded_token, timeout=10)

            if response.status_code != 200:
                logger.debug(
                    "Request failed with status code %d: %s",
                    response.status_code,
                    response.text,
                )
                raise ValueError(f"Failed to exchange setup token: {response.text}")

            # Extract the access URL from the response
            access_url = response.text
            logger.debug("Access URL: %s", access_url)

            if not access_url:
                logger.debug("No access_url found in response data")
                raise ValueError("No access_url in response")

            # Create and save the SimpleFINConnection
            logger.debug("Creating new SimpleFIN connection for budget %s", budget.id)
            connection = cls(budget=budget, access_url=access_url)
            connection.save()
            logger.debug("Created SimpleFIN connection %s", connection.id)

            return connection
        except Exception as e:
            logger.error("Error processing SimpleFIN setup token: %s", str(e))
            raise ValueError(f"Error processing SimpleFIN setup token: {str(e)}") from e

    def get_accounts(self):
        """
        Retrieve accounts from the SimpleFIN connection's access URL.

        Sends a GET request to the configured access URL's '/accounts' endpoint
        and returns the JSON response containing account information.

        Returns:
            dict: A JSON-decoded response containing account details
        """
        endpoint = f"{self.access_url}/accounts?balances-only=true"
        response = requests.get(endpoint, timeout=30)
        # logger.info("SimpleFIN Accounts: %s", response.json())
        return response.json()

    def import_account(self, sfin_data, sfin_account_id, account_type="account"):
        """
        Import a SimpleFIN account into the current budget.

        Finds a specific account from SimpleFIN data by its account ID and creates
        a corresponding Account object in the database with transformed details.

        Args:
            sfin_data (dict): The complete SimpleFIN account data dictionary.
            sfin_account_id (str): The specific account ID to import.
            account_type (str, optional): The type of account to create. Defaults to "account".

        Returns:
            dict: An error dictionary if the account is not found, otherwise None.
        """
        sfin_account = next(
            (
                account
                for account in sfin_data.get("accounts", [])
                if account.get("id") == sfin_account_id
            ),
            None,
        )
        if not sfin_account:
            return {"error": "Account not found in SimpleFIN data"}

        account_name = sfin_account["org"]["name"] + ": " + sfin_account["name"]

        logger.info("Importing SimpleFIN account: %s", sfin_account)
        logger.info("Account type: %s", account_type)
        logger.info("Account name: %s", account_name)
        logger.info("Slug: %s", slugify(account_name))

        account = Account.objects.create(
            budget=self.budget,
            name=account_name,
            slug=slugify(account_name),
            type=account_type,
            balance=int(float(sfin_account["balance"]) * 1000),
            cleared_balance=int(float(sfin_account["balance"]) * 1000),
            sfin_id=sfin_account["id"],
        )

        return account

    def get_transactions(
        self,
        account_id=None,
        start_date=None,
        end_date=None,
        include_pending=True,
        import_transactions=True,
        update_account_amounts=True,
    ):
        """
        Retrieve transactions from the SimpleFIN connection's access URL.

        Fetches transactions with optional filtering by account, date range, and pending status.

        Args:
            account_id (str, optional): Specific account to retrieve transactions for.
            start_date (str, optional): Start date for transaction filtering in 'YYYY-MM-DD' format.
            end_date (str, optional): End date for transaction filtering in 'YYYY-MM-DD' format.
            include_pending (bool, optional): Whether to include pending transactions.
                Defaults to True.
            import_transactions (bool, optional): Whether to import the transactions to a
                matching EB account. Defaults to True.
            update_account_amounts (bool, optional): Whether to update the account balances
                after importing transactions. Defaults to True.

        Returns:
            dict: A JSON-decoded response containing transaction details from the SimpleFIN API.
        """
        parameters = {}
        buffer_days = 4
        logger.info("Retrieving transactions from SimpleFIN...")

        # If account_id is provided, use the last imported date with a buffer
        if account_id:
            parameters["account"] = account_id

            # If start_date is not explicitly provided, try to use the last imported date
            if not start_date:
                try:
                    account = Account.objects.get(sfin_id=account_id)
                    if account.sfin_last_imported_on:
                        # Use the last imported date minus a 3-day buffer to ensure we don't miss
                        # any transactions
                        buffer_date = (
                            account.sfin_last_imported_on
                            - datetime.timedelta(days=buffer_days)
                        )
                        parameters["start-date"] = int(buffer_date.timestamp())
                        logger.info(
                            "Using last imported date with buffer: %s",
                            buffer_date.strftime("%Y-%m-%d"),
                        )
                except Account.DoesNotExist:
                    logger.warning("No account found with sfin_id: %s", account_id)
        else:
            if not start_date:
                # Use the furthest back start date of all accounts that have sfin_last_imported_on
                accounts = Account.objects.filter(sfin_last_imported_on__isnull=False)
                if accounts.exists():
                    start_date = (
                        accounts.order_by("sfin_last_imported_on")
                        .first()
                        .sfin_last_imported_on
                    )
                    buffer_date = start_date - datetime.timedelta(days=buffer_days)
                    parameters["start-date"] = int(buffer_date.timestamp())
                    logger.info(
                        "Using date: %s",
                        buffer_date.strftime("%Y-%m-%d"),
                    )

        # If start_date is explicitly provided, use it
        if start_date and not parameters.get("start-date"):
            parameters["start-date"] = int(
                datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp()
            )

        if end_date:
            parameters["end-date"] = int(
                datetime.datetime.strptime(end_date, "%Y-%m-%d")
                .replace(hour=23, minute=59, second=59)
                .timestamp()
            )

        if include_pending:
            parameters["pending"] = 1 if include_pending else 0

        endpoint = f"{self.access_url}/accounts?{urllib.parse.urlencode(parameters)}"
        logger.info("SimpleFIN Transactions endpoint: %s", endpoint)

        try:
            response = requests.get(endpoint, timeout=30)

            # Log the response for debugging
            logger.debug("SimpleFIN API response status: %s", response.status_code)
            logger.debug(
                "SimpleFIN API response content: %s...", response.text[:200]
            )  # Log first 200 chars

            # Check if response is successful and contains content
            if response.status_code != 200:
                return {
                    "error": f"SimpleFIN API returned status code {response.status_code}",
                    "details": response.text,
                }

            if not response.text.strip():
                return {"error": "SimpleFIN API returned empty response"}

            if import_transactions:
                # Import the transactions to the budget
                self.import_sfin_transactions(response.json())

            if update_account_amounts:
                # Update the account balances
                self.update_sfin_account_balances(response.json())

            return response.json()
        except requests.exceptions.JSONDecodeError as e:
            logger.error("JSON decode error: %s", str(e))
            return {
                "error": "Failed to parse SimpleFIN API response as JSON",
                "details": str(e),
                "raw_response": (
                    response.text if "response" in locals() else "No response"
                ),
            }
        except requests.exceptions.RequestException as e:
            logger.error("Request error: %s", str(e))
            return {"error": "Failed to connect to SimpleFIN API", "details": str(e)}

        except (ValueError, TypeError) as e:
            logger.error("Data processing error in get_transactions: %s", str(e))
            return {
                "error": "Error processing transaction data",
                "details": str(e),
            }

    def import_sfin_transactions(self, sfin_data, update_account_amounts=True):
        logger.info("Importing SimpleFIN transactions, data: %s", sfin_data)
        for sfin_account in sfin_data.get("accounts", []):
            try:
                account = Account.objects.get(sfin_id=sfin_account.get("id"))
                logger.info("Found account for SimpleFIN account: %s", account)
            except Account.DoesNotExist:
                logger.warning(
                    "No account found for SimpleFIN account: %s", sfin_account["id"]
                )
                continue
            duplicate_transaction_ids = []
            created_transaction_ids = []
            for transaction in sfin_account.get("transactions", []):
                logger.info("Importing SimpleFIN transaction: %s", transaction)
                # Check for existing transaction with the same sfin_id or import_id
                transaction_exists = (
                    Transaction.objects.include_deleted()
                    .filter(
                        budget=self.budget,
                        account=account,
                    )
                    .filter(
                        models.Q(import_id=transaction.get("id"))
                        | models.Q(sfin_id=transaction.get("id"))
                    )
                    .first()
                )

                if transaction_exists:
                    # Update the existing transaction if it was pending and new one is not
                    if transaction_exists.pending and not transaction.get(
                        "pending", False
                    ):
                        transaction_exists.pending = False
                        transaction_exists.cleared = True
                        transaction_exists.save()
                        logger.info(
                            "Updated transaction %s from pending to cleared",
                            transaction_exists.id,
                        )
                    else:
                        # If transaction exists, add its ID to duplicate_transaction_ids
                        duplicate_transaction_ids.append(transaction_exists.id)
                else:
                    # Create a new Transaction for each unique transaction
                    try:
                        payee = None
                        if transaction["payee"]:
                            payee = Payee.objects.get_or_create(
                                name=transaction["payee"], budget=self.budget
                            )[0]

                        new_transaction = Transaction.objects.create(
                            budget=self.budget,
                            account=account,
                            date=datetime.datetime.fromtimestamp(
                                transaction["transacted_at"]
                            ).date(),
                            amount=int(float(transaction["amount"]) * 1000),
                            memo=transaction["description"],
                            payee=payee,
                            sfin_id=transaction["id"],
                            import_payee_name=transaction["payee"],
                            cleared=False if transaction.get("pending") else True,
                            pending=transaction.get("pending", False),
                        )
                        created_transaction_ids.append(new_transaction.id)
                    except (
                        ValueError,
                        TypeError,
                        KeyError,
                        Payee.DoesNotExist,
                        Transaction.DoesNotExist,
                    ) as e:
                        logger.error(
                            "Error creating transaction: %s for transaction: %s",
                            str(e),
                            transaction,
                        )
            # Update the last imported date for this account
            account.sfin_last_imported_on = datetime.datetime.now()
            account.save(update_fields=["sfin_last_imported_on"])

    def update_sfin_account_balances(self, sfin_data):
        """
        Update the balances of SimpleFIN accounts based on the provided data.

        Args:
            sfin_data (dict): The data received from the SimpleFIN API.
        """
        logger.info("⚖️ Updating SimpleFIN account balances...")
        for sfin_account in sfin_data.get("accounts", []):
            try:
                account = Account.objects.get(sfin_id=sfin_account.get("id"))
                logger.info("Found account for SimpleFIN account: %s", account)
            except Account.DoesNotExist:
                logger.warning(
                    "No account found for SimpleFIN account: %s", sfin_account["id"]
                )
                continue
            balance = int(float(sfin_account.get("balance")) * 1000)
            if account:
                account.balance = balance
                account.save(update_fields=["balance"])
                logger.info(
                    "✅ Updated balance for account: %s; balance: %s",
                    account.name,
                    balance,
                )


@receiver(post_save, sender=Account)
def create_linked_envelope_for_debt_account(sender, instance, created, **kwargs):
    """
    Create a linked envelope for credit card and loan accounts.
    """
    # Import here to avoid circular imports
    from envelopes.models import Category, Envelope

    debt_account_types = ["credit_card", "loan", "credit", "line_of_credit"]

    if instance.type.lower() in debt_account_types and not instance.deleted:
        # Check if envelope already exists
        existing_envelope = Envelope.objects.filter(linked_account=instance).first()
        if existing_envelope:
            return

        # Get or create "Debt" category
        debt_category, _ = Category.objects.get_or_create(
            budget=instance.budget,
            name="Debt",
            deleted=False,
            defaults={"sort_order": 999},
        )

        # Create the linked envelope
        envelope_name = f"{instance.name} Payments"
        Envelope.objects.create(
            budget=instance.budget,
            category=debt_category,
            name=envelope_name,
            balance=0,
            linked_account=instance,
        )

        logger.info(
            "Created linked envelope '%s' for account '%s'",
            envelope_name,
            instance.name,
        )


@receiver(pre_save, sender=Account)
def update_linked_envelope_name(sender, instance, **kwargs):
    """
    Update the linked envelope name when account name changes.
    """
    if instance.pk:  # Only for existing accounts
        try:
            from envelopes.models import Envelope

            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.name != instance.name:
                envelope = Envelope.objects.filter(linked_account=instance).first()
                if envelope:
                    envelope.name = f"{instance.name} Payments"
                    envelope.save(update_fields=["name"])
                    logger.info(
                        "Updated linked envelope name to '%s'",
                        envelope.name,
                    )
        except sender.DoesNotExist:
            pass
