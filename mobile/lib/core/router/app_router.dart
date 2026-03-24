import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/bloc/auth_bloc.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/auth/screens/splash_screen.dart';
import '../../features/apartments/data/repositories/apartment_repository.dart';
import '../../features/apartments/presentation/bloc/apartment_detail_cubit.dart';
import '../../features/apartments/presentation/screens/apartment_detail_screen.dart';
import '../../features/buildings/data/repositories/building_repository.dart';
import '../../features/buildings/presentation/bloc/building_detail_cubit.dart';
import '../../features/buildings/presentation/bloc/building_form_cubit.dart';
import '../../features/buildings/presentation/bloc/building_list_cubit.dart';
import '../../features/buildings/presentation/bloc/building_units_cubit.dart';
import '../../features/buildings/presentation/screens/building_detail_screen.dart';
import '../../features/buildings/presentation/screens/building_list_screen.dart';
import '../../features/buildings/presentation/screens/building_units_screen.dart';
import '../../features/dashboard/presentation/bloc/admin_dashboard_cubit.dart';
import '../../features/dashboard/presentation/bloc/owner_dashboard_cubit.dart';
import '../../features/dashboard/presentation/screens/admin_dashboard_screen.dart';
import '../../features/dashboard/presentation/screens/owner_dashboard_screen.dart';
import '../../features/expenses/presentation/bloc/expense_detail_cubit.dart';
import '../../features/expenses/presentation/bloc/expense_form_cubit.dart';
import '../../features/expenses/presentation/bloc/expense_list_cubit.dart';
import '../../features/expenses/presentation/screens/expense_create_screen.dart';
import '../../features/expenses/presentation/screens/expense_detail_screen.dart';
import '../../features/expenses/presentation/screens/expense_list_screen.dart';
import '../../features/home/screens/home_screen.dart';
import '../../features/notifications/screens/notifications_screen.dart';
import '../../features/payments/screens/payments_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../injection.dart';
import '../features/expenses/data/repositories/expense_repository.dart';
import 'routes.dart';
import 'shells/admin_shell.dart';
import 'shells/owner_shell.dart';

/// Public routes that do not require authentication.
const _publicRoutes = {'/splash', '/login', '/register', '/register/invite'};

/// Return the home route for the authenticated user's role.
String _roleHome(AuthState state) {
  if (state is AuthAuthenticated && state.isAdmin) return '/admin/dashboard';
  return '/owner/dashboard';
}

class AppRouter {
  static final router = GoRouter(
    initialLocation: '/splash',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final authState = context.read<AuthBloc>().state;
      final isAuth = authState is AuthAuthenticated;
      final loc = state.matchedLocation;

      // Allow splash to always render (it handles its own navigation)
      if (loc == '/splash') return null;

      // Unauthenticated users can only access public routes
      if (!isAuth && !_publicRoutes.contains(loc)) return '/login';

      // Authenticated users on public routes → redirect to role dashboard
      if (isAuth && _publicRoutes.contains(loc)) {
        return _roleHome(authState);
      }

      // RBAC: owners cannot access admin routes
      if (isAuth && loc.startsWith('/admin')) {
        if (_roleHome(authState) != '/admin/dashboard') {
          return '/owner/dashboard';
        }
      }

      return null;
    },
    routes: [
      // ── Public ─────────────────────────────────────────────
      GoRoute(
        path: '/splash',
        builder: (_, __) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (_, __) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (_, __) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/register/invite',
        builder: (_, __) => const InviteCodeScreen(),
      ),

      // ── Shared ─────────────────────────────────────────────
      GoRoute(
        path: '/profile',
        builder: (_, __) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/settings',
        builder: (_, __) => const _PlaceholderScreen(title: 'Settings'),
      ),

      _buildAdminShell(),
      _buildOwnerShell(),
    ],
  );
}

