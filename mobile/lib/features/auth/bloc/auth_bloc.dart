import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/auth/jwt_decoder.dart';
import '../../../core/auth/token_storage.dart';
import '../../../injection.dart';
import '../repositories/auth_repository.dart';

// ── Events ────────────────────────────────────────────────────────────────────

abstract class AuthEvent extends Equatable {
  const AuthEvent();
  @override
  List<Object?> get props => [];
}

/// Dispatched on app launch — checks stored tokens and restores session.
class AuthCheckRequested extends AuthEvent {
  const AuthCheckRequested();
}

/// Dispatched when user submits the login form.
class AuthLoginRequested extends AuthEvent {
  final String email;
  final String password;
  const AuthLoginRequested({required this.email, required this.password});

  @override
  List<Object?> get props => [email, password];
}

/// Dispatched when user taps logout or session expires.
class AuthLogoutRequested extends AuthEvent {
  const AuthLogoutRequested();
}

/// Dispatched when the backend returns HTTP 423 (account locked).
class AuthAccountLocked extends AuthEvent {
  final String message;
  final String? lockedUntil;
  const AuthAccountLocked({required this.message, this.lockedUntil});

  @override
  List<Object?> get props => [message, lockedUntil];
}

/// Dispatched on app resume to silently refresh the access token if needed.
class AuthTokenRefreshRequested extends AuthEvent {
  const AuthTokenRefreshRequested();
}

/// Dispatched when user updates their profile fields.
class AuthProfileUpdateRequested extends AuthEvent {
  final Map<String, dynamic> fields;
  const AuthProfileUpdateRequested(this.fields);
  @override
  List<Object?> get props => [fields];
}

/// Dispatched when user uploads a new profile picture.
class AuthProfilePictureUpdateRequested extends AuthEvent {
  final XFile imageFile;
  const AuthProfilePictureUpdateRequested(this.imageFile);
  @override
  List<Object?> get props => [imageFile];
}

// ── States ────────────────────────────────────────────────────────────────────

abstract class AuthState extends Equatable {
  const AuthState();
  @override
  List<Object?> get props => [];
}

class AuthInitial extends AuthState {
  const AuthInitial();
}

class AuthLoading extends AuthState {
  const AuthLoading();
}

class AuthAuthenticated extends AuthState {
  final Map<String, dynamic> user;
  const AuthAuthenticated({required this.user});

  /// Convenience: extract the user role (admin | owner).
  String get role => (user['role'] as String?) ?? 'owner';

  /// Convenience: check if the user is an admin.
  bool get isAdmin => role == 'admin';

  @override
  List<Object?> get props => [user];
}

class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
}

/// Account locked by the backend (HTTP 423).
class AuthLocked extends AuthState {
  final String message;
  final String? lockedUntil;
  const AuthLocked({required this.message, this.lockedUntil});

  @override
  List<Object?> get props => [message, lockedUntil];
}

class AuthError extends AuthState {
  final String message;
  final bool isLocked;
  const AuthError({required this.message, this.isLocked = false});

  @override
  List<Object?> get props => [message, isLocked];
}

