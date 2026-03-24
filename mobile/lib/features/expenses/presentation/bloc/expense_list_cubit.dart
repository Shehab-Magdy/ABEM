import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/expense_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class ExpenseListState extends Equatable {
  const ExpenseListState();
  @override
  List<Object?> get props => [];
}

class ExpenseListInitial extends ExpenseListState {
  const ExpenseListInitial();
}

class ExpenseListLoading extends ExpenseListState {
  const ExpenseListLoading();
}

class ExpenseListLoaded extends ExpenseListState {
  final List<Map<String, dynamic>> expenses;
  final bool hasMore;
  const ExpenseListLoaded(this.expenses, {this.hasMore = false});

  @override
  List<Object?> get props => [expenses, hasMore];
}

class ExpenseListError extends ExpenseListState {
  final String message;
  const ExpenseListError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class ExpenseListCubit extends Cubit<ExpenseListState> {
  final ExpenseRepository _repo;
  String? _lastBuildingId;
  String? _lastSearch;
  int _currentPage = 1;
  static const int _pageSize = 20;

  ExpenseListCubit(this._repo) : super(const ExpenseListInitial());

  Future<void> loadExpenses({String? buildingId, String? search}) async {
    _lastBuildingId = buildingId;
    _lastSearch = search;
    _currentPage = 1;
    emit(const ExpenseListLoading());
    final result = await _repo.getExpenses(
      buildingId: buildingId,
      page: _currentPage,
      pageSize: _pageSize,
    );
    result.fold(
      (failure) => emit(ExpenseListError(failure.message)),
      (data) => emit(ExpenseListLoaded(
        data,
        hasMore: data.length >= _pageSize,
      )),
    );
  }

  Future<void> loadMore() async {
    final currentState = state;
    if (currentState is! ExpenseListLoaded || !currentState.hasMore) return;

    _currentPage++;
    final result = await _repo.getExpenses(
      buildingId: _lastBuildingId,
      page: _currentPage,
      pageSize: _pageSize,
    );
    result.fold(
      (failure) {
        _currentPage--;
        emit(ExpenseListError(failure.message));
      },
      (data) => emit(ExpenseListLoaded(
        [...currentState.expenses, ...data],
        hasMore: data.length >= _pageSize,
      )),
    );
  }

  Future<void> refresh() =>
      loadExpenses(buildingId: _lastBuildingId, search: _lastSearch);

  Future<void> deleteExpense(String id) async {
    final result = await _repo.deleteExpense(id);
    result.fold(
      (failure) => emit(ExpenseListError(failure.message)),
      (_) => refresh(),
    );
  }
}
