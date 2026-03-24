import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';

import 'core/api/dio_client.dart';
import 'core/auth/token_storage.dart';
import 'features/auth/repositories/auth_repository.dart';

/// Global service locator instance.
final getIt = GetIt.instance;

/// Initialize all dependencies.
///
/// Call this once in [main] before [runApp]. Registration order matters:
/// singletons first, then repositories, then blocs/cubits (as factories).
Future<void> configureDependencies() async {
  // ── Singletons ──────────────────────────────────────────────

  getIt.registerSingleton<FlutterSecureStorage>(
    const FlutterSecureStorage(),
  );

  getIt.registerSingleton<TokenStorage>(
    TokenStorage(getIt<FlutterSecureStorage>()),
  );

  getIt.registerSingleton<Dio>(
    DioClient.create(getIt<TokenStorage>()),
  );

  // ── Repositories (lazy singletons) ──────────────────────────

  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepository(
      dio: getIt<Dio>(),
      tokenStorage: getIt<TokenStorage>(),
    ),
  );

  // Feature repositories will be registered here as they are built:
  // getIt.registerLazySingleton<BuildingRepository>(() => ...);
  // getIt.registerLazySingleton<ExpenseRepository>(() => ...);
  // getIt.registerLazySingleton<PaymentRepository>(() => ...);
  // getIt.registerLazySingleton<DashboardRepository>(() => ...);
  // getIt.registerLazySingleton<NotificationRepository>(() => ...);
  // getIt.registerLazySingleton<UserRepository>(() => ...);
  // getIt.registerLazySingleton<AssetRepository>(() => ...);
  // getIt.registerLazySingleton<AuditRepository>(() => ...);
}
