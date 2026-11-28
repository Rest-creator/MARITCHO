import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../../core/theme/app_notification.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/screen_shell.dart';
import '../../../suburbs/data/models/suburb.dart';
import '../../../suburbs/data/repositories/suburbs_repository.dart';
import '../../data/repositories/workers_repository.dart';
import '../cubit/worker_skills_cubit.dart';
import '../cubit/worker_skills_state.dart';

const _trades = [
  ('Plumber', 'PLUMBING'),
  ('Electrician', 'ELECTRICAL'),
  ('Solar', 'SOLAR'),
  ('Welder', 'WELDING'),
  ('Builder', 'BUILDING'),
  ('Appliance repair', 'APPLIANCE_REPAIR'),
  ('Painter', 'PAINTING'),
  ('Carpenter', 'CARPENTRY'),
  ('Tiler', 'TILING'),
  ('Landscaping', 'LANDSCAPING'),
];

const _maxTrades = 5;

/// Design W1: Step 2 of 2 · Worker Skills and Service Area Setup.
/// Replicates the web visual layout, progress bar, trade chips, search/add,
/// travel distance slider, and suburb selector with full theme parity.
class WorkerSkillsPage extends StatefulWidget {
  const WorkerSkillsPage({super.key});

  @override
  State<WorkerSkillsPage> createState() => _WorkerSkillsPageState();
}

class _WorkerSkillsPageState extends State<WorkerSkillsPage> {
  late final Future<Result<List<Suburb>, Failure>> _suburbsFuture;
  final _selectedTrades = <String>{};
  String? _suburb;
  double _travelKm = 15.0;
  bool _isSearchingSkill = false;
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _suburbsFuture = context.read<SuburbsRepository>().listSuburbs();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _toggleTrade(String tradeValue) {
    setState(() {
      if (_selectedTrades.contains(tradeValue)) {
        _selectedTrades.remove(tradeValue);
      } else {
        if (_selectedTrades.length < _maxTrades) {
          _selectedTrades.add(tradeValue);
        } else {
          AppNotification.show(
            context,
            message: "That's $_maxTrades skills — the most you can add",
            type: NotificationType.warning,
          );
        }
      }
    });
  }

