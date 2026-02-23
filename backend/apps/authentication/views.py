"""Authentication views – stubs to be fully implemented in Sprint 1."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # TODO Sprint 1: implement JWT login with lockout logic
        return Response({"detail": "Not implemented yet"}, status=501)


class LogoutView(APIView):
    def post(self, request):
        # TODO Sprint 1: blacklist refresh token
        return Response({"detail": "Not implemented yet"}, status=501)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # TODO Sprint 1: admin-only user creation
        return Response({"detail": "Not implemented yet"}, status=501)


class ChangePasswordView(APIView):
    def patch(self, request):
        # TODO Sprint 1: password change with current password confirmation
        return Response({"detail": "Not implemented yet"}, status=501)


class ProfileView(APIView):
    def get(self, request):
        # TODO Sprint 1: return current user profile
        return Response({"detail": "Not implemented yet"}, status=501)

    def patch(self, request):
        # TODO Sprint 1: update profile fields
        return Response({"detail": "Not implemented yet"}, status=501)
