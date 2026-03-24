import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/expense_repository.dart';

part 'expense_detail_state.dart';

class ExpenseDetailCubit extends Cubit<ExpenseDetailState> {
  final ExpenseRepository _repo;
  String? _expenseId;

  ExpenseDetailCubit(this._repo) : super(const ExpenseDetailInitial());

  Future<void> load(String id) async {
    _expenseId = id;
    emit(const ExpenseDetailLoading());
    final result = await _repo.getExpense(id);
    result.fold(
      (failure) => emit(ExpenseDetailError(failure.message)),
      (expense) => emit(ExpenseDetailLoaded(expense)),
    );
  }

  Future<void> refresh() async {
    final id = _expenseId;
    if (id == null) return;
    await load(id);
  }

  Future<void> delete(String? id) async {
    final targetId = id ?? _expenseId;
    if (targetId == null) return;
    emit(const ExpenseDetailLoading());
    final result = await _repo.deleteExpense(targetId);
    result.fold(
      (failure) => emit(ExpenseDetailError(failure.message)),
      (_) => emit(const ExpenseDetailDeleted()),
    );
  }
}
