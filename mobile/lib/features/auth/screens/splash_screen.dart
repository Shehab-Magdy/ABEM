import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';

import '../bloc/auth_bloc.dart';

/// Splash screen displayed after the native splash completes.
///
/// Renders the full branded SVG splash design from [abem-assets].
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
      final route = state.isAdmin ? '/admin/dashboard' : '/owner/dashboard';
      context.go(route);
    } else {
      context.go('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is! AuthInitial && state is! AuthLoading) {
          _authResolved = true;
          _tryNavigate();
        }
      },
      child: Scaffold(
        body: SizedBox.expand(
          child: SvgPicture.asset(
            'assets/splash/splash.svg',
            fit: BoxFit.cover,
          ),
        ),
      ),
    );
  }
}
