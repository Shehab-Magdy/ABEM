import { useTranslation } from "react-i18next";
import ErrorPage from "./ErrorPage";

export default function NotFoundPage() {
  const { t } = useTranslation("errors");

  return (
    <ErrorPage
      code="404"
      icon="🔍"
      title={t("page_not_found", "Page not found")}
      description={t("page_not_found_desc", "The page you're looking for doesn't exist or has been moved. Double-check the URL or head back home.")}
      primaryAction={{ label: t("go_to_dashboard", "Go to Dashboard"), to: "/dashboard" }}
      secondaryAction={{ label: t("go_back", "Go Back"), onClick: () => window.history.back() }}
      accentColor="#2563EB"
    />
  );
}
