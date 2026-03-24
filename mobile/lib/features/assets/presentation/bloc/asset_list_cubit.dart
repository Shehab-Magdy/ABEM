import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/asset_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class AssetListState extends Equatable {
  const AssetListState();
  @override
  List<Object?> get props => [];
}

class AssetListInitial extends AssetListState {
  const AssetListInitial();
}

class AssetListLoading extends AssetListState {
  const AssetListLoading();
}

class AssetListLoaded extends AssetListState {
  final List<Map<String, dynamic>> assets;
  final double totalSaleProceeds;
  const AssetListLoaded(this.assets, {this.totalSaleProceeds = 0});

  @override
  List<Object?> get props => [assets, totalSaleProceeds];
}

class AssetListError extends AssetListState {
  final String message;
  const AssetListError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class AssetListCubit extends Cubit<AssetListState> {
  final AssetRepository _repo;
  String? _lastBuildingId;

  AssetListCubit(this._repo) : super(const AssetListInitial());

  Future<void> loadAssets({String? buildingId}) async {
    _lastBuildingId = buildingId;
    emit(const AssetListLoading());
    final result = await _repo.getAssets(buildingId: buildingId);
    result.fold(
      (failure) => emit(AssetListError(failure.message)),
      (data) {
        double totalProceeds = 0;
        for (final asset in data) {
          final salePrice =
              double.tryParse(asset['sale_price']?.toString() ?? '0') ?? 0;
          if (asset['is_sold'] == true) {
            totalProceeds += salePrice;
          }
        }
        emit(AssetListLoaded(data, totalSaleProceeds: totalProceeds));
      },
    );
  }

  Future<void> refresh() => loadAssets(buildingId: _lastBuildingId);
}
