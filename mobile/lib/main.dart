import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:firebase_core/firebase_core.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/bloc/auth_bloc.dart';
import 'features/auth/repositories/auth_repository.dart';
import 'injection.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Firebase is optional — skip gracefully when google-services.json / plist
  // is not yet configured (e.g. local development without FCM).
  try {
    await Firebase.initializeApp();
  } catch (_) {
    // Firebase not configured — push notifications disabled.
  }

  // Initialize dependency injection container
  await configureDependencies();

  runApp(const AbemApp());
}

class AbemApp extends StatelessWidget {
  const AbemApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (_) => AuthBloc(
            authRepository: getIt<AuthRepository>(),
          )..add(const AuthCheckRequested()),
        ),
      ],
      child: MaterialApp.router(
        title: 'ABEM',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        routerConfig: AppRouter.router,
      ),
    );
  }
}
