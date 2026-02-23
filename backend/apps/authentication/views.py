"""
Authentication views – Login, Logout, Register, Profile, Change Password.
All endpoints are under /api/v1/auth/.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.mixins import log_action
from .models import User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterUserSerializer,
    UserSerializer,
)
from .tokens import CustomRefreshToken
from .permissions import IsAdminRole


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Account lockout check
        if user.is_locked:
            remaining = max(
                1, int((user.locked_until - timezone.now()).total_seconds() / 60)
            )
            return Response(
                {
                    "detail": f"Account locked. Try again in {remaining} minute(s).",
                    "locked_until": user.locked_until,
                },
                status=status.HTTP_423_LOCKED,
            )

        # Wrong password
        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                user.locked_until = timezone.now() + timedelta(
                    minutes=settings.LOGIN_LOCKOUT_DURATION_MINUTES
                )
                log_action(
                    user=user,
                    action="lockout",
                    entity="user",
                    entity_id=user.id,
                    request=request,
                )
            user.save(update_fields=["failed_login_attempts", "locked_until"])
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Inactive account
        if not user.is_active:
            return Response(
                {"detail": "This account has been deactivated."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Successful login – reset lockout counter
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=["failed_login_attempts", "locked_until"])

        refresh = CustomRefreshToken.for_user(user)

        log_action(
            user=user,
            action="login",
            entity="user",
            entity_id=user.id,
            request=request,
        )

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Token is invalid or already blacklisted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_action(
            user=request.user,
            action="logout",
            entity="user",
            entity_id=request.user.id,
            request=request,
        )

        return Response({"detail": "Successfully logged out."})


# ── Register (Admin only) ──────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        log_action(
            user=request.user,
            action="create",
            entity="user",
            entity_id=user.id,
            changes={"email": {"after": user.email}, "role": {"after": user.role}},
            request=request,
        )

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# ── Change Password ────────────────────────────────────────────────────────────

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])

        log_action(
            user=request.user,
            action="change_password",
            entity="user",
            entity_id=request.user.id,
            request=request,
        )

        return Response({"detail": "Password changed successfully."})


# ── Profile ────────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        old_values = {
            field: getattr(request.user, field)
            for field in serializer.validated_data
        }
        serializer.save()

        log_action(
            user=request.user,
            action="update",
            entity="user",
            entity_id=request.user.id,
            changes={
                field: {
                    "before": str(old_values[field]),
                    "after": str(serializer.validated_data[field]),
                }
                for field in serializer.validated_data
            },
            request=request,
        )

        return Response(UserSerializer(request.user).data)
