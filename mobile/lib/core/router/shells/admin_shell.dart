import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../features/auth/bloc/auth_bloc.dart';
import '../../../features/profile/screens/profile_screen.dart';
import '../routes.dart';

class AdminShell extends StatefulWidget {
  final StatefulNavigationShell navigationShell;

  const AdminShell({super.key, required this.navigationShell});

  @override
  State<AdminShell> createState() => _AdminShellState();
}

class _AdminShellState extends State<AdminShell> {
  final _scaffoldKey = GlobalKey<ScaffoldState>();

  final _navItems = const [
    _NavItem(icon: Icons.dashboard_outlined, selectedIcon: Icons.dashboard, label: 'Dashboard', route: Routes.adminDashboard),
    _NavItem(icon: Icons.apartment_outlined, selectedIcon: Icons.apartment, label: 'Buildings', route: Routes.adminBuildings),
    _NavItem(icon: Icons.receipt_long_outlined, selectedIcon: Icons.receipt_long, label: 'Expenses', route: Routes.adminExpenses),
    _NavItem(icon: Icons.payment_outlined, selectedIcon: Icons.payment, label: 'Payments', route: Routes.adminPayments),
    _NavItem(icon: Icons.drag_indicator_outlined, selectedIcon: Icons.drag_indicator, label: 'More ▸', route: Routes.adminMore),
  ];

  List<_DrawerItem> get _drawerItems => [
        _DrawerItem(title: 'Users', icon: Icons.group_outlined, route: Routes.adminUsers),
        _DrawerItem(title: 'Assets', icon: Icons.inventory_2_outlined, route: Routes.adminAssets),
        _DrawerItem(title: 'Audit Log', icon: Icons.assignment_turned_in_outlined, route: Routes.adminAudit),
        _DrawerItem(title: 'Notifications', icon: Icons.notifications_outlined, route: Routes.adminNotifications),
        _DrawerItem(title: 'Settings', icon: Icons.settings_outlined, route: Routes.adminSettings),
      ];

  void _onDestinationSelected(int index) {
    widget.navigationShell.goBranch(
      index,
      initialLocation: index == widget.navigationShell.currentIndex,
    );
  }

  void _handleDrawerSelection(BuildContext context, _DrawerItem item) {
    Navigator.of(context).pop();
    if (item.route != null) {
      context.go(item.route!);
    } else if (item.action != null) {
      item.action!(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentIndex = widget.navigationShell.currentIndex;
    final title = _navItems[currentIndex.clamp(0, _navItems.length - 1)].label;

    return Scaffold(
      key: _scaffoldKey,
      appBar: AppBar(
        title: Text(title),
        leading: IconButton(
          icon: const Icon(Icons.menu),
          onPressed: () => _scaffoldKey.currentState?.openDrawer(),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.account_circle_outlined),
            tooltip: 'Profile',
            onPressed: () => context.push(Routes.profile),
          ),
        ],
      ),
      drawer: Drawer(
        child: SafeArea(
          child: ListView(
            padding: EdgeInsets.zero,
            children: [
              const DrawerHeader(
                child: ListTile(
                  leading: CircleAvatar(child: Icon(Icons.apartment)),
                  title: Text('Admin Menu'),
                  subtitle: Text('Quick actions'),
                ),
              ),
              ..._drawerItems.map(
                (item) => ListTile(
                  leading: Icon(item.icon),
                  title: Text(item.title),
                  onTap: () => _handleDrawerSelection(context, item),
                ),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.logout),
                title: const Text('Logout'),
                onTap: () {
                  Navigator.of(context).pop();
                  context.read<AuthBloc>().add(const AuthLogoutRequested());
                },
              ),
            ],
          ),
        ),
      ),
      body: widget.navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: _onDestinationSelected,
        destinations: _navItems
            .map(
              (item) => NavigationDestination(
                icon: Icon(item.icon),
                selectedIcon: Icon(item.selectedIcon),
                label: item.label,
              ),
            )
            .toList(),
      ),
    );
  }
}

class _NavItem {
  final IconData icon;
  final IconData selectedIcon;
  final String label;
  final String route;

  const _NavItem({
    required this.icon,
    required this.selectedIcon,
    required this.label,
    required this.route,
  });
}

class _DrawerItem {
  final String title;
  final IconData icon;
  final String? route;
  final void Function(BuildContext context)? action;

  const _DrawerItem({
    required this.title,
    required this.icon,
    this.route,
    this.action,
  });
}
