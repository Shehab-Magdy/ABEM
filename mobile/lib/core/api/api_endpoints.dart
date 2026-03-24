/// All API URL path constants — no magic strings in feature code.
class ApiEndpoints {
  ApiEndpoints._();

  // ── Auth ───────────────────────────────────────────────────
  static const String login = '/auth/login/';
  static const String logout = '/auth/logout/';
  static const String refresh = '/auth/refresh/';
  static const String selfRegister = '/auth/self-register/';
  static const String profile = '/auth/profile/';
  static const String changePassword = '/auth/change-password/';

  // ── Buildings ──────────────────────────────────────────────
  static const String buildings = '/buildings/';
  static String buildingDetail(String id) => '/buildings/$id/';
  static String buildingActivate(String id) => '/buildings/$id/activate/';
  static String buildingDeactivate(String id) => '/buildings/$id/deactivate/';
  static String buildingAssignUser(String id) => '/buildings/$id/assign-user/';
  static const String buildingDirectory = '/buildings/directory/';
  static String buildingApartments(String id) => '/buildings/$id/apartments/';

  // ── Apartments ─────────────────────────────────────────────
  static const String apartmentsAvailable = '/apartments/available/';
  static String apartmentDetail(String id) => '/apartments/$id/';
  static String apartmentBalance(String id) => '/apartments/$id/balance/';
  static String apartmentClaim(String id) => '/apartments/$id/claim/';
  static String apartmentInvite(String id) => '/apartments/$id/invite/';
  static const String inviteValidate = '/apartments/invite/validate/';
  static const String inviteUse = '/apartments/invite/use/';

  // ── Expenses ───────────────────────────────────────────────
  static const String expenses = '/expenses/';
  static String expenseDetail(String id) => '/expenses/$id/';
  static String expenseUpload(String id) => '/expenses/$id/upload/';
  static const String expenseCategories = '/expenses/categories/';
  static String categoryDetail(String id) => '/expenses/categories/$id/';

  // ── Payments ───────────────────────────────────────────────
  static const String payments = '/payments/';
  static String paymentReceipt(String id) => '/payments/$id/receipt/';

  // ── Dashboard ──────────────────────────────────────────────
  static const String adminDashboard = '/dashboard/admin/';
  static const String ownerDashboard = '/dashboard/owner/';

  // ── Notifications ──────────────────────────────────────────
  static const String notifications = '/notifications/';
  static String notificationRead(String id) => '/notifications/$id/read/';
  static const String broadcast = '/notifications/broadcast/';
  static const String sendMessage = '/notifications/send/';

  // ── Users ──────────────────────────────────────────────────
  static const String users = '/users/';
  static String userDetail(String id) => '/users/$id/';
  static String userActivate(String id) => '/users/$id/activate/';
  static String userDeactivate(String id) => '/users/$id/deactivate/';
  static String userResetPassword(String id) => '/users/$id/reset-password/';
  static String userMessagingBlock(String id) => '/users/$id/set-messaging-block/';

  // ── Assets ─────────────────────────────────────────────────
  static const String assets = '/payments/assets/';
  static String assetDetail(String id) => '/payments/assets/$id/';
  static String assetSell(String id) => '/payments/assets/$id/sell/';

  // ── Audit ──────────────────────────────────────────────────
  static const String audit = '/audit/';

  // ── Exports ────────────────────────────────────────────────
  static const String exportPayments = '/exports/payments/';
  static const String exportExpenses = '/exports/expenses/';
  static const String exportAssetSales = '/exports/asset-sales/';
}
