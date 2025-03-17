import base64
import logging
import requests

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from budgetapp.utils import generate_uuid_hex


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
    cleared_balance = models.PositiveIntegerField(default=0)
    last_reconciled_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ["budget", "slug"]

    def __str__(self):
        return str(self.name)


@receiver(pre_save, sender=Account)
def slugify_name(sender, instance, *args, **kwargs):
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
            raise ValueError(f"Error processing SimpleFIN setup token: {str(e)}")
