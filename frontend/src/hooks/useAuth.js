/**
 * Convenience hook that exposes the auth store plus derived helpers.
 */
import { useAuthStore } from "../contexts/authStore";

export function useAuth() {
  const { user, accessToken, login, logout, setUser } = useAuthStore();

  return {
    user,
    accessToken,
    isAuthenticated: !!accessToken,
    isAdmin: user?.role === "admin",
    isOwner: user?.role === "owner",
    login,
    logout,
    setUser,
  };
}
