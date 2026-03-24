/// Named route path constants for GoRouter.
class Routes {
  Routes._();

  // ── Public ─────────────────────────────────────────────────
  static const String splash = '/splash';
  static const String login = '/login';
  static const String register = '/register';
  static const String registerInvite = '/register/invite';

  // ── Shared ─────────────────────────────────────────────────
  static const String profile = '/profile';
  static const String settings = '/settings';

  // ── Admin shell ────────────────────────────────────────────
  static const String adminDashboard = '/admin/dashboard';
  static const String adminBuildings = '/admin/buildings';
  static String adminBuildingDetail(String id) => '/admin/buildings/$id';
  static String adminBuildingUnits(String id) => '/admin/buildings/$id/units';
  static String adminApartmentDetail(String id) => '/admin/apartments/$id';
  static String adminApartmentInvite(String id) => '/admin/apartments/$id/invite';
  static const String adminExpenses = '/admin/expenses';
  static const String adminExpenseCreate = '/admin/expenses/create';
  static String adminExpenseDetail(String id) => '/admin/expenses/$id';
  static String adminExpenseEdit(String id) => '/admin/expenses/$id/edit';
  static const String adminPayments = '/admin/payments';
  static const String adminPaymentRecord = '/admin/payments/record';
  static String adminPaymentReceipt(String id) => '/admin/payments/$id/receipt';
  static const String adminUsers = '/admin/users';
  static const String adminUserCreate = '/admin/users/create';
  static String adminUserDetail(String id) => '/admin/users/$id';
  static const String adminAssets = '/admin/assets';
  static const String adminAssetCreate = '/admin/assets/create';
  static const String adminNotifications = '/admin/notifications';
  static const String adminAudit = '/admin/audit';
  static const String adminSettings = '/admin/settings';

  // ── Owner shell ────────────────────────────────────────────
  static const String ownerDashboard = '/owner/dashboard';
  static const String ownerExpenses = '/owner/expenses';
  static String ownerExpenseDetail(String id) => '/owner/expenses/$id';
  static const String ownerPayments = '/owner/payments';
  static String ownerPaymentReceipt(String id) => '/owner/payments/$id/receipt';
  static const String ownerNotifications = '/owner/notifications';
  static const String ownerProfile = '/owner/profile';
  static const String ownerSettings = '/owner/settings';
}
