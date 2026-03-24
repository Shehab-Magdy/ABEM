import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/dashboard_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class AdminDashboardState extends Equatable {
  const AdminDashboardState();
  @override
  List<Object?> get props => [];
}

class AdminDashboardInitial extends AdminDashboardState {
  const AdminDashboardInitial();
}

class AdminDashboardLoading extends AdminDashboardState {
  const AdminDashboardLoading();
}

class AdminDashboardLoaded extends AdminDashboardState {
  final Map<String, dynamic> data;
  const AdminDashboardLoaded(this.data);

  @override
  List<Object?> get props => [data];
}

class AdminDashboardError extends AdminDashboardState {
  final String message;
  const AdminDashboardError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class AdminDashboardCubit extends Cubit<AdminDashboardState> {
  final DashboardRepository _repo;
  String? _lastBuildingId;
  String? _lastDateFrom;
  String? _lastDateTo;

  AdminDashboardCubit(this._repo) : super(const AdminDashboardInitial());

  Future<void> load({
    String? buildingId,
    String? dateFrom,
    String? dateTo,
  }) async {
    _lastBuildingId = buildingId;
    _lastDateFrom = dateFrom;
    _lastDateTo = dateTo;
    emit(const AdminDashboardLoading());
    final result = await _repo.getAdminDashboard(
      buildingId: buildingId,
      dateFrom: dateFrom,
      dateTo: dateTo,
    );
    result.fold(
      (failure) => emit(AdminDashboardError(failure.message)),
      (data) => emit(AdminDashboardLoaded(data)),
    );
  }

  Future<void> refresh() => load(
        buildingId: _lastBuildingId,
        dateFrom: _lastDateFrom,
        dateTo: _lastDateTo,
      );
}
