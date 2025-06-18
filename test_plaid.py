import os
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid import Environment

client_id = os.environ.get("PLAID_CLIENT_ID")
secret = os.environ.get("PLAID_SANDBOX_SECRET")

print(f"Client ID: {client_id}")
print(f"Secret exists: {bool(secret)}")

configuration = Configuration(
    host=Environment.Sandbox,
    api_key={
        "clientId": client_id,
        "secret": secret,
    },
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Test the connection
try:
    link_request = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="Test App",
        country_codes=[CountryCode("US")],
        language="en",
        user=LinkTokenCreateRequestUser(client_user_id="test_user"),
    )
    response = client.link_token_create(link_request)
    print("Success! Credentials are working.")
except Exception as e:
    print(f"Error: {e}")
