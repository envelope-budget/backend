from ninja import Schema
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


class RegisterSerializer(Schema):
    email: str
    password: str
    # Add any other fields you require


class LoginSerializer(Schema):
    email: str
    password: str


class APIKeyCreateSerializer(Schema):
    termination_date: datetime = None
    note: str = None


class APIKeyResponseSerializer(Schema):
    key: str
    created_at: datetime
    termination_date: datetime = None
    note: str = None
