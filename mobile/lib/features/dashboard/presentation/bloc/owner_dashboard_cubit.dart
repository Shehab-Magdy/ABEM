import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/dashboard_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class OwnerDashboardState extends Equatable {
  const OwnerDashboardState();
  @override
  List<Object?> get props => [];
}

class OwnerDashboardInitial extends OwnerDashboardState {
  const OwnerDashboardInitial();
}

class OwnerDashboardLoading extends OwnerDashboardState {
  const OwnerDashboardLoading();
}

class OwnerDashboardLoaded extends OwnerDashboardState {
  final Map<String, dynamic> data;
  const OwnerDashboardLoaded(this.data);

  @override
  List<Object?> get props => [data];
}

class OwnerDashboardError extends OwnerDashboardState {
  final String message;
  const OwnerDashboardError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class OwnerDashboardCubit extends Cubit<OwnerDashboardState> {
  final DashboardRepository _repo;
  String? _lastDateFrom;
  String? _lastDateTo;

  OwnerDashboardCubit(this._repo) : super(const OwnerDashboardInitial());

  Future<void> load({
    String? dateFrom,
    String? dateTo,
  }) async {
    _lastDateFrom = dateFrom;
    _lastDateTo = dateTo;
    emit(const OwnerDashboardLoading());
    final result = await _repo.getOwnerDashboard(
      dateFrom: dateFrom,
      dateTo: dateTo,
    );
    result.fold(
      (failure) => emit(OwnerDashboardError(failure.message)),
      (data) => emit(OwnerDashboardLoaded(data)),
    );
  }

  Future<void> refresh() => load(
        dateFrom: _lastDateFrom,
        dateTo: _lastDateTo,
      );
}
