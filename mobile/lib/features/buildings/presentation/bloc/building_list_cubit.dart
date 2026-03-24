import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/building_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class BuildingListState extends Equatable {
  const BuildingListState();
  @override
  List<Object?> get props => [];
}

class BuildingListInitial extends BuildingListState {
  const BuildingListInitial();
}

class BuildingListLoading extends BuildingListState {
  const BuildingListLoading();
}

class BuildingListLoaded extends BuildingListState {
  final List<Map<String, dynamic>> buildings;
  final bool hasMore;
  const BuildingListLoaded(this.buildings, {this.hasMore = false});

  @override
  List<Object?> get props => [buildings, hasMore];
}

class BuildingListError extends BuildingListState {
  final String message;
  const BuildingListError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class BuildingListCubit extends Cubit<BuildingListState> {
  final BuildingRepository _repo;
  String _lastSearch = '';

  BuildingListCubit(this._repo) : super(const BuildingListInitial());

  Future<void> loadBuildings({String? search}) async {
    _lastSearch = search ?? '';
    emit(const BuildingListLoading());
    final result = await _repo.getBuildings(search: search);
    result.fold(
      (failure) => emit(BuildingListError(failure.message)),
      (data) => emit(BuildingListLoaded(data)),
    );
  }

  Future<void> refresh() => loadBuildings(search: _lastSearch);

  Future<void> deleteBuilding(String id) async {
    final result = await _repo.deleteBuilding(id);
    result.fold(
      (failure) => emit(BuildingListError(failure.message)),
      (_) => refresh(),
    );
  }

  Future<void> toggleActive(String id, {required bool isCurrentlyActive}) async {
    final result = isCurrentlyActive
        ? await _repo.deactivateBuilding(id)
        : await _repo.activateBuilding(id);
    result.fold(
      (failure) => emit(BuildingListError(failure.message)),
      (_) => refresh(),
    );
  }
}
