/// Backend base URL. `10.0.2.2` is the Android emulator's alias for the
/// host machine's `localhost` — the iOS simulator and web builds can
/// reach the host directly via `localhost`. Override at build time with
/// `--dart-define=API_BASE_URL=...` once a real deployed backend exists.
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
