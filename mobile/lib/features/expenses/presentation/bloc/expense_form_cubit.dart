import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/expense_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class ExpenseFormState extends Equatable {
  const ExpenseFormState();
  @override
  List<Object?> get props => [];
}

class ExpenseFormInitial extends ExpenseFormState {
  const ExpenseFormInitial();
}

class ExpenseFormLoading extends ExpenseFormState {
  const ExpenseFormLoading();
}

class ExpenseFormCategoriesLoaded extends ExpenseFormState {
  final List<Map<String, dynamic>> categories;
  const ExpenseFormCategoriesLoaded(this.categories);

  @override
  List<Object?> get props => [categories];
}

class ExpenseFormSubmitting extends ExpenseFormState {
  const ExpenseFormSubmitting();
}

class ExpenseFormCreated extends ExpenseFormState {
  final Map<String, dynamic> expense;
  const ExpenseFormCreated(this.expense);

  @override
  List<Object?> get props => [expense];
}

class ExpenseFormError extends ExpenseFormState {
  final String message;
  const ExpenseFormError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class ExpenseFormCubit extends Cubit<ExpenseFormState> {
  final ExpenseRepository _repo;

  ExpenseFormCubit(this._repo) : super(const ExpenseFormInitial());

  Future<void> loadCategories({String? buildingId}) async {
    emit(const ExpenseFormLoading());
    final result = await _repo.getCategories(buildingId: buildingId);
    result.fold(
      (failure) => emit(ExpenseFormError(failure.message)),
      (data) => emit(ExpenseFormCategoriesLoaded(data)),
    );
  }

  Future<void> createExpense(Map<String, dynamic> payload) async {
    emit(const ExpenseFormSubmitting());
    final result = await _repo.createExpense(payload);
    result.fold(
      (failure) => emit(ExpenseFormError(failure.message)),
      (data) => emit(ExpenseFormCreated(data)),
    );
  }

  Future<void> updateExpense(String id, Map<String, dynamic> payload) async {
    emit(const ExpenseFormSubmitting());
    final result = await _repo.updateExpense(id, payload);
    result.fold(
      (failure) => emit(ExpenseFormError(failure.message)),
      (data) => emit(ExpenseFormCreated(data)),
    );
  }
}