// ── BLoC ──────────────────────────────────────────────────────────────────────

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository authRepository;

  AuthBloc({required this.authRepository}) : super(const AuthInitial()) {
    on<AuthCheckRequested>(_onCheckRequested);
    on<AuthLoginRequested>(_onLoginRequested);
    on<AuthLogoutRequested>(_onLogoutRequested);
    on<AuthAccountLocked>(_onAccountLocked);
    on<AuthTokenRefreshRequested>(_onTokenRefreshRequested);
    on<AuthProfileUpdateRequested>(_onProfileUpdateRequested);
    on<AuthProfilePictureUpdateRequested>(_onProfilePictureUpdateRequested);
  }

  /// Check stored tokens on app start. If the access token is expired but a
  /// refresh token exists, attempt a silent refresh.
  Future<void> _onCheckRequested(
    AuthCheckRequested event,
    Emitter<AuthState> emit,
  ) async {
    final tokenStorage = getIt<TokenStorage>();
    final accessToken = await tokenStorage.accessToken;

    if (accessToken == null || accessToken.isEmpty) {
      emit(const AuthUnauthenticated());
      return;
    }

    // If the access token is still valid, restore from cached user
    if (!JwtDecoder.isExpired(accessToken)) {
      final user = await authRepository.getStoredUser();
      if (user != null) {
        emit(AuthAuthenticated(user: user));
        return;
      }
    }

    // Access token expired — try silent refresh
    final refreshToken = await tokenStorage.refreshToken;
    if (refreshToken == null || refreshToken.isEmpty) {
      emit(const AuthUnauthenticated());
      return;
    }

    try {
      // The RefreshInterceptor will handle the actual refresh when we make
      // any API call. But for startup, we do it explicitly here.
      final dio = getIt<Dio>();
      final response = await dio.post(
        '/auth/refresh/',
        data: {'refresh': refreshToken},
      );
      final newAccess = response.data['access'] as String;
      await tokenStorage.saveTokens(access: newAccess, refresh: refreshToken);

      final user = await authRepository.getStoredUser();
      if (user != null) {
        emit(AuthAuthenticated(user: user));
      } else {
        emit(const AuthUnauthenticated());
      }
    } catch (_) {
      await tokenStorage.clearAll();
      emit(const AuthUnauthenticated());
    }
  }

  Future<void> _onLoginRequested(
    AuthLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());
    try {
      final result = await authRepository.login(event.email, event.password);
      emit(AuthAuthenticated(user: result['user'] as Map<String, dynamic>));
    } on AccountLockedException catch (e) {
      emit(AuthLocked(message: e.message, lockedUntil: e.lockedUntil));
    } on DioException catch (e) {
      final detail =
          (e.response?.data as Map<String, dynamic>?)?['detail'] as String?;
      emit(AuthError(message: detail ?? 'Invalid email or password.'));
    } catch (e) {
      emit(const AuthError(message: 'An unexpected error occurred.'));
    }
  }

  Future<void> _onLogoutRequested(
    AuthLogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    await authRepository.logout();
    emit(const AuthUnauthenticated());
  }

  void _onAccountLocked(
    AuthAccountLocked event,
    Emitter<AuthState> emit,
  ) {
    emit(AuthLocked(message: event.message, lockedUntil: event.lockedUntil));
  }

  /// Silently refresh the access token. If it fails, log out.
  Future<void> _onTokenRefreshRequested(
    AuthTokenRefreshRequested event,
    Emitter<AuthState> emit,
  ) async {
    final tokenStorage = getIt<TokenStorage>();
    final accessToken = await tokenStorage.accessToken;

    // Only refresh if the current token is expiring soon
    if (accessToken != null && !JwtDecoder.isExpiringSoon(accessToken)) {
      return; // Token still valid, nothing to do
    }

    final refreshToken = await tokenStorage.refreshToken;
    if (refreshToken == null || refreshToken.isEmpty) {
      emit(const AuthUnauthenticated());
      return;
    }

    try {
      final dio = getIt<Dio>();
      final response = await dio.post(
        '/auth/refresh/',
        data: {'refresh': refreshToken},
      );
      final newAccess = response.data['access'] as String;
      await tokenStorage.saveTokens(access: newAccess, refresh: refreshToken);
    } catch (_) {
      await authRepository.logout();
      emit(const AuthUnauthenticated());
    }
  }

  Future<void> _onProfileUpdateRequested(
    AuthProfileUpdateRequested event,
    Emitter<AuthState> emit,
  ) async {
    try {
      final updated = await authRepository.updateProfile(event.fields);
      emit(AuthAuthenticated(user: updated));
    } on DioException catch (e) {
      final msg =
          (e.response?.data as Map<String, dynamic>?)?['detail'] as String? ??
              'Profile update failed.';
      emit(AuthError(message: msg));
    }
  }

  Future<void> _onProfilePictureUpdateRequested(
    AuthProfilePictureUpdateRequested event,
    Emitter<AuthState> emit,
  ) async {
    try {
      final updated =
          await authRepository.uploadProfilePicture(event.imageFile);
      emit(AuthAuthenticated(user: updated));
    } on DioException catch (e) {
      final msg =
          (e.response?.data as Map<String, dynamic>?)?['detail'] as String? ??
              'Profile picture upload failed.';
      emit(AuthError(message: msg));
    }
  }
}
