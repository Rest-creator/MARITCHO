import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/workers/data/models/worker_directory_item.dart';
import 'package:mobile/features/workers/data/repositories/workers_repository.dart';
import 'package:mobile/features/workers/presentation/cubit/workers_list_cubit.dart';
import 'package:mobile/features/workers/presentation/cubit/workers_list_state.dart';

class WorkersDirectoryPage extends StatelessWidget {
  const WorkersDirectoryPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) =>
          WorkersListCubit(ctx.read<WorkersRepository>())..loadWorkers(),
      child: const _WorkersDirectoryView(),
    );
  }
}

class _WorkersDirectoryView extends StatefulWidget {
  const _WorkersDirectoryView();

  @override
  State<_WorkersDirectoryView> createState() => _WorkersDirectoryViewState();
}

class _WorkersDirectoryViewState extends State<_WorkersDirectoryView> {
  final _searchController = TextEditingController();

  static const _popularTrades = [
    ('All', null),
    ('Plumber', 'PLUMBING'),
    ('Electrician', 'ELECTRICAL'),
    ('Solar', 'SOLAR'),
    ('Welder', 'WELDING'),
    ('Builder', 'BUILDING'),
  ];

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verified Workers')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search by skill, name or suburb...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          context.read<WorkersListCubit>().search('');
                        },
                      )
                    : null,
                contentPadding: const EdgeInsets.symmetric(vertical: 10),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onSubmitted: (query) {
                context.read<WorkersListCubit>().search(query.trim());
              },
            ),
          ),
          BlocBuilder<WorkersListCubit, WorkersListState>(
            builder: (context, state) {
              final activeTrade = state is WorkersListLoaded
                  ? state.selectedTrade
                  : null;

              return SizedBox(
                height: 48,
                child: ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  scrollDirection: Axis.horizontal,
                  itemCount: _popularTrades.length,
                  separatorBuilder: (context, index) =>
                      const SizedBox(width: 8),
                  itemBuilder: (context, index) {
                    final (label, trade) = _popularTrades[index];
                    final isSelected = activeTrade == trade;
                    return ChoiceChip(
                      label: Text(label),
                      selected: isSelected,
                      onSelected: (_) {
                        context.read<WorkersListCubit>().filterTrade(trade);
                      },
                    );
                  },
                ),
              );
            },
          ),
          const SizedBox(height: 8),
          Expanded(
            child: BlocBuilder<WorkersListCubit, WorkersListState>(
              builder: (context, state) {
                if (state is WorkersListLoading ||
                    state is WorkersListInitial) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is WorkersListFailure) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          'Could not load workers: ${state.errorMessage}',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: () =>
                              context.read<WorkersListCubit>().loadWorkers(),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  );
                }

                final workers = (state as WorkersListLoaded).workers;
                if (workers.isEmpty) {
                  return const Center(
                    child: Text('No verified workers found in this category.'),
                  );
                }

                return RefreshIndicator(
                  onRefresh: () =>
                      context.read<WorkersListCubit>().loadWorkers(),
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: workers.length,
                    separatorBuilder: (context, index) =>
                        const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      return _WorkerCard(worker: workers[index]);
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _WorkerCard extends StatelessWidget {
  final WorkerDirectoryItem worker;

  const _WorkerCard({required this.worker});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.5)),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(12),
        leading: CircleAvatar(
          backgroundColor: AppTheme.primaryBlueGray,
          child: Text(
            worker.name.isNotEmpty ? worker.name[0].toUpperCase() : 'W',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                worker.name,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: AppTheme.primaryBlueGray.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                worker.grade,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppTheme.primaryBlueGray,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              worker.trades.join(' · '),
              style: TextStyle(
                color: Colors.grey.shade800,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                if (worker.suburb != null) ...[
                  Icon(
                    Icons.location_on_outlined,
                    size: 14,
                    color: Colors.grey.shade600,
                  ),
                  const SizedBox(width: 2),
                  Text(
                    worker.suburb!,
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                  const SizedBox(width: 8),
                ],
                Icon(Icons.star, size: 14, color: Colors.amber.shade700),
                const SizedBox(width: 2),
                Text(
                  worker.ratingAverage != null
                      ? worker.ratingAverage!.toStringAsFixed(1)
                      : 'New',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  ' (${worker.jobsCompleted} done)',
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                ),
              ],
            ),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          Navigator.of(context)
              .pushNamed('/worker-public-profile', arguments: worker.id);
        },
      ),
    );
  }
}
