import ErrorPage from "./ErrorPage";

export default function ForbiddenPage() {
  return (
    <ErrorPage
      code="403"
      icon="🚫"
      title="Access denied"
      description="You don't have permission to view this page. Contact your building admin if you think this is a mistake."
      primaryAction={{ label: "Go to Dashboard", to: "/dashboard" }}
      secondaryAction={{ label: "Go Back", onClick: () => window.history.back() }}
      accentColor="#EF4444"
    />
  );
}
