import 'package:flutter/material.dart';

import '../../features/accounts/presentation/pages/landing_page.dart';
import '../../features/accounts/presentation/pages/signup_page.dart';
import '../../features/jobs/data/models/job.dart';
import '../../features/jobs/data/models/open_job.dart';
import '../../features/jobs/presentation/pages/applicants_page.dart';
import '../../features/jobs/presentation/pages/employer_home_page.dart';
import '../../features/jobs/presentation/pages/job_detail_page.dart';
import '../../features/jobs/presentation/pages/job_tracking_page.dart';
import '../../features/jobs/presentation/pages/post_job_page.dart';
import '../../features/jobs/presentation/pages/worker_home_page.dart';
import '../../features/workers/presentation/pages/my_work_page.dart';
import '../../features/workers/presentation/pages/worker_skills_page.dart';

/// Named-route table. No routing package is introduced for this — the
/// screen count doesn't warrant `go_router` yet.
Route<dynamic>? onGenerateRoute(RouteSettings settings) {
  switch (settings.name) {
    case '/':
      return MaterialPageRoute(builder: (_) => const LandingPage());
    case '/signup':
      final role = settings.arguments as String? ?? 'BUYER';
      return MaterialPageRoute(builder: (_) => SignUpPage(role: role));
    case '/employer-home':
      return MaterialPageRoute(builder: (_) => const EmployerHomePage());
    case '/post-job':
      final initialTrade = settings.arguments as String?;
      return MaterialPageRoute(builder: (_) => PostJobPage(initialTrade: initialTrade));
    case '/applicants':
      final jobId = settings.arguments as String;
      return MaterialPageRoute(builder: (_) => ApplicantsPage(jobId: jobId));
    case '/job-tracking':
      final job = settings.arguments as Job;
      return MaterialPageRoute(builder: (_) => JobTrackingPage(job: job));
    case '/worker-skills':
      return MaterialPageRoute(builder: (_) => const WorkerSkillsPage());
    case '/worker-home':
      return MaterialPageRoute(builder: (_) => const WorkerHomePage());
    case '/job-detail':
      final job = settings.arguments as OpenJob;
      return MaterialPageRoute(builder: (_) => JobDetailPage(job: job));
    case '/my-work':
      return MaterialPageRoute(builder: (_) => const MyWorkPage());
    default:
      return null;
  }
}
