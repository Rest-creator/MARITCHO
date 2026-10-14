import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:path_provider/path_provider.dart';

import 'core/navigation/app_router.dart';
import 'core/network/api_client.dart';
import 'core/storage/database_helper.dart';
import 'core/storage/token_storage.dart';
import 'core/sync/sqlite_outbox.dart';
import 'core/sync/sync_scheduler.dart';
import 'core/sync/sync_service.dart';
import 'core/theme/app_theme.dart';
import 'features/accounts/data/repositories/auth_repository.dart';
import 'features/jobs/data/repositories/job_work_repository.dart';
import 'features/jobs/data/repositories/jobs_repository.dart';
import 'features/suburbs/data/repositories/suburbs_repository.dart';
import 'features/workers/data/repositories/workers_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  final tokenStorage = TokenStorage();
  final dbHelper = DatabaseHelper();
  final dio = buildApiDio(tokenStorage);
  final authRepository = AuthRepository(dio, tokenStorage);
  final jobsRepository = JobsRepository(dio, dbHelper);
  final suburbsRepository = SuburbsRepository(dio);
  final workersRepository = WorkersRepository(dio, dbHelper);

  // Offline work (on-site price, photos) is saved first and sent when
  // there's signal; the scheduler decides when (APP-002).
  final outbox = SqliteOutbox(dbHelper);
  final syncService = SyncService(outbox, dio);
  final syncScheduler = SyncScheduler(syncService);
  final jobWorkRepository = JobWorkRepository(
    outbox,
    onQueued: syncScheduler.nudge,
    photoDirectory: () async => Directory(
      '${(await getApplicationDocumentsDirectory()).path}/outbox_photos',
    ),
  );
  syncScheduler.start();

  runApp(
    MyApp(
      authRepository: authRepository,
      jobsRepository: jobsRepository,
      suburbsRepository: suburbsRepository,
      workersRepository: workersRepository,
      jobWorkRepository: jobWorkRepository,
      syncService: syncService,
    ),
  );
}

class MyApp extends StatelessWidget {
  final AuthRepository authRepository;
  final JobsRepository jobsRepository;
  final SuburbsRepository suburbsRepository;
  final WorkersRepository workersRepository;
  final JobWorkRepository jobWorkRepository;
  final SyncService syncService;

  const MyApp({
    super.key,
    required this.authRepository,
    required this.jobsRepository,
    required this.suburbsRepository,
    required this.workersRepository,
    required this.jobWorkRepository,
    required this.syncService,
  });

  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider<AuthRepository>.value(value: authRepository),
        RepositoryProvider<JobsRepository>.value(value: jobsRepository),
        RepositoryProvider<SuburbsRepository>.value(value: suburbsRepository),
        RepositoryProvider<WorkersRepository>.value(value: workersRepository),
        RepositoryProvider<JobWorkRepository>.value(value: jobWorkRepository),
        RepositoryProvider<SyncService>.value(value: syncService),
      ],
      child: MaterialApp(
        title: 'Maricho',
        theme: AppTheme.lightTheme,
        initialRoute: '/',
        onGenerateRoute: onGenerateRoute,
      ),
    );
  }
}
