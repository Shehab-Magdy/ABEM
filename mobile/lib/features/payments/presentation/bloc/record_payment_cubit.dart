import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/payment_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class RecordPaymentState extends Equatable {
  const RecordPaymentState();
  @override
  List<Object?> get props => [];
}

class RecordPaymentInitial extends RecordPaymentState {
  const RecordPaymentInitial();
}

class RecordPaymentLoading extends RecordPaymentState {
  const RecordPaymentLoading();
}

class RecordPaymentRecording extends RecordPaymentState {
  const RecordPaymentRecording();
}

class RecordPaymentRecorded extends RecordPaymentState {
  final Map<String, dynamic> payment;
  const RecordPaymentRecorded(this.payment);

  @override
  List<Object?> get props => [payment];
}

class RecordPaymentError extends RecordPaymentState {
  final String message;
  const RecordPaymentError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class RecordPaymentCubit extends Cubit<RecordPaymentState> {
  final PaymentRepository _repo;

  RecordPaymentCubit(this._repo) : super(const RecordPaymentInitial());

  Future<void> recordPayment(Map<String, dynamic> payload) async {
    emit(const RecordPaymentRecording());
    final result = await _repo.recordPayment(payload);
    result.fold(
      (failure) => emit(RecordPaymentError(failure.message)),
      (data) => emit(RecordPaymentRecorded(data)),
    );
  }
}
