import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';

import 'package:mobile/core/sync/sync_service.dart';
import 'package:mobile/features/jobs/data/models/job.dart';
import 'package:mobile/features/jobs/data/models/my_offer.dart';
import 'package:mobile/features/jobs/data/repositories/job_work_repository.dart';
import 'package:mobile/features/workers/data/repositories/work_screen_repository.dart';
import 'package:mobile/features/workers/presentation/cubit/my_work_cubit.dart';
import 'package:mobile/features/workers/presentation/cubit/my_work_state.dart';
import 'package:mobile/features/workers/presentation/widgets/active_job_card.dart';
import 'package:mobile/features/workers/presentation/widgets/quote_input.dart';
import 'package:mobile/features/workers/presentation/widgets/quote_sheet.dart';

/// Ports MyWork.dc.html. The stats header shows Jobs completed and
/// On-time rate (from GET /workers/me/standing) instead of the
/// wireframe's "$Earned"/star rating — no earnings-aggregate endpoint
/// and no numeric rating exist anywhere in the backend; not faked here.
class MyWorkPage extends StatelessWidget {
  const MyWorkPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (BuildContext ctx) => MyWorkCubit(
        ctx.read<WorkScreenRepository>(),
        ctx.read<JobWorkRepository>(),
        syncChanges: ctx.read<SyncService>().changes,
      )..load(),
      child: const _MyWorkView(),
    );
  }
}

class _MyWorkView extends StatelessWidget {
  const _MyWorkView();

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('My work'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Offers'),
              Tab(text: 'Active'),
              Tab(text: 'Done'),
            ],
          ),
        ),
        body: BlocConsumer<MyWorkCubit, MyWorkState>(
          listenWhen: (MyWorkState previous, MyWorkState current) =>
              current is MyWorkLoaded && current.notice != null,
          listener: (BuildContext context, MyWorkState state) {
            final String? notice = (state as MyWorkLoaded).notice;
            if (notice == null) return;
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(notice)));
            context.read<MyWorkCubit>().clearNotice();
          },
          builder: (BuildContext context, MyWorkState state) {
            if (state is MyWorkInitial || state is MyWorkLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            if (state is MyWorkFailure) {
              return Center(
                child: Text('Could not load your work: ${state.errorMessage}'),
              );
            }

            final loaded = state as MyWorkLoaded;
            return Column(
              children: [
                _StatsRow(loaded: loaded),
                Expanded(
                  child: TabBarView(
                    children: [
                      _OffersTab(offers: loaded.offers),
                      _ActiveTab(loaded: loaded),
                      _JobsTab(
                        jobs: loaded.doneJobs,
                        emptyText: 'No completed jobs yet.',
                      ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _StatsRow extends StatelessWidget {
  final MyWorkLoaded loaded;

  const _StatsRow({required this.loaded});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _Stat(
            value: '${loaded.standing.jobsCompleted}',
            label: 'Jobs completed',
          ),
          _Stat(
            value: '${loaded.standing.onTimeRate.toStringAsFixed(0)}%',
            label: 'On-time rate',
          ),
          _Stat(value: loaded.standing.grade, label: 'Grade'),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String value;
  final String label;

  const _Stat({required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      ],
    );
  }
}

class _OffersTab extends StatelessWidget {
  final List<MyOffer> offers;

  const _OffersTab({required this.offers});

  @override
  Widget build(BuildContext context) {
    if (offers.isEmpty) {
      return const Center(child: Text('No offers submitted yet.'));
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final offer in offers)
          Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              title: Text(offer.jobTrade),
              subtitle: Text('${offer.jobSuburb} · ${offer.jobStatus}'),
              trailing: Text('\$${offer.quotedAmount.toStringAsFixed(2)}'),
            ),
          ),
      ],
    );
  }
}

/// Hired jobs: arrive and confirm the price, add photos — all of it
/// saved on the phone first, so it works without signal.
class _ActiveTab extends StatelessWidget {
  final MyWorkLoaded loaded;

  const _ActiveTab({required this.loaded});

  Future<void> _arrive(BuildContext context, Job job) async {
    final MyWorkCubit cubit = context.read<MyWorkCubit>();
    final QuoteInput? input = await showModalBottomSheet<QuoteInput>(
      context: context,
      isScrollControlled: true,
      builder: (BuildContext _) =>
          QuoteSheet(offeredAmount: loaded.offeredAmountFor(job.id)),
    );
    if (input == null) return;
    await cubit.submitQuote(
      jobId: job.id,
      laborAmount: input.laborAmount,
      materialsAmount: input.materialsAmount,
    );
  }

  Future<void> _addPhoto(BuildContext context, Job job) async {
    final MyWorkCubit cubit = context.read<MyWorkCubit>();
    final XFile? photo;
    try {
      // Shrunk by the camera plugin itself: small enough for a data bundle.
      photo = await ImagePicker().pickImage(
        source: ImageSource.camera,
        maxWidth: 1280,
        maxHeight: 1280,
        imageQuality: 70,
      );
    } on Exception {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'The camera is not available. Allow it in your phone settings.',
          ),
        ),
      );
      return;
    }
    if (photo == null) return;
    await cubit.addPhoto(jobId: job.id, filePath: photo.path);
  }

  @override
  Widget build(BuildContext context) {
    final List<Job> jobs = loaded.activeJobs;
    if (jobs.isEmpty) {
      return const Center(
        child: Text('No active jobs. When a client hires you, it shows here.'),
      );
    }
    return RefreshIndicator(
      onRefresh: () => context.read<MyWorkCubit>().refresh(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          for (final Job job in jobs)
            ActiveJobCard(
              job: job,
              undelivered: loaded.undeliveredFor(job.id),
              onArrived: () => _arrive(context, job),
              onAddPhoto: () => _addPhoto(context, job),
              onRetry: (int id) => context.read<MyWorkCubit>().retry(id),
            ),
        ],
      ),
    );
  }
}

class _JobsTab extends StatelessWidget {
  final List<Job> jobs;
  final String emptyText;

  const _JobsTab({required this.jobs, required this.emptyText});

  @override
  Widget build(BuildContext context) {
    if (jobs.isEmpty) {
      return Center(child: Text(emptyText));
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final job in jobs)
          Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              title: Text(job.trade),
              subtitle: Text('${job.suburb} · ${job.status}'),
            ),
          ),
      ],
    );
  }
}
