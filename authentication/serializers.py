from ninja import Schema
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(Schema):
    email: str
    password: str
    # Add any other fields you require


class LoginSerializer(Schema):
    email: str
    password: str
