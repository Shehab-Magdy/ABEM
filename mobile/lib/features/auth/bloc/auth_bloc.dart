import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';
import '../repositories/auth_repository.dart';

// ── Events ────────────────────────────────────────────────────────────────────
abstract class AuthEvent extends Equatable {
  const AuthEvent();
  @override
  List<Object?> get props => [];
}

class AuthCheckRequested extends AuthEvent {
  const AuthCheckRequested();
}

class AuthLoginRequested extends AuthEvent {
  final String email;
  final String password;
  const AuthLoginRequested({required this.email, required this.password});

  @override
  List<Object?> get props => [email, password];
}

class AuthLogoutRequested extends AuthEvent {
  const AuthLogoutRequested();
}

class AuthProfileUpdateRequested extends AuthEvent {
  final Map<String, dynamic> fields;
  const AuthProfileUpdateRequested(this.fields);
  @override
  List<Object?> get props => [fields];
}

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

  @override
  List<Object?> get props => [user];
}

class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
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
    on<AuthProfileUpdateRequested>(_onProfileUpdateRequested);
    on<AuthProfilePictureUpdateRequested>(_onProfilePictureUpdateRequested);
  }

  Future<void> _onCheckRequested(
    AuthCheckRequested event,
    Emitter<AuthState> emit,
  ) async {
    final token = await authRepository.getStoredAccessToken();
    if (token != null) {
      final user = await authRepository.getStoredUser();
      if (user != null) {
        emit(AuthAuthenticated(user: user));
        return;
      }
    }
    emit(const AuthUnauthenticated());
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
      emit(AuthError(message: e.message, isLocked: true));
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
