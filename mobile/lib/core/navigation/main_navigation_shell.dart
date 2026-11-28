import 'package:flutter/material.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/core/theme/screen_shell.dart';
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

    final List<_NavTabItem> tabs = isWorker
        ? const [
            _NavTabItem(icon: Icons.search, label: 'Find Jobs'),
            _NavTabItem(icon: Icons.work_outline, label: 'My Work'),
            _NavTabItem(icon: Icons.person_outline, label: 'Account'),
          ]
        : const [
            _NavTabItem(icon: Icons.home_outlined, label: 'Jobs'),
            _NavTabItem(icon: Icons.people_outline, label: 'Workers'),
            _NavTabItem(icon: Icons.person_outline, label: 'Account'),
          ];

    return ScreenShell(
      safeArea: false,
      child: Stack(
        children: [
          // Current page
          Positioned.fill(
            bottom: 72,
            child: SafeArea(
              bottom: false,
              child: IndexedStack(index: _selectedIndex, children: pages),
            ),
          ),

          // Floating Glass Tab Bar matching web's TabBar.tsx
          Positioned(
            left: 20,
            right: 20,
            bottom: 16,
            child: SafeArea(
              top: false,
              child: Container(
                height: 64,
                decoration: BoxDecoration(
                  color: AppTheme.colorNav.withValues(alpha: 0.92),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: AppTheme.lineStrong, width: 1.0),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.35),
                      blurRadius: 18,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    for (int i = 0; i < tabs.length; i++)
                      _buildTabButton(
                        item: tabs[i],
                        isSelected: _selectedIndex == i,
                        onTap: () => setState(() => _selectedIndex = i),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabButton({
    required _NavTabItem item,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.glassSelected : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected
                ? AppTheme.cyanAccent.withValues(alpha: 0.4)
                : Colors.transparent,
            width: 1.0,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              item.icon,
              size: 22,
              color: isSelected ? AppTheme.cyanAccent : AppTheme.textMuted,
            ),
            const SizedBox(height: 2),
            Text(
              item.label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                color: isSelected ? AppTheme.text : AppTheme.textMuted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavTabItem {
  final IconData icon;
  final String label;

  const _NavTabItem({required this.icon, required this.label});
}
