import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/audit_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class AuditState extends Equatable {
  const AuditState();
  @override
  List<Object?> get props => [];
}

class AuditInitial extends AuditState {
  const AuditInitial();
}

class AuditLoading extends AuditState {
  const AuditLoading();
}

class AuditLoaded extends AuditState {
  final List<Map<String, dynamic>> logs;
  final bool hasMore;
  const AuditLoaded(this.logs, {this.hasMore = false});

  @override
  List<Object?> get props => [logs, hasMore];
}

class AuditError extends AuditState {
  final String message;
  const AuditError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class AuditCubit extends Cubit<AuditState> {
  final AuditRepository _repo;
  int _currentPage = 1;
  String? _entityType;
  String? _action;
  String? _dateFrom;
  String? _dateTo;
  List<Map<String, dynamic>> _allLogs = [];

  AuditCubit(this._repo) : super(const AuditInitial());

  Future<void> loadLogs({
    String? entityType,
    String? action,
    String? dateFrom,
    String? dateTo,
  }) async {
    _currentPage = 1;
    _allLogs = [];
    _entityType = entityType;
    _action = action;
    _dateFrom = dateFrom;
    _dateTo = dateTo;
    emit(const AuditLoading());
    await _fetchPage();
  }

  Future<void> loadMore() async {
    if (state is! AuditLoaded) return;
    final loaded = state as AuditLoaded;
    if (!loaded.hasMore) return;
    _currentPage++;
    await _fetchPage(append: true);
  }

  Future<void> _fetchPage({bool append = false}) async {
    final result = await _repo.getAuditLogs(
      entityType: _entityType,
      action: _action,
      dateFrom: _dateFrom,
      dateTo: _dateTo,
      page: _currentPage,
    );
    result.fold(
      (failure) => emit(AuditError(failure.message)),
      (data) {
        final results = data.containsKey('results')
            ? List<Map<String, dynamic>>.from(data['results'])
            : List<Map<String, dynamic>>.from(data is List ? data : []);
        final hasNext = data['next'] != null;
        if (append) {
          _allLogs = [..._allLogs, ...results];
        } else {
          _allLogs = results;
        }
        emit(AuditLoaded(_allLogs, hasMore: hasNext));
      },
    );
  }
}
