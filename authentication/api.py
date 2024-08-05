from ninja import Router
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string


from budgetapp.models import User, APIKey

import logging

logger = logging.getLogger(__name__)


from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    APIKeyCreateSerializer,
    APIKeyResponseSerializer,
)

router = Router()


@router.post("/register")
def register(request, data: RegisterSerializer):
    # Validate and create user
    user = User.objects.create_user(email=data.email, password=data.password)
    # Send confirmation email (use django-allauth functionality)
    # ...

    return {"success": True, "message": "User registered successfully."}


@router.post("/login")
def login(request, data: LoginSerializer):
    user = authenticate(email=data.email, password=data.password)
    if user:
        # Generate and return token (JWT or similar)
        # ...
        token = "foobar"
        return {"success": True, "token": token}
    else:
        return {"success": False, "message": "Invalid credentials"}


@router.post("/api-key", response=APIKeyResponseSerializer)
def create_api_key(request, data: APIKeyCreateSerializer):
    user = request.auth
    logger.debug("Creating API key for user: %s", user)

    if not user:
        logger.error("User not found")
        raise get_object_or_404(User, pk=1)

    api_key = APIKey.create_new_key(
        user, termination_date=data.termination_date, note=data.note
    )
    logger.debug("API key created: %s", api_key)

    return APIKeyResponseSerializer.from_orm(api_key)


@router.delete("/api-key/{api_key_id}")
def delete_api_key(request, api_key_id: str):
    user = request.auth
    logger.debug("Deleting API key %s for user: %s", api_key_id, user)

    if not user:
        logger.error("User not found")
        return {"success": False, "message": "User not authenticated"}

    try:
        api_key = APIKey.objects.get(id=api_key_id, user=user)
        api_key.delete()
        logger.debug("API key deleted: %s", api_key_id)
        return {"success": True, "message": "API key deleted successfully"}
    except APIKey.DoesNotExist:
        logger.error("API key not found: %s", api_key_id)
        return {"success": False, "message": "API key not found"}
