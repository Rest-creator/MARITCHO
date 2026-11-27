import 'package:flutter/material.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/accounts/presentation/pages/account_page.dart';
import 'package:mobile/features/jobs/presentation/pages/employer_home_page.dart';
import 'package:mobile/features/jobs/presentation/pages/worker_home_page.dart';
import 'package:mobile/features/workers/presentation/pages/my_work_page.dart';
import 'package:mobile/features/workers/presentation/pages/workers_directory_page.dart';

class MainNavigationShell extends StatefulWidget {
  final String initialRole;

  const MainNavigationShell({super.key, required this.initialRole});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  late String _currentRole;
  int _selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    _currentRole = widget.initialRole;
  }

  void _onRoleSwitched() {
    setState(() {
      _currentRole = _currentRole == 'WORKER' ? 'BUYER' : 'WORKER';
      _selectedIndex = 0;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isWorker = _currentRole == 'WORKER';

    final List<Widget> pages = isWorker
        ? [
            const WorkerHomePage(),
            const MyWorkPage(),
            AccountPage(onRoleSwitched: _onRoleSwitched),
          ]
        : [
            const EmployerHomePage(),
            const WorkersDirectoryPage(),
            AccountPage(onRoleSwitched: _onRoleSwitched),
          ];

    final List<NavigationDestination> destinations = isWorker
        ? const [
            NavigationDestination(
              icon: Icon(Icons.search),
              selectedIcon: Icon(Icons.search, color: AppTheme.primaryBlueGray),
              label: 'Find Jobs',
            ),
            NavigationDestination(
              icon: Icon(Icons.work_outline),
              selectedIcon: Icon(Icons.work, color: AppTheme.primaryBlueGray),
              label: 'My Work',
            ),
            NavigationDestination(
              icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person, color: AppTheme.primaryBlueGray),
              label: 'Account',
            ),
          ]
        : const [
            NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home, color: AppTheme.primaryBlueGray),
              label: 'Jobs',
            ),
            NavigationDestination(
              icon: Icon(Icons.people_outline),
              selectedIcon: Icon(Icons.people, color: AppTheme.primaryBlueGray),
              label: 'Workers',
            ),
            NavigationDestination(
              icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person, color: AppTheme.primaryBlueGray),
              label: 'Account',
            ),
          ];

    if (_selectedIndex >= pages.length) {
      _selectedIndex = 0;
    }

    return Scaffold(
      body: IndexedStack(index: _selectedIndex, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (int index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: destinations,
      ),
    );
  }
}
