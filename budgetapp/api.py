import logging

from ninja import NinjaAPI
from ninja.security import APIKeyHeader, HttpBearer, django_auth

from accounts.apis import router as accounts_router
from authentication.api import router as authentication_router
from budgets.apis import router as budgets_router
from envelopes.apis import router as envelopes_router
from envelopes.category_apis import router as category_router
from transactions.apis import router as transactions_router

from .models import APIKey

logger = logging.getLogger(__name__)


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        user = APIKey.get_user_from_key(token)
        if user:
            logger.debug("User authenticated: %s", user)
            request.user = user
            return user
        logger.debug("Authentication failed: Invalid token")
        return None


class ApiKeyAuth(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        user = APIKey.get_user_from_key(key)
        if user:
            logger.debug("Successfully authenticated user: %s", user)
            request.user = user
            return user
        logger.debug("Authentication failed: Invalid API key")
        return None


api = NinjaAPI(
    title="EnvelopeBudget API",
    csrf=False,
    auth=[AuthBearer(), ApiKeyAuth(), django_auth],
    openapi_extra={
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer"},
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            }
        },
        "security": [{"BearerAuth": []}, {"ApiKeyAuth": []}],
    },
)

api.add_router("/budgets", budgets_router)
api.add_router("/accounts", accounts_router)
api.add_router("/envelopes", envelopes_router)
api.add_router("/categories", category_router)
api.add_router("", transactions_router)
api.add_router("/auth", authentication_router)
