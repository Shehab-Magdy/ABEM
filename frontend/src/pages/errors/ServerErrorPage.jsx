import { useTranslation } from "react-i18next";
import ErrorPage from "./ErrorPage";

export default function ServerErrorPage() {
  const { t } = useTranslation("errors");

  return (
    <ErrorPage
      code="500"
      icon="⚠️"
      title={t("something_went_wrong", "Something went wrong")}
      description={t("server_error_desc", "The server encountered an unexpected error. Our team has been notified. Please try again in a few moments.")}
      primaryAction={{ label: t("try_again", "Try Again"), onClick: () => window.location.reload() }}
      secondaryAction={{ label: t("go_to_dashboard", "Go to Dashboard"), to: "/dashboard" }}
      accentColor="#EF4444"
    />
  );
}
