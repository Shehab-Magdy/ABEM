import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../contexts/authStore";
import { useNavigate } from "react-router-dom";
import ErrorPage from "./ErrorPage";

export default function UnauthorizedPage() {
  const { t } = useTranslation("errors");
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
      title={t("session_expired_title", "Session expired")}
      description={t("session_expired_desc", "Your session has expired or you are not signed in. Please sign in again to continue.")}
      primaryAction={{ label: t("sign_in", "Sign In"), onClick: handleSignIn }}
      secondaryAction={{ label: t("go_back", "Go Back"), onClick: () => window.history.back() }}
      accentColor="#F59E0B"
    />
  );
}
