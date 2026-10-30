"""
Authentication views – Login, Logout, Register, Profile, Change Password.
All endpoints are under /api/v1/auth/.
"""
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from django.utils.translation import gettext_lazy as _
from apps.audit.mixins import log_action
from .models import User
from .serializers import (
    ChangePasswordSerializer,
    ForceChangePasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterUserSerializer,
    SelfRegisterSerializer,
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
                {"detail": _("No account found with this email address."), "code": "email_not_found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Account lockout check
        if user.is_locked:
            remaining = max(
                1, int((user.locked_until - timezone.now()).total_seconds() / 60)
            )
            return Response(
                {
                    "detail": _("Account locked. Try again in %(minutes)s minute(s).") % {"minutes": remaining},
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
                {"detail": _("Incorrect password."), "code": "wrong_password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Inactive account
        if not user.is_active:
            return Response(
                {"detail": _("This account has been deactivated.")},
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
                "user": UserSerializer(user, context={"request": request}).data,
            }
        )


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": _("Refresh token is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": _("Token is invalid or already blacklisted.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_action(
            user=request.user,
            action="logout",
            entity="user",
            entity_id=request.user.id,
            request=request,
        )

        return Response({"detail": _("Successfully logged out.")})


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

        return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_201_CREATED)


# ── Self-Register (public, role forced to 'owner') ────────────────────────────

class SelfRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SelfRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = CustomRefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ── Change Password ────────────────────────────────────────────────────────────

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.must_change_password = False
        request.user.save(update_fields=["password", "must_change_password"])

        log_action(
            user=request.user,
            action="change_password",
            entity="user",
            entity_id=request.user.id,
            request=request,
        )

        return Response({"detail": _("Password changed successfully.")})


# ── Force Change Password (after admin reset) ────────────────────────────

class ForceChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.must_change_password:
            return Response(
                {"detail": _("Password change is not required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ForceChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.must_change_password = False
        request.user.save(update_fields=["password", "must_change_password"])

        log_action(
            user=request.user,
            action="force_change_password",
            entity="user",
            entity_id=request.user.id,
            request=request,
        )

        return Response(
            {"detail": _("Password changed successfully."), "user": UserSerializer(request.user, context={"request": request}).data}
        )


# ── Profile ────────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)

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

        return Response(UserSerializer(request.user, context={"request": request}).data)


# ── Forgot / reset password (emailed link) ───────────────────────────────────

class ForgotPasswordView(APIView):
    """POST /auth/forgot-password/ {email}. Always answers 200 so emails cannot be probed."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        email = (request.data.get("email") or "").strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first() if email else None
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?uid={uid}&token={token}"
            send_mail(
                subject="إعادة تعيين كلمة المرور | Reset your password — 3maracom",
                message=(
                    f"لإعادة تعيين كلمة المرور افتح الرابط التالي:\n{link}\n\n"
                    f"To reset your password open this link:\n{link}\n\n"
                    "إذا لم تطلب ذلك تجاهل هذه الرسالة. / If you did not ask for this, ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        return Response({"detail": _("If that email is registered, a reset link has been sent.")})


class ResetPasswordView(APIView):
    """POST /auth/reset-password/ {uid, token, password, confirm_password}."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode

        from .validators import validate_password_complexity

        password = request.data.get("password") or ""
        if password != request.data.get("confirm_password"):
            return Response({"detail": _("Passwords do not match.")}, status=400)
        try:
            validate_password_complexity(password)
        except DjangoValidationError as exc:
            return Response({"detail": " ".join(exc.messages)}, status=400)

        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(request.data.get("uid", ""))))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError, DjangoValidationError):
            user = None
        if user is None or not default_token_generator.check_token(user, request.data.get("token", "")):
            return Response({"detail": _("This reset link is invalid or has expired.")}, status=400)

        user.set_password(password)
        user.must_change_password = False
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=["password", "must_change_password", "failed_login_attempts", "locked_until"])
        log_action(user=user, action="reset_password", entity="user", entity_id=user.id, request=request)
        return Response({"detail": _("Password has been reset. You can now sign in.")})


# ── Delete my account ────────────────────────────────────────────────────────

class DeleteAccountView(APIView):
    """
    POST /auth/delete-account/ {password}

    Removes the person, keeps the books: the account is deactivated and its personal data
    (name, email, phone, picture, memberships) is erased, while payments, expense shares and the
    audit log stay attached to an anonymised user. The primary admin of a building must hand it
    over first so no building is left without an administrator.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.apartments.models import Apartment
        from apps.buildings.models import Building, BuildingCoAdmin, UserBuilding

        user = request.user
        if not user.check_password(request.data.get("password") or ""):
            return Response({"detail": _("Password is incorrect.")}, status=status.HTTP_400_BAD_REQUEST)

        owned = Building.objects.filter(admin=user, deleted_at__isnull=True)
        if owned.exists():
            return Response(
                {"detail": _("You are the administrator of a building. Hand it over to another admin before deleting your account.")},
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            for apt in Apartment.objects.filter(owner=user):
                apt.owner = None
                apt.save(update_fields=["owner", "updated_at"])
            Apartment.owners.through.objects.filter(user_id=user.pk).delete()
            UserBuilding.objects.filter(user=user).delete()
            BuildingCoAdmin.objects.filter(user=user).delete()

            log_action(user=user, action="delete_account", entity="user", entity_id=user.id, request=request)

            user.email = f"deleted-{user.pk}@deleted.invalid"
            user.first_name = ""
            user.last_name = ""
            user.phone = ""
            user.profile_picture = None
            user.is_active = False
            user.set_unusable_password()
            user.save()

            # sign the person out everywhere
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

            for token in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=token)

        return Response({"detail": _("Your account has been deleted.")})
