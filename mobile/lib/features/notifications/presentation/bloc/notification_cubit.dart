import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/notification_repository.dart';

// ── State ─────────────────────────────────────────────────────────────────────

abstract class NotificationState extends Equatable {
  const NotificationState();
  @override
  List<Object?> get props => [];
}

class NotificationInitial extends NotificationState {
  const NotificationInitial();
}

class NotificationLoading extends NotificationState {
  const NotificationLoading();
}

class NotificationLoaded extends NotificationState {
  final List<Map<String, dynamic>> items;
  final int unreadCount;
  const NotificationLoaded(this.items, {this.unreadCount = 0});

  @override
  List<Object?> get props => [items, unreadCount];
}

class NotificationError extends NotificationState {
  final String message;
  const NotificationError(this.message);

  @override
  List<Object?> get props => [message];
}

// ── Cubit ─────────────────────────────────────────────────────────────────────

class NotificationCubit extends Cubit<NotificationState> {
  final NotificationRepository _repo;
  int _currentPage = 1;
  static const int _pageSize = 20;

  NotificationCubit(this._repo) : super(const NotificationInitial());

  Future<void> loadNotifications() async {
    _currentPage = 1;
    emit(const NotificationLoading());
    final result = await _repo.getNotifications(
      page: _currentPage,
      pageSize: _pageSize,
    );
    result.fold(
      (failure) => emit(NotificationError(failure.message)),
      (data) {
        final unread = data.where((n) => n['is_read'] != true).length;
        emit(NotificationLoaded(data, unreadCount: unread));
      },
    );
  }

  Future<void> loadMore() async {
    final currentState = state;
    if (currentState is! NotificationLoaded) return;

    _currentPage++;
    final result = await _repo.getNotifications(
      page: _currentPage,
      pageSize: _pageSize,
    );
    result.fold(
      (failure) {
        _currentPage--;
        emit(NotificationError(failure.message));
      },
      (data) {
        final allItems = [...currentState.items, ...data];
        final unread = allItems.where((n) => n['is_read'] != true).length;
        emit(NotificationLoaded(allItems, unreadCount: unread));
      },
    );
  }

  Future<void> markRead(String id) async {
    final result = await _repo.markRead(id);
    result.fold(
      (failure) => emit(NotificationError(failure.message)),
      (_) => loadNotifications(),
    );
  }

  Future<void> markAllRead() async {
    final result = await _repo.markAllRead();
    result.fold(
      (failure) => emit(NotificationError(failure.message)),
      (_) => loadNotifications(),
    );
  }

  Future<void> refresh() => loadNotifications();
}
