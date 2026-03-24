part of 'building_detail_cubit.dart';

abstract class BuildingDetailState extends Equatable {
  const BuildingDetailState();

  @override
  List<Object?> get props => [];
}

class BuildingDetailInitial extends BuildingDetailState {
  const BuildingDetailInitial();
}

class BuildingDetailLoading extends BuildingDetailState {
  const BuildingDetailLoading();
}

class BuildingDetailLoaded extends BuildingDetailState {
  final Map<String, dynamic> building;
  const BuildingDetailLoaded(this.building);

  @override
  List<Object?> get props => [building];
}

class BuildingDetailError extends BuildingDetailState {
  final String message;
  const BuildingDetailError(this.message);

  @override
  List<Object?> get props => [message];
}
