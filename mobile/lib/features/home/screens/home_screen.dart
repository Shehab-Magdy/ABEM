import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../auth/bloc/auth_bloc.dart';
import '../../buildings/screens/buildings_screen.dart';
import '../../expenses/screens/expenses_screen.dart';
import '../../payments/screens/payments_screen.dart';
import '../../notifications/screens/notifications_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    BuildingsScreen(),
    ExpensesScreen(),
    PaymentsScreen(),
    NotificationsScreen(),
  ];

  CircleAvatar _buildAvatar(
    Map<String, dynamic> user,
    ThemeData theme, {
    double radius = 20,
    double fontSize = 14,
  }) {
    final pictureUrl = user['profile_picture'] as String?;
    final initials =
        ((user['first_name'] as String? ?? '?')[0]).toUpperCase();
    if (pictureUrl != null && pictureUrl.isNotEmpty) {
      return CircleAvatar(
        radius: radius,
        backgroundImage: CachedNetworkImageProvider(pictureUrl),
      );
    }
    return CircleAvatar(
      radius: radius,
      backgroundColor: theme.colorScheme.primary,
      child: Text(
        initials,
        style: TextStyle(color: theme.colorScheme.onPrimary, fontSize: fontSize),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final authState = context.watch<AuthBloc>().state;
    final user = authState is AuthAuthenticated ? authState.user : null;
    final role = user?['role'] as String? ?? '';

    return Scaffold(
      appBar: AppBar(
        title: const Text('ABEM'),
        centerTitle: false,
        actions: [
          // User avatar chip — taps open Profile screen
          if (user != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(
                child: GestureDetector(
                  onTap: () => context.push('/profile'),
                  child: Chip(
                    avatar: _buildAvatar(
                      user,
                      theme,
                      radius: 14,
                      fontSize: 12,
                    ),
                    label: Text(user['first_name'] as String? ?? ''),
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                ),
              ),
            ),
          IconButton(
            icon: const Icon(Icons.logout_outlined),
            tooltip: 'Sign out',
            onPressed: () =>
                context.read<AuthBloc>().add(AuthLogoutRequested()),
          ),
        ],
      ),
      body: _screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) =>
            setState(() => _currentIndex = index),
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.apartment_outlined),
            selectedIcon: Icon(Icons.apartment),
            label: 'Buildings',
          ),
          const NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long),
            label: 'Expenses',
          ),
          const NavigationDestination(
            icon: Icon(Icons.payment_outlined),
            selectedIcon: Icon(Icons.payment),
            label: 'Payments',
          ),
          NavigationDestination(
            icon: const Icon(Icons.notifications_outlined),
            selectedIcon: const Icon(Icons.notifications),
            label: 'Notifications',
          ),
        ],
      ),
    );
  }
}
