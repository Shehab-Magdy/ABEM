import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "../contexts/authStore";

// Auth pages
import LoginPage from "../pages/auth/LoginPage";

// Layout (placeholder – implemented in Sprint 2)
import DashboardLayout from "../components/common/DashboardLayout";

// Dashboard pages
import AdminDashboardPage from "../pages/dashboard/AdminDashboardPage";
import OwnerDashboardPage from "../pages/dashboard/OwnerDashboardPage";

// Building pages
import BuildingsPage from "../pages/buildings/BuildingsPage";

// Expense pages
import ExpensesPage from "../pages/expenses/ExpensesPage";

// Payment pages
import PaymentsPage from "../pages/payments/PaymentsPage";

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

export default function AppRouter() {
  const { user } = useAuthStore();

  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected */}
      <Route
        path="/"
        element={
          <RequireAuth>
            <DashboardLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route
          path="dashboard"
          element={
            user?.role === "admin" ? <AdminDashboardPage /> : <OwnerDashboardPage />
          }
        />
        <Route path="buildings" element={<RequireAdmin><BuildingsPage /></RequireAdmin>} />
        <Route path="expenses" element={<ExpensesPage />} />
        <Route path="payments" element={<PaymentsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
