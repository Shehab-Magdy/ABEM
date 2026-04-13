import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:firebase_core/firebase_core.dart';

import 'core/api/api_client.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/bloc/auth_bloc.dart';
import 'features/auth/repositories/auth_repository.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Firebase is optional — skip gracefully when google-services.json / plist
  // is not yet configured (e.g. local development without FCM).
  try {
    await Firebase.initializeApp();
  } catch (_) {
    // Firebase not configured — push notifications disabled.
  }
  runApp(const AbemApp());
}

class AbemApp extends StatelessWidget {
  const AbemApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider(create: (_) => ApiClient()),
        RepositoryProvider(
          create: (ctx) => AuthRepository(apiClient: ctx.read<ApiClient>()),
        ),
      ],
      child: MultiBlocProvider(
        providers: [
          BlocProvider(
            create: (ctx) => AuthBloc(
              authRepository: ctx.read<AuthRepository>(),
            )..add(const AuthCheckRequested()),
          ),
        ],
        child: Builder(builder: (context) {
          final authBloc = context.read<AuthBloc>();
          return MaterialApp.router(
            title: 'ABEM',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.light,
            routerConfig: AppRouter.router(authBloc),
          );
        }),
      ),
    );
  }
}
