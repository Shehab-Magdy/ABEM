import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "../contexts/authStore";
import TutorialSystem from "../tutorial/TutorialOverlay";
import { CircularProgress, Box } from "@mui/material";

// Layout (kept eager – it wraps every authenticated page)
import DashboardLayout from "../components/common/DashboardLayout";

// Error pages (kept eager – used as inline fallbacks in route guards)
import NotFoundPage from "../pages/errors/NotFoundPage";
import ForbiddenPage from "../pages/errors/ForbiddenPage";
import UnauthorizedPage from "../pages/errors/UnauthorizedPage";
import ServerErrorPage from "../pages/errors/ServerErrorPage";

// Lazy-loaded pages
const LandingPage = lazy(() => import("../pages/landing/LandingPage"));
const LoginPage = lazy(() => import("../pages/auth/LoginPage"));
const RegisterPage = lazy(() => import("../pages/auth/RegisterPage"));
const ForgotPasswordPage = lazy(() => import("../pages/auth/ForgotPasswordPage"));
const ForceChangePasswordPage = lazy(() => import("../pages/auth/ForceChangePasswordPage"));
const AdminDashboardPage = lazy(() => import("../pages/dashboard/AdminDashboardPage"));
const OwnerDashboardPage = lazy(() => import("../pages/dashboard/OwnerDashboardPage"));
const UsersPage = lazy(() => import("../pages/users/UsersPage"));
const ProfilePage = lazy(() => import("../pages/profile/ProfilePage"));
const BuildingsPage = lazy(() => import("../pages/buildings/BuildingsPage"));
const ExpensesPage = lazy(() => import("../pages/expenses/ExpensesPage"));
const PaymentsPage = lazy(() => import("../pages/payments/PaymentsPage"));
const NotificationCenterPage = lazy(() => import("../pages/notifications/NotificationCenterPage"));
const AuditLogPage = lazy(() => import("../pages/audit/AuditLogPage"));
const ExpenseCategoriesPage = lazy(() => import("../pages/expenses/ExpenseCategoriesPage"));
const AssetsPage = lazy(() => import("../pages/assets/AssetsPage"));

// Shared loading fallback
const SuspenseFallback = (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
    <CircularProgress />
  </Box>
);

// ── Route guards ──────────────────────────────────────────────────────────────

function RequireAuth({ children }) {
  const { accessToken, user } = useAuthStore();
  if (!accessToken) return <Navigate to="/login" replace />;
  if (user?.must_change_password) return <Navigate to="/change-password-required" replace />;
  return children;
}

function RequireForceChange({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  if (user.must_change_password) return children;
  return <Navigate to="/dashboard" replace />;
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
    <Suspense fallback={SuspenseFallback}>
    <Routes>
      {/* Public marketing page */}
      <Route path="/landing" element={user ? <Navigate to="/dashboard" replace /> : <LandingPage />} />

      {/* Public auth pages */}
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      {/* /register has no guard here: the wizard calls login() mid-flow (after AccountStep),
          which would otherwise cause an immediate redirect away before the user finishes the wizard. */}
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />

      {/* Forced password change — accessible only when must_change_password is true */}
      <Route
        path="/change-password-required"
        element={
          <RequireForceChange>
            <ForceChangePasswordPage />
          </RequireForceChange>
        }
      />

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
    </Suspense>
    </>
  );
}
