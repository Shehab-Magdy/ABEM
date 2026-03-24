part of 'expense_detail_cubit.dart';

abstract class ExpenseDetailState extends Equatable {
  const ExpenseDetailState();

  @override
  List<Object?> get props => [];
}

class ExpenseDetailInitial extends ExpenseDetailState {
  const ExpenseDetailInitial();
}

class ExpenseDetailLoading extends ExpenseDetailState {
  const ExpenseDetailLoading();
}

class ExpenseDetailLoaded extends ExpenseDetailState {
  final Map<String, dynamic> expense;
  const ExpenseDetailLoaded(this.expense);

  @override
  List<Object?> get props => [expense];
}

class ExpenseDetailDeleted extends ExpenseDetailState {
  const ExpenseDetailDeleted();
}

class ExpenseDetailError extends ExpenseDetailState {
  final String message;
  const ExpenseDetailError(this.message);

  @override
  List<Object?> get props => [message];
}
