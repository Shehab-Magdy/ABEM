import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:internet_connection_checker/internet_connection_checker.dart';

// ── State ─────────────────────────────────────────────────────────────────────

enum ConnectivityStatus { online, offline, unknown }

class ConnectivityState extends Equatable {
  final ConnectivityStatus status;
  const ConnectivityState(this.status);

  bool get isOnline => status == ConnectivityStatus.online;
  bool get isOffline => status == ConnectivityStatus.offline;

  @override
  List<Object?> get props => [status];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

/// Monitors internet connectivity and emits online/offline states.
///
/// Uses [connectivity_plus] for network change events and
/// [internet_connection_checker] for actual internet reachability.
class ConnectivityCubit extends Cubit<ConnectivityState> {
  final InternetConnectionChecker _checker;
  StreamSubscription<InternetConnectionStatus>? _subscription;

  ConnectivityCubit(this._checker)
      : super(const ConnectivityState(ConnectivityStatus.unknown)) {
    _subscription = _checker.onStatusChange.listen((status) {
      emit(ConnectivityState(
        status == InternetConnectionStatus.connected
            ? ConnectivityStatus.online
            : ConnectivityStatus.offline,
      ));
    });
    // Initial check
    _checker.hasConnection.then((connected) {
      emit(ConnectivityState(
        connected ? ConnectivityStatus.online : ConnectivityStatus.offline,
      ));
    });
  }

  @override
  Future<void> close() {
    _subscription?.cancel();
    return super.close();
  }
}
