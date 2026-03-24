import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/building_repository.dart';

part 'building_detail_state.dart';

class BuildingDetailCubit extends Cubit<BuildingDetailState> {
  final BuildingRepository _repo;
  String? _buildingId;

  BuildingDetailCubit(this._repo) : super(const BuildingDetailInitial());

  Future<void> load(String buildingId) async {
    _buildingId = buildingId;
    emit(const BuildingDetailLoading());
    final result = await _repo.getBuilding(buildingId);
    result.fold(
      (failure) => emit(BuildingDetailError(failure.message)),
      (building) => emit(BuildingDetailLoaded(building)),
    );
  }

  Future<void> refresh() async {
    final id = _buildingId;
    if (id == null) return;
    await load(id);
  }

  /// Toggle building active state. Returns `null` on success, or an error
  /// message string if the operation fails (state remains unchanged on error).
  Future<String?> toggleActive() async {
    final id = _buildingId;
    if (id == null) return 'Missing building id';

    final current = state;
    final isActive = current is BuildingDetailLoaded
        ? (current.building['is_active'] as bool? ?? true)
        : true;

    final result = isActive
        ? await _repo.deactivateBuilding(id)
        : await _repo.activateBuilding(id);

    final error = result.fold<String?>((failure) => failure.message, (_) => null);
    if (error == null) {
      await load(id);
    }
    return error;
  }
}
