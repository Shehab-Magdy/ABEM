import ErrorPage from "./ErrorPage";

export default function NotFoundPage() {
  return (
    <ErrorPage
      code="404"
      icon="🔍"
      title="Page not found"
      description="The page you're looking for doesn't exist or has been moved. Double-check the URL or head back home."
      primaryAction={{ label: "Go to Dashboard", to: "/dashboard" }}
      secondaryAction={{ label: "Go Back", onClick: () => window.history.back() }}
      accentColor="#2563EB"
    />
  );
}
