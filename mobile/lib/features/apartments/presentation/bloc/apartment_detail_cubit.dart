import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/apartment_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class ApartmentDetailState extends Equatable {
  const ApartmentDetailState();
  @override
  List<Object?> get props => [];
}

class ApartmentDetailInitial extends ApartmentDetailState {
  const ApartmentDetailInitial();
}

class ApartmentDetailLoading extends ApartmentDetailState {
  const ApartmentDetailLoading();
}

class ApartmentDetailLoaded extends ApartmentDetailState {
  final Map<String, dynamic> apartment;
  final Map<String, dynamic>? balance;
  const ApartmentDetailLoaded(this.apartment, {this.balance});

  @override
  List<Object?> get props => [apartment, balance];
}

class ApartmentDetailError extends ApartmentDetailState {
  final String message;
  const ApartmentDetailError(this.message);

  @override
  List<Object?> get props => [message];
}

/// Invite generation sub-states.
class ApartmentInviteGenerated extends ApartmentDetailState {
  final Map<String, dynamic> apartment;
  final Map<String, dynamic>? balance;
  final String code;
  final String? expiresAt;
  const ApartmentInviteGenerated({
    required this.apartment,
    this.balance,
    required this.code,
    this.expiresAt,
  });

  @override
  List<Object?> get props => [apartment, balance, code, expiresAt];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class ApartmentDetailCubit extends Cubit<ApartmentDetailState> {
  final ApartmentRepository _repo;
  ApartmentDetailCubit(this._repo) : super(const ApartmentDetailInitial());

  Future<void> load(String id) async {
    emit(const ApartmentDetailLoading());

    final aptResult = await _repo.getApartment(id);
    await aptResult.fold(
      (failure) async => emit(ApartmentDetailError(failure.message)),
      (apartment) async {
        // Also fetch balance
        final balResult = await _repo.getBalance(id);
        final balance = balResult.fold((_) => null, (b) => b);
        emit(ApartmentDetailLoaded(apartment, balance: balance));
      },
    );
  }

  Future<void> updateStatus(String id, String status) async {
    final result = await _repo.updateApartment(id, {'status': status});
    result.fold(
      (failure) => emit(ApartmentDetailError(failure.message)),
      (_) => load(id),
    );
  }

  Future<void> generateInvite(String apartmentId) async {
    final currentState = state;
    final result = await _repo.generateInvite(apartmentId);
    result.fold(
      (failure) => emit(ApartmentDetailError(failure.message)),
      (data) {
        final code = (data['token'] ?? data['code'] ?? '').toString();
        final expiresAt = data['expires_at']?.toString();
        if (currentState is ApartmentDetailLoaded) {
          emit(ApartmentInviteGenerated(
            apartment: currentState.apartment,
            balance: currentState.balance,
            code: code,
            expiresAt: expiresAt,
          ));
        }
      },
    );
  }
}
