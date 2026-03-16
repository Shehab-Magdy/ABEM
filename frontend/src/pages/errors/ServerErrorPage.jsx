import ErrorPage from "./ErrorPage";

export default function ServerErrorPage() {
  return (
    <ErrorPage
      code="500"
      icon="⚠️"
      title="Something went wrong"
      description="The server encountered an unexpected error. Our team has been notified. Please try again in a few moments."
      primaryAction={{ label: "Try Again", onClick: () => window.location.reload() }}
      secondaryAction={{ label: "Go to Dashboard", to: "/dashboard" }}
      accentColor="#EF4444"
    />
  );
}
