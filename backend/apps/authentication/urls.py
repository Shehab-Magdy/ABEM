from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, LogoutView, ChangePasswordView, RegisterView, SelfRegisterView, ProfileView

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("self-register/", SelfRegisterView.as_view(), name="auth-self-register"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("profile/", ProfileView.as_view(), name="auth-profile"),
]
