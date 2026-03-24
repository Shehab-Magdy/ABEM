import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/building_repository.dart';

part 'building_units_state.dart';

class BuildingUnitsCubit extends Cubit<BuildingUnitsState> {
  final BuildingRepository _repo;
  String? _buildingId;

  BuildingUnitsCubit(this._repo) : super(const BuildingUnitsInitial());

  Future<void> load(String buildingId) async {
    _buildingId = buildingId;
    emit(const BuildingUnitsLoading());
    final result = await _repo.getBuildingUnits(buildingId);
    result.fold(
      (failure) => emit(BuildingUnitsError(failure.message)),
      (units) => emit(BuildingUnitsLoaded(units)),
    );
  }

  Future<void> refresh() async {
    final id = _buildingId;
    if (id == null) return;
    final currentState = state;
    if (currentState is BuildingUnitsLoaded) {
      emit(BuildingUnitsRefreshing(currentState.units));
    }
    final result = await _repo.getBuildingUnits(id);
    result.fold(
      (failure) => emit(BuildingUnitsError(failure.message)),
      (units) => emit(BuildingUnitsLoaded(units)),
    );
  }
}
