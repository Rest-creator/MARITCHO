import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../../core/theme/app_notification.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/screen_shell.dart';
import '../../../suburbs/data/models/suburb.dart';
import '../../../suburbs/data/repositories/suburbs_repository.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/post_job_cubit.dart';
import '../cubit/post_job_state.dart';

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

enum _PricingMode { fixed, negotiable, afterVisit }

enum _TimingOption { today, thisWeek }

/// Replicates the web PostJobScreen (Design 2 · Post a Job) with full visual parity:
/// - Trade selection chips
/// - Timing selector (Today, This week, Specific date)
/// - Suburb selection with "Use my location"
/// - Pricing mode cards (Fixed price, Negotiable, Price after visit)
/// - Budget input with quick-suggest chips
/// - Character countdown and floating notifications
class PostJobPage extends StatefulWidget {
  final String? initialTrade;

  const PostJobPage({super.key, this.initialTrade});

  @override
  State<PostJobPage> createState() => _PostJobPageState();
}

class _PostJobPageState extends State<PostJobPage> {
  late final Future<Result<List<Suburb>, Failure>> _suburbsFuture;
  final _addressController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _budgetController = TextEditingController();

  String? _trade;
  String? _suburb;
  _PricingMode _pricingMode = _PricingMode.negotiable;
  _TimingOption _timing = _TimingOption.today;

  @override
  void initState() {
    super.initState();
    _trade = widget.initialTrade;
    _suburbsFuture = context.read<SuburbsRepository>().listSuburbs();
  }

  @override
  void dispose() {
    _addressController.dispose();
    _descriptionController.dispose();
    _budgetController.dispose();
    super.dispose();
  }

