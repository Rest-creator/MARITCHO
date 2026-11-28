import 'package:flutter/material.dart';

import '../../features/accounts/presentation/pages/account_page.dart';
import '../../features/accounts/presentation/pages/landing_page.dart';
import '../../features/accounts/presentation/pages/signup_page.dart';
import '../../features/jobs/data/models/job.dart';
import '../../features/jobs/data/models/open_job.dart';
import '../../features/jobs/presentation/pages/applicants_page.dart';
import '../../features/jobs/presentation/pages/job_detail_page.dart';
import '../../features/jobs/presentation/pages/job_tracking_page.dart';
import '../../features/jobs/presentation/pages/post_job_page.dart';
import '../../features/messaging/presentation/pages/chat_page.dart';
import '../../features/workers/presentation/pages/my_work_page.dart';
import '../../features/workers/presentation/pages/worker_public_profile_page.dart';
import '../../features/workers/presentation/pages/worker_review_client_page.dart';
import '../../features/workers/presentation/pages/worker_skills_page.dart';
import '../../features/workers/presentation/pages/workers_directory_page.dart';
import 'main_navigation_shell.dart';

/// Named-route table.
Route<dynamic>? onGenerateRoute(RouteSettings settings) {
  switch (settings.name) {
    case '/':
      return MaterialPageRoute(builder: (_) => const LandingPage());
    case '/signup':
      if (settings.arguments is Map<String, dynamic>) {
        final map = settings.arguments as Map<String, dynamic>;
        return MaterialPageRoute(
          builder: (_) => SignUpPage(
            role: map['role'] as String? ?? 'BUYER',
            initialIsLogin: map['isLogin'] as bool? ?? false,
          ),
        );
      }
      final role = settings.arguments as String? ?? 'BUYER';
      return MaterialPageRoute(builder: (_) => SignUpPage(role: role));
    case '/shell':
      final role = settings.arguments as String? ?? 'BUYER';
      return MaterialPageRoute(
        builder: (_) => MainNavigationShell(initialRole: role),
      );
    case '/employer-home':
      return MaterialPageRoute(
        builder: (_) => const MainNavigationShell(initialRole: 'BUYER'),
      );
    case '/worker-home':
      return MaterialPageRoute(
        builder: (_) => const MainNavigationShell(initialRole: 'WORKER'),
      );
    case '/workers':
      return MaterialPageRoute(builder: (_) => const WorkersDirectoryPage());
    case '/worker-public-profile':
      final workerId = settings.arguments as String;
      return MaterialPageRoute(
        builder: (_) => WorkerPublicProfilePage(workerId: workerId),
      );
    case '/worker-review-client':
      final job = settings.arguments as Job;
      return MaterialPageRoute(
        builder: (_) => WorkerReviewClientPage(job: job),
      );
    case '/account':
      return MaterialPageRoute(builder: (_) => const AccountPage());
    case '/chat':
      final args = settings.arguments as Map<String, dynamic>? ?? {};
      final jobId = args['jobId'] as String? ?? '';
      final jobTitle = args['jobTitle'] as String?;
      return MaterialPageRoute(
        builder: (_) => ChatPage(jobId: jobId, jobTitle: jobTitle),
      );
    case '/post-job':
      final initialTrade = settings.arguments as String?;
      return MaterialPageRoute(
        builder: (_) => PostJobPage(initialTrade: initialTrade),
      );
    case '/applicants':
      final jobId = settings.arguments as String;
      return MaterialPageRoute(builder: (_) => ApplicantsPage(jobId: jobId));
    case '/job-tracking':
      final job = settings.arguments as Job;
      return MaterialPageRoute(builder: (_) => JobTrackingPage(job: job));
    case '/worker-skills':
      return MaterialPageRoute(builder: (_) => const WorkerSkillsPage());
    case '/job-detail':
      final job = settings.arguments as OpenJob;
      return MaterialPageRoute(builder: (_) => JobDetailPage(job: job));
    case '/my-work':
      return MaterialPageRoute(builder: (_) => const MyWorkPage());
    default:
      return null;
  }
}
