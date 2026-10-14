/// Where the app's API lives: the BFF (`/api` on the Next.js server,
/// ADR-009), not FastAPI directly. `10.0.2.2` is the Android emulator's
/// name for the host machine; override at build time with
/// `--dart-define=API_BASE_URL=https://<site>/api`.
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:3000/api',
  );
}
