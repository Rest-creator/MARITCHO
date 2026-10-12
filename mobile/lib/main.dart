import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'core/navigation/app_router.dart';
import 'core/network/api_client.dart';
import 'core/storage/database_helper.dart';
import 'core/storage/token_storage.dart';
import 'core/theme/app_theme.dart';
import 'features/accounts/data/repositories/auth_repository.dart';
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

  runApp(
    MyApp(
      authRepository: authRepository,
      jobsRepository: jobsRepository,
      suburbsRepository: suburbsRepository,
      workersRepository: workersRepository,
    ),
  );
}

class MyApp extends StatelessWidget {
  final AuthRepository authRepository;
  final JobsRepository jobsRepository;
  final SuburbsRepository suburbsRepository;
  final WorkersRepository workersRepository;

  const MyApp({
    super.key,
    required this.authRepository,
    required this.jobsRepository,
    required this.suburbsRepository,
    required this.workersRepository,
  });

  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider<AuthRepository>.value(value: authRepository),
        RepositoryProvider<JobsRepository>.value(value: jobsRepository),
        RepositoryProvider<SuburbsRepository>.value(value: suburbsRepository),
        RepositoryProvider<WorkersRepository>.value(value: workersRepository),
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
