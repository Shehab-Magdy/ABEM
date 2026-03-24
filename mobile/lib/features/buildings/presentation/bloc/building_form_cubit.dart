import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../shared/domain/failures/failures.dart';
import '../../data/repositories/building_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class BuildingFormState extends Equatable {
  const BuildingFormState();
  @override
  List<Object?> get props => [];
}

class BuildingFormInitial extends BuildingFormState {
  const BuildingFormInitial();
}

class BuildingFormSubmitting extends BuildingFormState {
  const BuildingFormSubmitting();
}

class BuildingFormSuccess extends BuildingFormState {
  final Map<String, dynamic> building;
  const BuildingFormSuccess(this.building);

  @override
  List<Object?> get props => [building];
}

class BuildingFormError extends BuildingFormState {
  final String message;
  final Map<String, dynamic>? fieldErrors;
  const BuildingFormError(this.message, {this.fieldErrors});

  @override
  List<Object?> get props => [message, fieldErrors];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class BuildingFormCubit extends Cubit<BuildingFormState> {
  final BuildingRepository _repo;
  BuildingFormCubit(this._repo) : super(const BuildingFormInitial());

  Future<void> createBuilding(Map<String, dynamic> payload) async {
    emit(const BuildingFormSubmitting());
    final result = await _repo.createBuilding(payload);
    result.fold(
      (failure) => emit(
        BuildingFormError(
          failure.message,
          fieldErrors: failure is ServerFailure ? failure.fieldErrors : null,
        ),
      ),
      (building) => emit(BuildingFormSuccess(building)),
    );
  }

  Future<void> updateBuilding(String id, Map<String, dynamic> payload) async {
    emit(const BuildingFormSubmitting());
    final result = await _repo.updateBuilding(id, payload);
    result.fold(
      (failure) => emit(
        BuildingFormError(
          failure.message,
          fieldErrors: failure is ServerFailure ? failure.fieldErrors : null,
        ),
      ),
      (building) => emit(BuildingFormSuccess(building)),
    );
  }

  void reset() => emit(const BuildingFormInitial());
}
