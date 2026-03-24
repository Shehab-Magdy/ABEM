import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';

import 'core/api/dio_client.dart';
import 'core/auth/token_storage.dart';
import 'features/auth/repositories/auth_repository.dart';
import 'features/apartments/data/datasources/apartment_remote_data_source.dart';
import 'features/apartments/data/repositories/apartment_repository.dart';
import 'features/buildings/data/datasources/building_remote_data_source.dart';
import 'features/buildings/data/repositories/building_repository.dart';
import 'features/expenses/data/datasources/expense_remote_data_source.dart';
import 'features/expenses/data/repositories/expense_repository.dart';

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

  getIt.registerLazySingleton<BuildingRemoteDataSource>(
    () => BuildingRemoteDataSource(getIt<Dio>()),
  );

  getIt.registerLazySingleton<BuildingRepository>(
    () => BuildingRepository(getIt<BuildingRemoteDataSource>()),
  );

  getIt.registerLazySingleton<ApartmentRemoteDataSource>(
    () => ApartmentRemoteDataSource(getIt<Dio>()),
  );

  getIt.registerLazySingleton<ApartmentRepository>(
    () => ApartmentRepository(getIt<ApartmentRemoteDataSource>()),
  );

  getIt.registerLazySingleton<ExpenseRemoteDataSource>(
    () => ExpenseRemoteDataSource(getIt<Dio>()),
  );

  getIt.registerLazySingleton<ExpenseRepository>(
    () => ExpenseRepository(getIt<ExpenseRemoteDataSource>()),
  );

  // Future feature repositories:
  // getIt.registerLazySingleton<PaymentRepository>(() => ...);
  // getIt.registerLazySingleton<DashboardRepository>(() => ...);
  // getIt.registerLazySingleton<NotificationRepository>(() => ...);
  // getIt.registerLazySingleton<UserRepository>(() => ...);
  // getIt.registerLazySingleton<AssetRepository>(() => ...);
  // getIt.registerLazySingleton<AuditRepository>(() => ...);
}
