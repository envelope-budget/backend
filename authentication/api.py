from ninja import Router
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404


from .serializers import LoginSerializer, RegisterSerializer

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