/// Temporary placeholder for screens not yet implemented.
///
/// Shows the route title so you can verify navigation works before
/// building the real screen.
StatefulShellRoute _buildAdminShell() {
  return StatefulShellRoute.indexedStack(
    builder: (context, state, navigationShell) => AdminShell(
      navigationShell: navigationShell,
    ),
    branches: [
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.adminDashboard,
            builder: (_, __) => BlocProvider(
              create: (_) => AdminDashboardCubit(getIt())..load(),
              child: const AdminDashboardScreen(),
            ),
          ),
        ],
      ),
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.adminBuildings,
            builder: (_, __) => MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (_) =>
                      BuildingListCubit(getIt<BuildingRepository>())..loadBuildings(),
                ),
                BlocProvider(
                  create: (_) => BuildingFormCubit(getIt<BuildingRepository>()),
                ),
              ],
              child: const BuildingListScreen(),
            ),
          ),
          GoRoute(
            path: Routes.adminBuildingDetail(':id'),
            builder: (_, state) {
              final id = state.pathParameters['id']!;
              return MultiBlocProvider(
                providers: [
                  BlocProvider(
                    create: (_) =>
                        BuildingDetailCubit(getIt<BuildingRepository>())..load(id),
                  ),
                  BlocProvider(
                    create: (_) => BuildingFormCubit(getIt<BuildingRepository>()),
                  ),
                ],
                child: BuildingDetailScreen(buildingId: id),
              );
            },
          ),
          GoRoute(
            path: Routes.adminBuildingUnits(':id'),
            builder: (_, state) {
              final id = state.pathParameters['id']!;
              final extra = state.extra;
              String? buildingName;
              if (extra is Map<String, dynamic>) {
                buildingName = extra['buildingName'] as String?;
              }
              return BlocProvider(
                create: (_) =>
                    BuildingUnitsCubit(getIt<BuildingRepository>())..load(id),
                child: BuildingUnitsScreen(
                  buildingId: id,
                  buildingName: buildingName,
                ),
              );
            },
          ),
          GoRoute(
            path: Routes.adminApartmentDetail(':id'),
            builder: (_, state) {
              final id = state.pathParameters['id']!;
              return BlocProvider(
                create: (_) =>
                    ApartmentDetailCubit(getIt<ApartmentRepository>())..load(id),
                child: ApartmentDetailScreen(apartmentId: id),
              );
            },
          ),
        ],
      ),
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.adminExpenses,
            builder: (_, __) => BlocProvider(
              create: (_) => ExpenseListCubit(getIt<ExpenseRepository>()),
              child: const ExpenseListScreen(),
            ),
          ),
          GoRoute(
            path: Routes.adminExpenseCreate,
            builder: (_, __) => BlocProvider(
              create: (_) => ExpenseFormCubit(getIt<ExpenseRepository>())
                ..loadCategories(),
              child: const ExpenseCreateScreen(),
            ),
          ),
          GoRoute(
            path: Routes.adminExpenseDetail(':id'),
            builder: (_, state) {
              final id = state.pathParameters['id']!;
              return BlocProvider(
                create: (_) => ExpenseDetailCubit(getIt<ExpenseRepository>())
                  ..load(id),
                child: ExpenseDetailScreen(expenseId: id),
              );
            },
          ),
        ],
      ),
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.adminPayments,
            builder: (_, __) => const PaymentsScreen(),
          ),
          GoRoute(
            path: Routes.adminPaymentRecord,
            builder: (_, __) => const _PlaceholderScreen(title: 'Record Payment'),
          ),
          GoRoute(
            path: Routes.adminPaymentReceipt(':id'),
            builder: (_, state) => _PlaceholderScreen(
              title: 'Receipt ${state.pathParameters['id']}',
            ),
          ),
        ],
      ),
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.adminMore,
            builder: (_, __) => const _PlaceholderScreen(title: 'More'),
          ),
          GoRoute(
            path: Routes.adminUsers,
            builder: (_, __) => const _PlaceholderScreen(title: 'Users'),
          ),
          GoRoute(
            path: Routes.adminUserCreate,
            builder: (_, __) => const _PlaceholderScreen(title: 'Create User'),
          ),
          GoRoute(
            path: Routes.adminUserDetail(':id'),
            builder: (_, state) => _PlaceholderScreen(
              title: 'User ${state.pathParameters['id']}',
            ),
          ),
          GoRoute(
            path: Routes.adminAssets,
            builder: (_, __) => const _PlaceholderScreen(title: 'Assets'),
          ),
          GoRoute(
            path: Routes.adminAssetCreate,
            builder: (_, __) => const _PlaceholderScreen(title: 'Add Asset'),
          ),
          GoRoute(
            path: Routes.adminNotifications,
            builder: (_, __) => const NotificationsScreen(),
          ),
          GoRoute(
            path: Routes.adminAudit,
            builder: (_, __) => const _PlaceholderScreen(title: 'Audit Log'),
          ),
          GoRoute(
            path: Routes.adminSettings,
            builder: (_, __) => const _PlaceholderScreen(title: 'Settings'),
          ),
        ],
      ),
    ],
  );
}

StatefulShellRoute _buildOwnerShell() {
  return StatefulShellRoute.indexedStack(
    builder: (context, state, navigationShell) => OwnerShell(
      navigationShell: navigationShell,
    ),
    branches: [
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.ownerDashboard,
            builder: (_, __) => BlocProvider(
              create: (_) => OwnerDashboardCubit(getIt())..load(),
              child: const OwnerDashboardScreen(),
            ),
          ),
        ],
      ),
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.ownerExpenses,
            builder: (_, __) => BlocProvider(
              create: (_) => ExpenseListCubit(getIt<ExpenseRepository>()),
              child: const ExpenseListScreen(),
            ),
          ),
          GoRoute(
            path: Routes.ownerExpenseDetail(':id'),
            builder: (_, state) {
              final id = state.pathParameters['id']!;
              return BlocProvider(
                create: (_) => ExpenseDetailCubit(getIt<ExpenseRepository>())
                  ..load(id),
                child: ExpenseDetailScreen(expenseId: id),
              );
            },
          ),
        ],
      ),
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.ownerPayments,
            builder: (_, __) => const PaymentsScreen(),
          ),
          GoRoute(
            path: Routes.ownerPaymentReceipt(':id'),
            builder: (_, state) => _PlaceholderScreen(
              title: 'Receipt ${state.pathParameters['id']}',
            ),
          ),
        ],
      ),
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.ownerNotifications,
            builder: (_, __) => const NotificationsScreen(),
          ),
        ],
      ),
      StatefulShellBranch(
        routes: [
          GoRoute(
            path: Routes.ownerProfile,
            builder: (_, __) => const ProfileScreen(),
          ),
          GoRoute(
            path: Routes.ownerSettings,
            builder: (_, __) => const _PlaceholderScreen(title: 'Settings'),
          ),
        ],
      ),
    ],
  );
}

class _PlaceholderScreen extends StatelessWidget {
  final String title;
  const _PlaceholderScreen({required this.title});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.construction_rounded,
                size: 48,
                color: Theme.of(context).colorScheme.onSurfaceVariant),
            const SizedBox(height: 16),
            Text(title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    )),
            const SizedBox(height: 8),
            Text('Coming soon',
                style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }
}
