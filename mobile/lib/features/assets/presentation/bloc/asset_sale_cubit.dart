import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/asset_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class AssetSaleState extends Equatable {
  const AssetSaleState();
  @override
  List<Object?> get props => [];
}

class AssetSaleInitial extends AssetSaleState {
  const AssetSaleInitial();
}

class AssetSaleSubmitting extends AssetSaleState {
  const AssetSaleSubmitting();
}

class AssetSaleSold extends AssetSaleState {
  final Map<String, dynamic> asset;
  const AssetSaleSold(this.asset);

  @override
  List<Object?> get props => [asset];
}

class AssetSaleError extends AssetSaleState {
  final String message;
  const AssetSaleError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class AssetSaleCubit extends Cubit<AssetSaleState> {
  final AssetRepository _repo;

  AssetSaleCubit(this._repo) : super(const AssetSaleInitial());

  Future<void> recordSale(
    String assetId,
    Map<String, dynamic> payload,
  ) async {
    emit(const AssetSaleSubmitting());
    final result = await _repo.sellAsset(assetId, payload);
    result.fold(
      (failure) => emit(AssetSaleError(failure.message)),
      (data) => emit(AssetSaleSold(data)),
    );
  }
}
