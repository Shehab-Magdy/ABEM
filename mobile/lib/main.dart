import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/cubit/theme_cubit.dart';
import 'features/auth/bloc/auth_bloc.dart';
import 'features/auth/repositories/auth_repository.dart';
import 'injection.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Hive (local cache + settings persistence)
  await Hive.initFlutter();

  // Firebase is optional — skip gracefully when google-services.json / plist
  // is not yet configured (e.g. local development without FCM).
  try {
    await Firebase.initializeApp();
  } catch (_) {
    // Firebase not configured — push notifications disabled.
  }

  // Initialize dependency injection container
  await configureDependencies();

  // Create ThemeCubit early (reads from Hive before runApp — no theme flash)
  final themeCubit = await ThemeCubit.create();

  runApp(AbemApp(themeCubit: themeCubit));
}

class AbemApp extends StatelessWidget {
  final ThemeCubit themeCubit;

  const AbemApp({super.key, required this.themeCubit});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (_) => AuthBloc(
            authRepository: getIt<AuthRepository>(),
          )..add(const AuthCheckRequested()),
        ),
        BlocProvider.value(value: themeCubit),
      ],
      child: BlocBuilder<ThemeCubit, ThemeMode>(
        builder: (context, themeMode) {
          return MaterialApp.router(
            title: 'ABEM',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.light,
            darkTheme: AppTheme.dark,
            themeMode: themeMode,
            routerConfig: AppRouter.router,
          );
        },
      ),
    );
  }
}
