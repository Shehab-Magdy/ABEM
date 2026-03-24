import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/bloc/auth_bloc.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/auth/screens/splash_screen.dart';
import '../../features/buildings/screens/buildings_screen.dart';
import '../../features/expenses/screens/expenses_screen.dart';
import '../../features/home/screens/home_screen.dart';
import '../../features/notifications/screens/notifications_screen.dart';
import '../../features/payments/screens/payments_screen.dart';
import '../../features/profile/screens/profile_screen.dart';

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

      // ── Admin routes ───────────────────────────────────────
      GoRoute(
        path: '/admin/dashboard',
        builder: (_, __) => const HomeScreen(),
      ),
      GoRoute(
        path: '/admin/buildings',
        builder: (_, __) => const BuildingsScreen(),
      ),
      GoRoute(
        path: '/admin/buildings/:id',
        builder: (_, state) => _PlaceholderScreen(
          title: 'Building ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: '/admin/buildings/:id/units',
        builder: (_, state) => _PlaceholderScreen(
          title: 'Units — ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: '/admin/apartments/:id',
        builder: (_, state) => _PlaceholderScreen(
          title: 'Apartment ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: '/admin/expenses',
        builder: (_, __) => const ExpensesScreen(),
      ),
      GoRoute(
        path: '/admin/expenses/create',
        builder: (_, __) => const _PlaceholderScreen(title: 'Create Expense'),
      ),
      GoRoute(
        path: '/admin/expenses/:id',
        builder: (_, state) => _PlaceholderScreen(
          title: 'Expense ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: '/admin/payments',
        builder: (_, __) => const PaymentsScreen(),
      ),
      GoRoute(
        path: '/admin/payments/record',
        builder: (_, __) =>
            const _PlaceholderScreen(title: 'Record Payment'),
      ),
      GoRoute(
        path: '/admin/payments/:id/receipt',
        builder: (_, state) => _PlaceholderScreen(
          title: 'Receipt ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: '/admin/users',
        builder: (_, __) => const _PlaceholderScreen(title: 'Users'),
      ),
      GoRoute(
        path: '/admin/users/create',
        builder: (_, __) => const _PlaceholderScreen(title: 'Create User'),
      ),
      GoRoute(
        path: '/admin/users/:id',
        builder: (_, state) => _PlaceholderScreen(
          title: 'User ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: '/admin/assets',
        builder: (_, __) => const _PlaceholderScreen(title: 'Assets'),
      ),
      GoRoute(
        path: '/admin/assets/create',
        builder: (_, __) =>
            const _PlaceholderScreen(title: 'Add Asset'),
      ),
      GoRoute(
        path: '/admin/notifications',
        builder: (_, __) => const NotificationsScreen(),
      ),
      GoRoute(
        path: '/admin/audit',
        builder: (_, __) => const _PlaceholderScreen(title: 'Audit Log'),
      ),
      GoRoute(
        path: '/admin/settings',
        builder: (_, __) => const _PlaceholderScreen(title: 'Settings'),
      ),

      // ── Owner routes ───────────────────────────────────────
      GoRoute(
        path: '/owner/dashboard',
        builder: (_, __) => const HomeScreen(),
      ),
      GoRoute(
        path: '/owner/expenses',
        builder: (_, __) => const ExpensesScreen(),
      ),
      GoRoute(
        path: '/owner/expenses/:id',
        builder: (_, state) => _PlaceholderScreen(
          title: 'Expense ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: '/owner/payments',
        builder: (_, __) => const PaymentsScreen(),
      ),
      GoRoute(
        path: '/owner/payments/:id/receipt',
        builder: (_, state) => _PlaceholderScreen(
          title: 'Receipt ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: '/owner/notifications',
        builder: (_, __) => const NotificationsScreen(),
      ),
      GoRoute(
        path: '/owner/profile',
        builder: (_, __) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/owner/settings',
        builder: (_, __) => const _PlaceholderScreen(title: 'Settings'),
      ),

      // ── Legacy fallback (redirect /home to role-based dashboard) ──
      GoRoute(
        path: '/home',
        redirect: (context, _) {
          final authState = context.read<AuthBloc>().state;
          if (authState is AuthAuthenticated) {
            return authState.isAdmin ? '/admin/dashboard' : '/owner/dashboard';
          }
          return '/login';
        },
      ),
    ],
  );
}

/// Temporary placeholder for screens not yet implemented.
///
/// Shows the route title so you can verify navigation works before
/// building the real screen.
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
