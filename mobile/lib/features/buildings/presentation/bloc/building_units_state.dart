part of 'building_units_cubit.dart';

abstract class BuildingUnitsState extends Equatable {
  const BuildingUnitsState();

  @override
  List<Object?> get props => [];
}

class BuildingUnitsInitial extends BuildingUnitsState {
  const BuildingUnitsInitial();
}

class BuildingUnitsLoading extends BuildingUnitsState {
  const BuildingUnitsLoading();
}

class BuildingUnitsRefreshing extends BuildingUnitsState {
  final List<Map<String, dynamic>> units;
  const BuildingUnitsRefreshing(this.units);

  @override
  List<Object?> get props => [units];
}

class BuildingUnitsLoaded extends BuildingUnitsState {
  final List<Map<String, dynamic>> units;
  const BuildingUnitsLoaded(this.units);

  @override
  List<Object?> get props => [units];
}

class BuildingUnitsError extends BuildingUnitsState {
  final String message;
  const BuildingUnitsError(this.message);

  @override
  List<Object?> get props => [message];
}