  void _submit(BuildContext context) {
    if (_selectedTrades.isEmpty) {
      AppNotification.show(
        context,
        message: 'Pick at least one kind of work you can do.',
        type: NotificationType.error,
      );
      return;
    }
    if (_suburb == null || _suburb!.isEmpty) {
      AppNotification.show(
        context,
        message: "Choose where you're based so we can show jobs nearby.",
        type: NotificationType.error,
      );
      return;
    }

    context.read<WorkerSkillsCubit>().submit(
      trades: _selectedTrades.toList(),
      suburb: _suburb!,
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => WorkerSkillsCubit(ctx.read<WorkersRepository>()),
      child: ScreenShell(
        child: Scaffold(
          backgroundColor: Colors.transparent,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back, color: Colors.white),
              onPressed: () => Navigator.of(context).maybePop(),
            ),
            actions: [
              Padding(
                padding: const EdgeInsets.only(right: 20),
                child: Center(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppTheme.glass,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.line),
                    ),
                    child: const Text(
                      'Step 2 of 2',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.cyanAccent,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
          body: BlocConsumer<WorkerSkillsCubit, WorkerSkillsState>(
            listener: (context, state) {
              if (!mounted) return;
              if (state is WorkerSkillsSuccess) {
                AppNotification.show(
                  context,
                  message: 'Profile and skills updated successfully!',
                  type: NotificationType.success,
                );
                Navigator.of(context).pushReplacementNamed('/worker-home');
              } else if (state is WorkerSkillsFailure) {
                AppNotification.show(
                  context,
                  message: state.errorMessage,
                  type: NotificationType.error,
                );
              }
            },
            builder: (context, state) {
              final isSubmitting = state is WorkerSkillsSubmitting;

              return FutureBuilder<Result<List<Suburb>, Failure>>(
                future: _suburbsFuture,
                builder: (context, snapshot) {
                  final suburbs = snapshot.data?.okValue ?? [];

                  return ListView(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 8,
                    ),
                    children: [
                      // Progress Bar
                      ClipRRect(
                        borderRadius: BorderRadius.circular(2),
                        child: Container(
                          height: 4,
                          color: AppTheme.glass,
                          child: FractionallySizedBox(
                            alignment: Alignment.centerLeft,
                            widthFactor: 1.0,
                            child: Container(color: AppTheme.cyanAccent),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Title & Subtitle
                      const Text(
                        'What work can you do?',
                        style: TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                          letterSpacing: -0.5,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Pick up to $_maxTrades. Here, what you can do matters more than certificates.',
                        style: TextStyle(
                          fontSize: 14,
                          color: AppTheme.textSecondary,
                          height: 1.5,
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Selected Skills Chips
                      if (_selectedTrades.isNotEmpty) ...[
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: _selectedTrades.map((tradeValue) {
                            final match = _trades.firstWhere(
                              (t) => t.$2 == tradeValue,
                              orElse: () => (tradeValue, tradeValue),
                            );
                            return Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 8,
                              ),
                              decoration: BoxDecoration(
                                color: AppTheme.cyanTintSoft,
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: AppTheme.cyanEdge),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(
                                    Icons.check_circle_rounded,
                                    size: 16,
                                    color: AppTheme.cyanAccent,
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    match.$1,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w600,
                                      fontSize: 13,
                                    ),
                                  ),
                                  const SizedBox(width: 4),
                                  GestureDetector(
                                    onTap: isSubmitting
                                        ? null
                                        : () => _toggleTrade(tradeValue),
                                    child: const Icon(
                                      Icons.close,
                                      size: 14,
                                      color: AppTheme.textSecondary,
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        ),
                        const SizedBox(height: 14),
                      ],

                      // Add a skill / Search Box
                      if (!_isSearchingSkill)
                        OutlinedButton.icon(
                          onPressed:
                              _selectedTrades.length >= _maxTrades ||
                                  isSubmitting
                              ? null
                              : () => setState(() => _isSearchingSkill = true),
                          style: OutlinedButton.styleFrom(
                            side: const BorderSide(color: AppTheme.line),
                            backgroundColor: AppTheme.glass,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          icon: const Icon(
                            Icons.add,
                            size: 18,
                            color: AppTheme.cyanAccent,
                          ),
                          label: Text(
                            _selectedTrades.length >= _maxTrades
                                ? "That's $_maxTrades skills — the most you can add"
                                : 'Add a skill',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        )
                      else ...[
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          decoration: BoxDecoration(
                            color: AppTheme.colorBgRaised,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.cyanAccent),
                          ),
                          child: TextField(
                            controller: _searchController,
                            autofocus: true,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                            ),
                            onChanged: (_) => setState(() {}),
                            decoration: InputDecoration(
                              icon: const Icon(
                                Icons.search,
                                color: AppTheme.cyanAccent,
                                size: 20,
                              ),
                              hintText: 'Type what you do, e.g. I fix geysers',
                              hintStyle: const TextStyle(
                                color: AppTheme.textMuted,
                              ),
                              border: InputBorder.none,
                              suffixIcon: IconButton(
                                icon: const Icon(
                                  Icons.close,
                                  color: AppTheme.textMuted,
                                  size: 18,
                                ),
                                onPressed: () {
                                  setState(() {
                                    _searchController.clear();
                                    _isSearchingSkill = false;
                                  });
                                },
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: _trades
                              .where(
                                (t) =>
                                    !_selectedTrades.contains(t.$2) &&
                                    (_searchController.text.isEmpty ||
                                        t.$1.toLowerCase().contains(
                                          _searchController.text.toLowerCase(),
                                        )),
                              )
                              .map((trade) {
                                return ActionChip(
                                  avatar: const Icon(
                                    Icons.add,
                                    size: 14,
                                    color: AppTheme.cyanAccent,
                                  ),
                                  label: Text(trade.$1),
                                  backgroundColor: AppTheme.glass,
                                  labelStyle: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 13,
                                  ),
                                  side: const BorderSide(color: AppTheme.line),
                                  onPressed: () {
                                    _toggleTrade(trade.$2);
                                    setState(() {
                                      _searchController.clear();
                                    });
                                  },
                                );
                              })
                              .toList(),
                        ),
                      ],
                      const SizedBox(height: 24),

                      // Card: Travel Range & Suburb
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppTheme.glass,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: AppTheme.line),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'How far can you travel?',
                                  style: TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w700,
                                    color: Colors.white,
                                  ),
                                ),
                                Text(
                                  '${_travelKm.toInt()} km',
                                  style: const TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w700,
                                    color: AppTheme.cyanAccent,
                                  ),
                                ),
                              ],
                            ),
                            SliderTheme(
                              data: SliderTheme.of(context).copyWith(
                                activeTrackColor: AppTheme.cyanAccent,
                                inactiveTrackColor: Colors.white12,
                                thumbColor: AppTheme.cyanAccent,
                                overlayColor: AppTheme.cyanAccent.withValues(
                                  alpha: 0.2,
                                ),
                              ),
                              child: Slider(
                                value: _travelKm,
                                min: 2,
                                max: 50,
                                divisions: 48,
                                onChanged: isSubmitting
                                    ? null
                                    : (val) => setState(() => _travelKm = val),
                              ),
                            ),
                            const Divider(color: AppTheme.line, height: 24),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'From',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.textSecondary,
                                  ),
                                ),
                                TextButton.icon(
                                  onPressed: isSubmitting
                                      ? null
                                      : () {
                                          if (suburbs.isNotEmpty) {
                                            setState(
                                              () =>
                                                  _suburb = suburbs.first.name,
                                            );
                                            AppNotification.show(
                                              context,
                                              message:
                                                  'Set nearest suburb to ${suburbs.first.name}',
                                              type: NotificationType.info,
                                            );
                                          }
                                        },
                                  icon: const Icon(
                                    Icons.my_location,
                                    size: 14,
                                    color: AppTheme.cyanAccent,
                                  ),
                                  label: const Text(
                                    'Use my location',
                                    style: TextStyle(
                                      fontSize: 13,
                                      color: AppTheme.cyanAccent,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            DropdownButtonFormField<String>(
                              initialValue: _suburb,
                              dropdownColor: AppTheme.colorBgRaised,
                              decoration: InputDecoration(
                                hintText: suburbs.isEmpty
                                    ? 'Loading suburbs...'
                                    : 'Choose your suburb',
                                hintStyle: const TextStyle(
                                  color: AppTheme.textMuted,
                                ),
                                filled: true,
                                fillColor: AppTheme.glass,
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  borderSide: const BorderSide(
                                    color: AppTheme.line,
                                  ),
                                ),
                                enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  borderSide: const BorderSide(
                                    color: AppTheme.line,
                                  ),
                                ),
                                focusedBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  borderSide: const BorderSide(
                                    color: AppTheme.cyanAccent,
                                  ),
                                ),
                              ),
                              items: suburbs
                                  .map(
                                    (s) => DropdownMenuItem(
                                      value: s.name,
                                      child: Text(
                                        s.name,
                                        style: const TextStyle(
                                          color: Colors.white,
                                        ),
                                      ),
                                    ),
                                  )
                                  .toList(),
                              onChanged: isSubmitting
                                  ? null
                                  : (val) => setState(() => _suburb = val),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 28),

                      // Submit Button
                      SizedBox(
                        height: 52,
                        child: ElevatedButton(
                          onPressed: isSubmitting
                              ? null
                              : () => _submit(context),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.cyanAccent,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                            elevation: 4,
                          ),
                          child: isSubmitting
                              ? const SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2.5,
                                    color: Colors.white,
                                  ),
                                )
                              : const Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      'Start finding work',
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                    SizedBox(width: 8),
                                    Icon(Icons.arrow_forward, size: 18),
                                  ],
                                ),
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],
                  );
                },
              );
            },
          ),
        ),
      ),
    );
  }
}
