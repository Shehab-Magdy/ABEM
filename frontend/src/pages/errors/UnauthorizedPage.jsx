import { useAuthStore } from "../../contexts/authStore";
import { useNavigate } from "react-router-dom";
import ErrorPage from "./ErrorPage";

export default function UnauthorizedPage() {
  const { logout } = useAuthStore();
  const navigate = useNavigate();

  const handleSignIn = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <ErrorPage
      code="401"
      icon="🔒"
      title="Session expired"
      description="Your session has expired or you are not signed in. Please sign in again to continue."
      primaryAction={{ label: "Sign In", onClick: handleSignIn }}
      secondaryAction={{ label: "Go Back", onClick: () => window.history.back() }}
      accentColor="#F59E0B"
    />
  );
}
