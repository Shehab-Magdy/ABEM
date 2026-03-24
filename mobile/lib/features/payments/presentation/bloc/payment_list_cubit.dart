import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/payment_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class PaymentListState extends Equatable {
  const PaymentListState();
  @override
  List<Object?> get props => [];
}

class PaymentListInitial extends PaymentListState {
  const PaymentListInitial();
}

class PaymentListLoading extends PaymentListState {
  const PaymentListLoading();
}

class PaymentListLoaded extends PaymentListState {
  final List<Map<String, dynamic>> payments;
  const PaymentListLoaded(this.payments);

  @override
  List<Object?> get props => [payments];
}

class PaymentListError extends PaymentListState {
  final String message;
  const PaymentListError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class PaymentListCubit extends Cubit<PaymentListState> {
  final PaymentRepository _repo;
  String? _lastApartmentId;

  PaymentListCubit(this._repo) : super(const PaymentListInitial());

  Future<void> loadPayments({String? apartmentId}) async {
    _lastApartmentId = apartmentId;
    emit(const PaymentListLoading());
    final result = await _repo.getPayments(apartmentId: apartmentId);
    result.fold(
      (failure) => emit(PaymentListError(failure.message)),
      (data) => emit(PaymentListLoaded(data)),
    );
  }

  Future<void> refresh() => loadPayments(apartmentId: _lastApartmentId);
}
