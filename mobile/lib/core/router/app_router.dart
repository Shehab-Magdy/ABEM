import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/bloc/auth_bloc.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/home/screens/home_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/splash/screens/splash_screen.dart';

class AppRouter {
  static GoRouter router(AuthBloc authBloc) => GoRouter(
        initialLocation: '/splash',
        refreshListenable: GoRouterRefreshStream(authBloc.stream),
        redirect: (context, state) {
          final authState = authBloc.state;
          final isLoggedIn = authState is AuthAuthenticated;
          final isAuthRoute = state.subloc == '/login' ||
              state.subloc == '/register' ||
              state.subloc == '/splash';

          if (authState is AuthInitial) {
            return state.subloc == '/splash' ? null : '/splash';
          }

          if (state.subloc == '/splash') {
            return isLoggedIn ? '/home' : '/login';
          }

          if (!isLoggedIn && !isAuthRoute) return '/login';
          if (isLoggedIn && (state.subloc == '/login' || state.subloc == '/register')) {
            return '/home';
          }
          return null;
        },
        routes: [
          GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
          GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
          GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
          GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
          GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
        ],
      );
}
