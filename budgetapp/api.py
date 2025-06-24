import logging
import jwt

from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import NinjaAPI
from ninja.security import APIKeyHeader, HttpBearer, django_auth

from accounts.apis import router as accounts_router
from authentication.api import router as authentication_router
from budgets.apis import router as budgets_router
from envelopes.apis import router as envelopes_router
from envelopes.category_apis import router as category_router
from reports.apis import router as reports_router
from transactions.apis import router as transactions_router

from .models import APIKey

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthBearer(HttpBearer):
    def __init__(self):
        super().__init__()
        logger.debug("AuthBearer initialized")

    def authenticate(self, request, token):
        logger.debug("=== AuthBearer.authenticate called ===")
        logger.debug(
            "Token received: %s",
            token[:50] + "..." if token and len(token) > 50 else token,
        )

        try:
            # Decode JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            logger.debug("JWT payload decoded: %s", payload)
            user_id = payload.get("user_id")

            if user_id:
                user = User.objects.get(id=user_id)
                logger.debug("User authenticated via JWT: %s", user)
                request.auth = user
                request.user = user
                return user
        except jwt.ExpiredSignatureError:
            logger.debug("JWT token expired")
        except jwt.InvalidTokenError as e:
            logger.debug("Invalid JWT token: %s", e)
        except User.DoesNotExist:
            logger.debug("User not found for JWT token with user_id: %s", user_id)
        except Exception as e:
            logger.debug("JWT authentication error: %s", e)

        logger.debug("JWT authentication failed, trying API key fallback")
        # Fallback to API key authentication
        user = APIKey.get_user_from_key(token)
        if user:
            logger.debug("User authenticated via API key: %s", user)
            return user

        logger.debug("All authentication methods failed")
        return None


class ApiKeyAuth(APIKeyHeader):
    param_name = "X-API-Key"

    def __init__(self):
        super().__init__()
        logger.debug("ApiKeyAuth initialized")

    def authenticate(self, request, key):
        logger.debug(
            "ApiKeyAuth.authenticate called with key: %s",
            key[:20] + "..." if key and len(key) > 20 else key,
        )
        user = APIKey.get_user_from_key(key)
        if user:
            logger.debug("Successfully authenticated user: %s", user)
            return user
        logger.debug("Authentication failed: Invalid API key")
        return None


# Create auth instances
auth_bearer = AuthBearer()
api_key_auth = ApiKeyAuth()

# Initialize API
api = NinjaAPI(
    title="EnvelopeBudget API",
    csrf=False,
    auth=[auth_bearer, api_key_auth, django_auth],
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

# Add routers
api.add_router("", transactions_router)
api.add_router("/accounts", accounts_router)
api.add_router("/auth", authentication_router)
api.add_router("/budgets", budgets_router)
api.add_router("/categories", category_router)
api.add_router("/envelopes", envelopes_router)
api.add_router("/reports/", reports_router)
