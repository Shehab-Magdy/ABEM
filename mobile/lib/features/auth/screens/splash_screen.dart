import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../bloc/auth_bloc.dart';

/// Splash screen displayed after the native splash completes.
///
/// Dispatches [AuthCheckRequested], waits for the result, then navigates
/// to the appropriate screen. Shows a minimum 1.5 s visual display to
/// avoid a jarring flash.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  bool _minDelayDone = false;
  bool _authResolved = false;

  @override
  void initState() {
    super.initState();
    // Minimum visual display time
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        _minDelayDone = true;
        _tryNavigate();
      }
    });
  }

  void _tryNavigate() {
    if (!_minDelayDone || !_authResolved) return;
    final state = context.read<AuthBloc>().state;
    if (state is AuthAuthenticated) {
      final route =
          state.isAdmin ? '/admin/dashboard' : '/owner/dashboard';
      context.go(route);
    } else {
      context.go('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is! AuthInitial && state is! AuthLoading) {
          _authResolved = true;
          _tryNavigate();
        }
      },
      child: Scaffold(
        backgroundColor: isDark
            ? const Color(0xFF141A18)
            : const Color(0xFF1A6B5A),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo icon
              const Icon(
                Icons.apartment_rounded,
                size: 80,
                color: Colors.white,
              ),
              const SizedBox(height: 20),
              Text(
                'ABEM',
                style: theme.textTheme.headlineLarge?.copyWith(
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                  letterSpacing: 4,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Building Expense Management',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: Colors.white70,
                ),
              ),
              const SizedBox(height: 48),
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
