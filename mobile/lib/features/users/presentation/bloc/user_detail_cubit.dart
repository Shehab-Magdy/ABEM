import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/user_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class UserDetailState extends Equatable {
  const UserDetailState();
  @override
  List<Object?> get props => [];
}

class UserDetailInitial extends UserDetailState {
  const UserDetailInitial();
}

class UserDetailLoading extends UserDetailState {
  const UserDetailLoading();
}

class UserDetailLoaded extends UserDetailState {
  final Map<String, dynamic> user;
  const UserDetailLoaded(this.user);

  @override
  List<Object?> get props => [user];
}

class UserDetailActionSuccess extends UserDetailState {
  final String message;
  const UserDetailActionSuccess(this.message);

  @override
  List<Object?> get props => [message];
}

class UserDetailError extends UserDetailState {
  final String message;
  const UserDetailError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class UserDetailCubit extends Cubit<UserDetailState> {
  final UserRepository _repo;

  UserDetailCubit(this._repo) : super(const UserDetailInitial());

  Future<void> load(String id) async {
    emit(const UserDetailLoading());
    final result = await _repo.getUser(id);
    result.fold(
      (failure) => emit(UserDetailError(failure.message)),
      (data) => emit(UserDetailLoaded(data)),
    );
  }

  Future<void> updateUser(String id, Map<String, dynamic> payload) async {
    final result = await _repo.updateUser(id, payload);
    result.fold(
      (failure) => emit(UserDetailError(failure.message)),
      (data) => emit(UserDetailLoaded(data)),
    );
  }

  Future<void> activate(String id) async {
    final result = await _repo.activateUser(id);
    result.fold(
      (failure) => emit(UserDetailError(failure.message)),
      (_) {
        emit(const UserDetailActionSuccess('User activated successfully'));
        load(id);
      },
    );
  }

  Future<void> deactivate(String id) async {
    final result = await _repo.deactivateUser(id);
    result.fold(
      (failure) => emit(UserDetailError(failure.message)),
      (_) {
        emit(const UserDetailActionSuccess('User deactivated successfully'));
        load(id);
      },
    );
  }

  Future<void> resetPassword(String id, String newPassword) async {
    final result = await _repo.resetPassword(id, newPassword);
    result.fold(
      (failure) => emit(UserDetailError(failure.message)),
      (_) =>
          emit(const UserDetailActionSuccess('Password reset successfully')),
    );
  }

  Future<void> setMessagingBlock(
    String id, {
    required bool blocked,
    required bool individualBlocked,
  }) async {
    final result = await _repo.setMessagingBlock(
      id,
      blocked: blocked,
      individualBlocked: individualBlocked,
    );
    result.fold(
      (failure) => emit(UserDetailError(failure.message)),
      (_) {
        emit(const UserDetailActionSuccess(
            'Messaging restrictions updated successfully'));
        load(id);
      },
    );
  }
}
