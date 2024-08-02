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
