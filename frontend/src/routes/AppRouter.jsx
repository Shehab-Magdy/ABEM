import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "../contexts/authStore";
import TutorialSystem from "../tutorial/TutorialOverlay";

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

// Feature pages
import BuildingsPage from "../pages/buildings/BuildingsPage";
import ExpensesPage from "../pages/expenses/ExpensesPage";
import PaymentsPage from "../pages/payments/PaymentsPage";
import NotificationCenterPage from "../pages/notifications/NotificationCenterPage";
import AuditLogPage from "../pages/audit/AuditLogPage";
import ExpenseCategoriesPage from "../pages/expenses/ExpenseCategoriesPage";
import AssetsPage from "../pages/assets/AssetsPage";

// Error pages
import NotFoundPage from "../pages/errors/NotFoundPage";
import ForbiddenPage from "../pages/errors/ForbiddenPage";
import UnauthorizedPage from "../pages/errors/UnauthorizedPage";
import ServerErrorPage from "../pages/errors/ServerErrorPage";

// ── Route guards ──────────────────────────────────────────────────────────────

function RequireAuth({ children }) {
  const { accessToken } = useAuthStore();
  return accessToken ? children : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin") return <ForbiddenPage />;
  return children;
}

// ── Router ────────────────────────────────────────────────────────────────────

export default function AppRouter() {
  const { user } = useAuthStore();

  return (
    <>
    <TutorialSystem />
    <Routes>
      {/* Public – redirect to dashboard if already authenticated */}
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      {/* /register has no guard here: the wizard calls login() mid-flow (after AccountStep),
          which would otherwise cause an immediate redirect away before the user finishes the wizard. */}
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
        <Route path="expense-categories" element={<RequireAdmin><ExpenseCategoriesPage /></RequireAdmin>} />
        <Route path="assets" element={<RequireAdmin><AssetsPage /></RequireAdmin>} />
      </Route>

      {/* Standalone error pages (navigable directly) */}
      <Route path="/401" element={<UnauthorizedPage />} />
      <Route path="/403" element={<ForbiddenPage />} />
      <Route path="/500" element={<ServerErrorPage />} />

      {/* 404 – catch-all */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
    </>
  );
}
