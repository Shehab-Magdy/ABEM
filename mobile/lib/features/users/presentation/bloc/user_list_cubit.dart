import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/user_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class UserListState extends Equatable {
  const UserListState();
  @override
  List<Object?> get props => [];
}

class UserListInitial extends UserListState {
  const UserListInitial();
}

class UserListLoading extends UserListState {
  const UserListLoading();
}

class UserListLoaded extends UserListState {
  final List<Map<String, dynamic>> users;
  const UserListLoaded(this.users);

  @override
  List<Object?> get props => [users];
}

class UserListError extends UserListState {
  final String message;
  const UserListError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class UserListCubit extends Cubit<UserListState> {
  final UserRepository _repo;
  String? _lastBuildingId;
  String? _lastSearch;
  String? _lastRole;

  UserListCubit(this._repo) : super(const UserListInitial());

  Future<void> loadUsers({
    String? buildingId,
    String? search,
    String? role,
  }) async {
    _lastBuildingId = buildingId;
    _lastSearch = search;
    _lastRole = role;
    emit(const UserListLoading());
    final result = await _repo.getUsers(
      buildingId: buildingId,
      search: search,
      role: role,
    );
    result.fold(
      (failure) => emit(UserListError(failure.message)),
      (data) => emit(UserListLoaded(data)),
    );
  }

  Future<void> refresh() => loadUsers(
        buildingId: _lastBuildingId,
        search: _lastSearch,
        role: _lastRole,
      );
}
