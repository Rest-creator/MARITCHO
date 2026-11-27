import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/accounts/data/models/person.dart';
import 'package:mobile/features/accounts/data/repositories/account_repository.dart';
import 'package:mobile/features/accounts/presentation/cubit/account_cubit.dart';
import 'package:mobile/features/accounts/presentation/cubit/account_state.dart';

class AccountPage extends StatelessWidget {
  final VoidCallback? onRoleSwitched;

  const AccountPage({super.key, this.onRoleSwitched});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) =>
          AccountCubit(ctx.read<AccountRepository>())..loadProfile(),
      child: _AccountView(onRoleSwitched: onRoleSwitched),
    );
  }
}

class _AccountView extends StatefulWidget {
  final VoidCallback? onRoleSwitched;

  const _AccountView({this.onRoleSwitched});

  @override
  State<_AccountView> createState() => _AccountViewState();
}

class _AccountViewState extends State<_AccountView> {
  final _nameController = TextEditingController();
  final _suburbController = TextEditingController();
  final _kinPhoneController = TextEditingController();

  double _travelKm = 25.0;
  bool _isAvailable = true;
  bool _initializedFromState = false;

  @override
  void dispose() {
    _nameController.dispose();
    _suburbController.dispose();
    _kinPhoneController.dispose();
    super.dispose();
  }

  void _populateFields(Person person) {
    _nameController.text = person.displayName ?? '';
    _suburbController.text = person.homeSuburb ?? '';
    _kinPhoneController.text = person.nextOfKinPhone ?? '';
    _travelKm = person.travelKm.toDouble().clamp(1.0, 50.0);
    _isAvailable = person.isAvailable;
    _initializedFromState = true;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Account'),
        actions: [
          BlocBuilder<AccountCubit, AccountState>(
            builder: (context, state) {
              if (state is AccountLoaded && state.isSaving) {
                return const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  ),
                );
              }
              return TextButton(
                onPressed: state is AccountLoaded
                    ? () => _saveProfile(context, state.person)
                    : null,
                child: const Text(
                  'Save',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              );
            },
          ),
        ],
      ),
      body: BlocConsumer<AccountCubit, AccountState>(
        listener: (context, state) {
          if (!mounted) return;
          if (state is AccountLoaded && state.noticeMessage != null) {
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(state.noticeMessage!)));
          }
        },
        builder: (context, state) {
          if (state is AccountLoading || state is AccountInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is AccountFailure) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Failed to load profile: ${state.errorMessage}',
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => context.read<AccountCubit>().loadProfile(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final person = (state as AccountLoaded).person;
          if (!_initializedFromState) {
            _populateFields(person);
          }

          final isWorker = person.role == 'WORKER';

          return RefreshIndicator(
            onRefresh: () => context.read<AccountCubit>().loadProfile(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _buildModeSwitchCard(context, person),
                const SizedBox(height: 16),
                _buildProfileDetailsCard(context, person),
                if (isWorker) ...[
                  const SizedBox(height: 16),
                  _buildWorkerSettingsCard(context, person),
                ],
                const SizedBox(height: 16),
                _buildEmergencyContactCard(context, person),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildModeSwitchCard(BuildContext context, Person person) {
    final isWorker = person.role == 'WORKER';
    final targetRole = isWorker ? 'BUYER' : 'WORKER';
    final targetRoleLabel = isWorker ? 'Employer (Hire)' : 'Worker (Find Work)';

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.5)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isWorker ? Icons.handyman : Icons.business,
                  color: AppTheme.primaryBlueGray,
                ),
                const SizedBox(width: 8),
                Text(
                  'Current Mode: ${isWorker ? "Worker" : "Employer"}',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Switch mode to ${targetRoleLabel.toLowerCase()} with the same account.',
              style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.swap_horiz),
                label: Text('Switch to $targetRoleLabel'),
                onPressed: () async {
                  final cubit = context.read<AccountCubit>();
                  final ok = await cubit.switchRole(targetRole);
                  if (ok && mounted) {
                    widget.onRoleSwitched?.call();
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileDetailsCard(BuildContext context, Person person) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.5)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Profile Info',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              'Phone: ${person.phone}',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Display Name / Full Name',
                hintText: 'e.g. Tendai Moyo',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _suburbController,
              decoration: const InputDecoration(
                labelText: 'Home Suburb',
                hintText: 'e.g. Nkulumane, Bulawayo',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWorkerSettingsCard(BuildContext context, Person person) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.5)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Worker Preferences',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Available for work'),
              subtitle: const Text('Appear in employer searches and matches'),
              value: _isAvailable,
              onChanged: (val) {
                setState(() {
                  _isAvailable = val;
                });
              },
            ),
            const Divider(),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Travel Radius',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                Text(
                  '${_travelKm.toInt()} km',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            Slider(
              value: _travelKm,
              min: 1.0,
              max: 50.0,
              divisions: 49,
              label: '${_travelKm.toInt()} km',
              onChanged: (val) {
                setState(() {
                  _travelKm = val;
                });
              },
            ),
            const SizedBox(height: 8),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(
                Icons.handyman,
                color: AppTheme.primaryBlueGray,
              ),
              title: const Text('Manage Skills & Trades'),
              subtitle: const Text('Configure trades and service coverage'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.of(context).pushNamed('/worker-skills');
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmergencyContactCard(BuildContext context, Person person) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.5)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Safety & Emergency Contact',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Optional next-of-kin or emergency phone number.',
              style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _kinPhoneController,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Next-of-kin Phone',
                hintText: '+263 77 ...',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _saveProfile(BuildContext context, Person current) {
    final cubit = context.read<AccountCubit>();
    final newName = _nameController.text.trim();
    final newSuburb = _suburbController.text.trim();
    final newKin = _kinPhoneController.text.trim();

    cubit.updateProfile(
      displayName: newName.isNotEmpty ? newName : null,
      homeSuburb: newSuburb.isNotEmpty ? newSuburb : null,
      nextOfKinPhone: newKin.isNotEmpty ? newKin : null,
      isAvailable: current.role == 'WORKER' ? _isAvailable : null,
      travelKm: current.role == 'WORKER' ? _travelKm.toInt() : null,
    );
  }
}