  void _submit(BuildContext context) {
    if (_trade == null) {
      AppNotification.show(
        context,
        message: 'Pick what kind of work you need done',
        type: NotificationType.warning,
      );
      return;
    }
    if (_suburb == null || _suburb!.isEmpty) {
      AppNotification.show(
        context,
        message: 'Choose which suburb the job is in',
        type: NotificationType.warning,
      );
      return;
    }
    if (_descriptionController.text.trim().isEmpty) {
      AppNotification.show(
        context,
        message: 'Please describe the problem so workers know what to bring',
        type: NotificationType.warning,
      );
      return;
    }

    final budgetText = _budgetController.text.trim();
    final budgetAmount = _pricingMode == _PricingMode.afterVisit
        ? null
        : (budgetText.isEmpty ? null : double.tryParse(budgetText));

    final timingPrefix = _timing == _TimingOption.today
        ? '[Today] '
        : '[This week] ';
    final fullDescription =
        '$timingPrefix${_descriptionController.text.trim()}';

    final address = _addressController.text.trim().isEmpty
        ? 'Near $_suburb center'
        : _addressController.text.trim();

    context.read<PostJobCubit>().submit(
      trade: _trade!,
      suburb: _suburb!,
      address: address,
      problemDescription: fullDescription,
      budgetAmount: budgetAmount,
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => PostJobCubit(ctx.read<JobsRepository>()),
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
            title: const Text(
              'Post a job',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),
          ),
          body: BlocConsumer<PostJobCubit, PostJobState>(
            listener: (context, state) {
              if (!mounted) return;
              if (state is PostJobSuccess) {
                AppNotification.show(
                  context,
                  message: 'Job posted! Workers nearby are being notified.',
                  type: NotificationType.success,
                );
                Navigator.of(
                  context,
                ).pushReplacementNamed('/applicants', arguments: state.job.id);
              } else if (state is PostJobFailure) {
                AppNotification.show(
                  context,
                  message: state.errorMessage,
                  type: NotificationType.error,
                );
              }
            },
            builder: (context, state) {
              final isSubmitting = state is PostJobSubmitting;

              return FutureBuilder<Result<List<Suburb>, Failure>>(
                future: _suburbsFuture,
                builder: (context, snapshot) {
                  final suburbs = snapshot.data?.okValue ?? [];

                  return ListView(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 12,
                    ),
                    children: [
                      // Section: Trade Selection
                      const Text(
                        'What needs to be done?',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: _trades.map((t) {
                          final isSelected = _trade == t.$2;
                          return ChoiceChip(
                            label: Text(t.$1),
                            selected: isSelected,
                            onSelected: isSubmitting
                                ? null
                                : (selected) {
                                    setState(
                                      () => _trade = selected ? t.$2 : null,
                                    );
                                  },
                            backgroundColor: AppTheme.glass,
                            selectedColor: AppTheme.cyanAccent.withValues(
                              alpha: 0.25,
                            ),
                            labelStyle: TextStyle(
                              color: isSelected
                                  ? Colors.white
                                  : AppTheme.textSecondary,
                              fontWeight: isSelected
                                  ? FontWeight.w700
                                  : FontWeight.w500,
                              fontSize: 13,
                            ),
                            side: BorderSide(
                              color: isSelected
                                  ? AppTheme.cyanAccent
                                  : AppTheme.line,
                            ),
                          );
                        }).toList(),
                      ),
                      const SizedBox(height: 24),

                      // Section: Timing
                      const Text(
                        'When do you need it done?',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTimingPill(
                              label: 'Today',
                              selected: _timing == _TimingOption.today,
                              onTap: isSubmitting
                                  ? null
                                  : () => setState(
                                      () => _timing = _TimingOption.today,
                                    ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _buildTimingPill(
                              label: 'This week',
                              selected: _timing == _TimingOption.thisWeek,
                              onTap: isSubmitting
                                  ? null
                                  : () => setState(
                                      () => _timing = _TimingOption.thisWeek,
                                    ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // Section: Description
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Describe the problem',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: Colors.white,
                            ),
                          ),
                          Text(
                            '${_descriptionController.text.length}/300',
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppTheme.textMuted,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Container(
                        decoration: BoxDecoration(
                          color: AppTheme.glass,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppTheme.line),
                        ),
                        child: TextField(
                          controller: _descriptionController,
                          maxLength: 300,
                          maxLines: 4,
                          enabled: !isSubmitting,
                          onChanged: (_) => setState(() {}),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                          ),
                          decoration: const InputDecoration(
                            hintText: 'e.g. Geyser is leaking from the pressure valve, dripping onto the ceiling',
                            hintStyle: TextStyle(
                              color: AppTheme.textMuted,
                              fontSize: 13,
                            ),
                            contentPadding: EdgeInsets.all(14),
                            border: InputBorder.none,
                            counterText: '',
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Section: Location & Suburb
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
                                  'Job Location',
                                  style: TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w700,
                                    color: Colors.white,
                                  ),
                                ),
                                TextButton.icon(
                                  onPressed: isSubmitting || suburbs.isEmpty
                                      ? null
                                      : () {
                                          setState(
                                            () => _suburb = suburbs.first.name,
                                          );
                                          AppNotification.show(
                                            context,
                                            message:
                                                'Selected ${suburbs.first.name}',
                                            type: NotificationType.info,
                                          );
                                        },
                                  icon: const Icon(
                                    Icons.my_location,
                                    size: 14,
                                    color: AppTheme.cyanAccent,
                                  ),
                                  label: const Text(
                                    'Use current',
                                    style: TextStyle(
                                      fontSize: 13,
                                      color: AppTheme.cyanAccent,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            DropdownButtonFormField<String>(
                              initialValue: _suburb,
                              dropdownColor: AppTheme.colorBgRaised,
                              decoration: InputDecoration(
                                hintText: suburbs.isEmpty
                                    ? 'Loading suburbs...'
                                    : 'Choose suburb',
                                hintStyle: const TextStyle(
                                  color: AppTheme.textMuted,
                                ),
                                filled: true,
                                fillColor: AppTheme.colorBgRaised.withValues(
                                  alpha: 0.5,
                                ),
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
                            const SizedBox(height: 12),
                            TextField(
                              controller: _addressController,
                              enabled: !isSubmitting,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                              ),
                              decoration: InputDecoration(
                                hintText:
                                    'Street address or landmark (optional)',
                                hintStyle: const TextStyle(
                                  color: AppTheme.textMuted,
                                  fontSize: 13,
                                ),
                                filled: true,
                                fillColor: AppTheme.colorBgRaised.withValues(
                                  alpha: 0.5,
                                ),
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
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Section: Pricing Mode
                      const Text(
                        'Pricing approach',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 10),
                      _buildPricingOption(
                        mode: _PricingMode.negotiable,
                        title: 'Negotiable price',
                        subtitle: 'Suggest a budget. Workers can accept it or counter-offer.',
                      ),
                      const SizedBox(height: 8),
                      _buildPricingOption(
                        mode: _PricingMode.fixed,
                        title: 'Fixed price',
                        subtitle: 'Set an exact price. First matching worker can take it immediately.',
                      ),
                      const SizedBox(height: 8),
                      _buildPricingOption(
                        mode: _PricingMode.afterVisit,
                        title: 'Price after visit',
                        subtitle: 'Workers come inspect on site before agreeing on a final price.',
                      ),
                      const SizedBox(height: 16),

                      // Budget Input (only for negotiable/fixed)
                      if (_pricingMode != _PricingMode.afterVisit) ...[
                        Row(
                          children: [
                            Expanded(
                              child: Container(
                                decoration: BoxDecoration(
                                  color: AppTheme.glass,
                                  borderRadius: BorderRadius.circular(14),
                                  border: Border.all(color: AppTheme.line),
                                ),
                                child: TextField(
                                  controller: _budgetController,
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                      ),
                                  enabled: !isSubmitting,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 18,
                                    fontWeight: FontWeight.w700,
                                  ),
                                  decoration: const InputDecoration(
                                    prefixText: 'US\$ ',
                                    prefixStyle: TextStyle(
                                      color: AppTheme.cyanAccent,
                                      fontSize: 18,
                                      fontWeight: FontWeight.w700,
                                    ),
                                    hintText: 'e.g. 25',
                                    hintStyle: TextStyle(
                                      color: AppTheme.textMuted,
                                      fontSize: 16,
                                    ),
                                    border: InputBorder.none,
                                    contentPadding: EdgeInsets.symmetric(
                                      horizontal: 16,
                                      vertical: 12,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 8,
                          children: ['15', '25', '40', '60'].map((amount) {
                            return ActionChip(
                              label: Text('US\$ $amount'),
                              backgroundColor: AppTheme.glass,
                              labelStyle: const TextStyle(
                                color: AppTheme.textSecondary,
                                fontSize: 12,
                              ),
                              side: const BorderSide(color: AppTheme.line),
                              onPressed: isSubmitting
                                  ? null
                                  : () => setState(
                                      () => _budgetController.text = amount,
                                    ),
                            );
                          }).toList(),
                        ),
                      ],
                      const SizedBox(height: 32),

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
                              : const Text(
                                  'Find someone for this job',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                        ),
                      ),
                      const SizedBox(height: 30),
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

  Widget _buildTimingPill({
    required String label,
    required bool selected,
    required VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: selected
              ? AppTheme.cyanAccent.withValues(alpha: 0.2)
              : AppTheme.glass,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? AppTheme.cyanAccent : AppTheme.line,
            width: selected ? 1.5 : 1.0,
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: selected ? Colors.white : AppTheme.textSecondary,
              fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
              fontSize: 14,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPricingOption({
    required _PricingMode mode,
    required String title,
    required String subtitle,
  }) {
    final isSelected = _pricingMode == mode;
    return GestureDetector(
      onTap: () => setState(() => _pricingMode = mode),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isSelected
              ? AppTheme.cyanAccent.withValues(alpha: 0.15)
              : AppTheme.glass,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isSelected ? AppTheme.cyanAccent : AppTheme.line,
            width: isSelected ? 1.5 : 1.0,
          ),
        ),
        child: Row(
          children: [
            Icon(
              isSelected ? Icons.radio_button_checked : Icons.radio_button_off,
              color: isSelected ? AppTheme.cyanAccent : AppTheme.textMuted,
              size: 20,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: isSelected
                          ? FontWeight.w700
                          : FontWeight.w600,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 12,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
