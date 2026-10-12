import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/storage/database_helper.dart';
import 'package:mobile/core/storage/token_storage.dart';
import 'package:mobile/features/accounts/data/repositories/auth_repository.dart';
import 'package:mobile/features/jobs/data/repositories/jobs_repository.dart';
import 'package:mobile/features/suburbs/data/repositories/suburbs_repository.dart';
import 'package:mobile/features/workers/data/repositories/workers_repository.dart';
import 'package:mobile/main.dart';

void main() {
  testWidgets('renders the Landing page with both role cards', (WidgetTester tester) async {
    final dio = Dio();
    final dbHelper = DatabaseHelper();
    final authRepository = AuthRepository(dio, TokenStorage());
    final jobsRepository = JobsRepository(dio, dbHelper);
    final suburbsRepository = SuburbsRepository(dio);
    final workersRepository = WorkersRepository(dio, dbHelper);

    await tester.pumpWidget(
      MyApp(
        authRepository: authRepository,
        jobsRepository: jobsRepository,
        suburbsRepository: suburbsRepository,
        workersRepository: workersRepository,
      ),
    );

    expect(find.text('Maricho'), findsOneWidget);
    expect(find.text('Your skills are your CV.'), findsOneWidget);
    expect(find.text('I need work done'), findsOneWidget);
    expect(find.text("I'm looking for work"), findsOneWidget);
  });
}
