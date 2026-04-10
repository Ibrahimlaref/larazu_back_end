from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def error_response(message, status_code=400):
    return Response({"error": message}, status=status_code)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        email = (data.get("email") or "").strip()
        password = data.get("password")
        first_name = (data.get("firstName") or "").strip()
        last_name = (data.get("lastName") or "").strip()
        phone = (data.get("phone") or "").strip()
        if not email:
            return error_response("email is required", 400)
        if not password:
            return error_response("password is required", 400)
        if User.objects.filter(email__iexact=email).exists():
            return error_response("Email already registered", 409)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        if phone:
            if hasattr(user, "phone"):
                user.phone = phone
                user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": {
                "id": str(user.pk) if hasattr(user.pk, "hex") else user.pk,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password")
        if not email or not password:
            return error_response("email and password are required", 400)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return error_response("Invalid credentials", 401)
        user = authenticate(request, username=user.username, password=password)
        if not user:
            return error_response("Invalid credentials", 401)
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": {
                "id": str(user.pk) if hasattr(user.pk, "hex") else user.pk,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)
