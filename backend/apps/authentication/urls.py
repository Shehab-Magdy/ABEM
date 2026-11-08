from django.urls import path

from .views import (
    CookieTokenRefreshView,
    DeleteAccountView,
    GoogleSignInView,
    LogoutView,
    OTPRequestView,
    OTPVerifyView,
    ProfileView,
    RegisterView,
    RevokeAllDevicesView,
    SelfRegisterView,
    SessionListView,
    SessionRevokeView,
)

urlpatterns = [
    path("otp/request/", OTPRequestView.as_view(), name="auth-otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="auth-otp-verify"),
    path("google/", GoogleSignInView.as_view(), name="auth-google"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", CookieTokenRefreshView.as_view(), name="auth-token-refresh"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("self-register/", SelfRegisterView.as_view(), name="auth-self-register"),
    path("delete-account/", DeleteAccountView.as_view(), name="auth-delete-account"),
    path(
        "devices/revoke-all/",
        RevokeAllDevicesView.as_view(),
        name="auth-devices-revoke-all",
    ),
    path("sessions/", SessionListView.as_view(), name="auth-sessions"),
    path(
        "sessions/<int:session_pk>/revoke/",
        SessionRevokeView.as_view(),
        name="auth-session-revoke",
    ),
    path("profile/", ProfileView.as_view(), name="auth-profile"),
]
