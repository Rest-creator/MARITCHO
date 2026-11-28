import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/theme/app_notification.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/screen_shell.dart';
import '../../data/models/open_job.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/job_detail_cubit.dart';
import '../cubit/job_detail_state.dart';

/// Design W3 · Job details (matching web JobDetailScreen).
/// Workers see the client's needs, distance, location, timing, and can either:
/// 1. Accept client's budget in one tap, OR
/// 2. Counter-offer with quick suggestions or custom amount, plus availability note.
class JobDetailPage extends StatefulWidget {
  final OpenJob job;

  const JobDetailPage({super.key, required this.job});

  @override
  State<JobDetailPage> createState() => _JobDetailPageState();
}

class _JobDetailPageState extends State<JobDetailPage> {
  final _priceController = TextEditingController();
  final _availabilityController = TextEditingController();
  bool _isCountering = false;

  @override
  void initState() {
    super.initState();
    if (widget.job.budgetAmount != null) {
      _priceController.text = widget.job.budgetAmount!.toStringAsFixed(0);
    }
  }

  @override
  void dispose() {
    _priceController.dispose();
    _availabilityController.dispose();
    super.dispose();
  }

  void _submit(BuildContext context, double amount) {
    final availability = _availabilityController.text.trim();
    context.read<JobDetailCubit>().submitOffer(
      jobId: widget.job.jobId,
      quotedAmount: amount,
      availabilityNote: availability.isEmpty ? null : availability,
    );
  }

  @override
  Widget build(BuildContext context) {
    final budget = widget.job.budgetAmount;
    final quickCounters = budget != null
        ? <int>{
            (budget * 0.9).round(),
            budget.round(),
            (budget * 1.15).round(),
            (budget * 1.3).round(),
          }.toList()
        : [20, 30, 45, 60];

    return BlocProvider(
      create: (ctx) => JobDetailCubit(ctx.read<JobsRepository>()),
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
            title: Text(
              widget.job.trade,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.share_outlined, color: Colors.white),
                onPressed: () {
                  AppNotification.show(
                    context,
                    message: 'Job link copied to clipboard',
                    type: NotificationType.info,
                  );
                },
              ),
            ],
          ),
          body: BlocConsumer<JobDetailCubit, JobDetailState>(
            listener: (context, state) {
              if (!mounted) return;
              if (state is JobDetailSuccess) {
                AppNotification.show(
                  context,
                  message: 'Your offer was sent to the client!',
                  type: NotificationType.success,
                );
                Navigator.of(context).pushReplacementNamed('/my-work');
              } else if (state is JobDetailFailure) {
                AppNotification.show(
                  context,
                  message: state.errorMessage,
                  type: NotificationType.error,
                );
              }
            },
            builder: (context, state) {
              final isSubmitting = state is JobDetailSubmitting;

              return ListView(
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 12,
                ),
                children: [
                  // Client Needs Header Card
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AppTheme.glass,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.line),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: AppTheme.cyanTintSoft,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: const Icon(
                                Icons.handyman_outlined,
                                color: AppTheme.cyanAccent,
                                size: 20,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    widget.job.trade,
                                    style: const TextStyle(
                                      fontSize: 17,
                                      fontWeight: FontWeight.w800,
                                      color: Colors.white,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    '${widget.job.suburb} • ${widget.job.distanceKm.toStringAsFixed(1)} km away',
                                    style: const TextStyle(
                                      fontSize: 13,
                                      color: AppTheme.textSecondary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        const Divider(color: AppTheme.line, height: 1),
                        const SizedBox(height: 14),
                        const Text(
                          'Problem description',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.textMuted,
                            letterSpacing: 0.5,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          widget.job.problemDescription ??
                              'No description provided.',
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.white,
                            height: 1.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),

                  // Client's Budget Hero Card
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          AppTheme.cyanAccent.withValues(alpha: 0.15),
                          AppTheme.brandRoyal.withValues(alpha: 0.25),
                        ],
                      ),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: AppTheme.cyanAccent.withValues(alpha: 0.3),
                      ),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "Client's budget",
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                            SizedBox(height: 4),
                            Text(
                              'Can accept or offer different',
                              style: TextStyle(
                                fontSize: 11,
                                color: AppTheme.textMuted,
                              ),
                            ),
                          ],
                        ),
                        Text(
                          budget != null
                              ? 'US\$ ${budget.toStringAsFixed(0)}'
                              : 'Open quote',
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w800,
                            color: AppTheme.cyanAccent,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Send Offer Section
                  const Text(
                    'Your offer',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Accept Client Price Button (1-tap like inDrive)
                  if (budget != null && !_isCountering) ...[
                    SizedBox(
                      height: 52,
                      child: ElevatedButton(
                        onPressed: isSubmitting
                            ? null
                            : () => _submit(context, budget),
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
                            : Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  const Icon(Icons.check, size: 20),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Accept US\$ ${budget.toStringAsFixed(0)}',
                                    style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ],
                              ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Center(
                      child: TextButton(
                        onPressed: isSubmitting
                            ? null
                            : () => setState(() => _isCountering = true),
                        child: const Text(
                          'Offer a different price',
                          style: TextStyle(
                            color: AppTheme.cyanAccent,
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                      ),
                    ),
                  ] else ...[
                    // Custom Counter-Offer Form
                    Container(
                      decoration: BoxDecoration(
                        color: AppTheme.glass,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppTheme.line),
                      ),
                      child: TextField(
                        controller: _priceController,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        enabled: !isSubmitting,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                        ),
                        decoration: const InputDecoration(
                          prefixText: 'US\$ ',
                          prefixStyle: TextStyle(
                            color: AppTheme.cyanAccent,
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                          ),
                          hintText: '0',
                          hintStyle: TextStyle(color: AppTheme.textMuted),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 14,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Quick Chips for Countering
                    Wrap(
                      spacing: 8,
                      children: quickCounters.map((val) {
                        return ActionChip(
                          label: Text('US\$ $val'),
                          backgroundColor: AppTheme.glass,
                          labelStyle: const TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 13,
                          ),
                          side: const BorderSide(color: AppTheme.line),
                          onPressed: isSubmitting
                              ? null
                              : () => setState(
                                  () => _priceController.text = val.toString(),
                                ),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),

                    // Availability note
                    Container(
                      decoration: BoxDecoration(
                        color: AppTheme.glass,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppTheme.line),
                      ),
                      child: TextField(
                        controller: _availabilityController,
                        enabled: !isSubmitting,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                        ),
                        decoration: const InputDecoration(
                          hintText: 'When can you come? (e.g. Can be there in 45 mins)',
                          hintStyle: TextStyle(
                            color: AppTheme.textMuted,
                            fontSize: 13,
                          ),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 14,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    SizedBox(
                      height: 52,
                      child: ElevatedButton(
                        onPressed: isSubmitting
                            ? null
                            : () {
                                final amount = double.tryParse(
                                  _priceController.text.trim(),
                                );
                                if (amount == null || amount <= 0) {
                                  AppNotification.show(
                                    context,
                                    message:
                                        'Enter a valid price for your offer',
                                    type: NotificationType.warning,
                                  );
                                  return;
                                }
                                _submit(context, amount);
                              },
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
                                'Send my offer',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 30),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}
