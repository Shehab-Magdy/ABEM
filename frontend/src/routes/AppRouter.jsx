import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "../contexts/authStore";

// Layout
import DashboardLayout from "../components/common/DashboardLayout";

// Auth
import LoginPage from "../pages/auth/LoginPage";
import RegisterPage from "../pages/auth/RegisterPage";

// Dashboards
import AdminDashboardPage from "../pages/dashboard/AdminDashboardPage";
import OwnerDashboardPage from "../pages/dashboard/OwnerDashboardPage";

// Sprint 1
import UsersPage from "../pages/users/UsersPage";
import ProfilePage from "../pages/profile/ProfilePage";

// Future sprints (stubs)
import BuildingsPage from "../pages/buildings/BuildingsPage";
import ExpensesPage from "../pages/expenses/ExpensesPage";
import PaymentsPage from "../pages/payments/PaymentsPage";
import NotificationCenterPage from "../pages/notifications/NotificationCenterPage";
import AuditLogPage from "../pages/audit/AuditLogPage";

// ── Route guards ──────────────────────────────────────────────────────────────

function RequireAuth({ children }) {
  const { accessToken } = useAuthStore();
  return accessToken ? children : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin") return <Navigate to="/dashboard" replace />;
  return children;
}

// ── Router ────────────────────────────────────────────────────────────────────

export default function AppRouter() {
  const { user } = useAuthStore();

  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected – all routes share the DashboardLayout shell */}
      <Route
        path="/"
        element={
          <RequireAuth>
            <DashboardLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />

        {/* Dashboard – role-split */}
        <Route
          path="dashboard"
          element={user?.role === "admin" ? <AdminDashboardPage /> : <OwnerDashboardPage />}
        />

        {/* Sprint 1 */}
        <Route path="profile" element={<ProfilePage />} />
        <Route path="users" element={<RequireAdmin><UsersPage /></RequireAdmin>} />

        {/* Sprint 2+ (stubs) */}
        <Route path="buildings" element={<RequireAdmin><BuildingsPage /></RequireAdmin>} />
        <Route path="expenses" element={<ExpensesPage />} />
        <Route path="payments" element={<PaymentsPage />} />
        <Route path="notifications" element={<NotificationCenterPage />} />
        <Route path="audit" element={<RequireAdmin><AuditLogPage /></RequireAdmin>} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
