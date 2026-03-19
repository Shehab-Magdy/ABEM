import { useTranslation } from "react-i18next";
import ErrorPage from "./ErrorPage";

export default function ForbiddenPage() {
  const { t } = useTranslation("errors");

  return (
    <ErrorPage
      code="403"
      icon="🚫"
      title={t("access_denied", "Access denied")}
      description={t("access_denied_desc", "You don't have permission to view this page. Contact your building admin if you think this is a mistake.")}
      primaryAction={{ label: t("go_to_dashboard", "Go to Dashboard"), to: "/dashboard" }}
      secondaryAction={{ label: t("go_back", "Go Back"), onClick: () => window.history.back() }}
      accentColor="#EF4444"
    />
  );
}
