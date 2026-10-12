import 'package:dio/dio.dart';

import '../storage/token_storage.dart';
import 'api_config.dart';

/// Builds the shared Dio instance every online repository uses: base URL
/// plus an interceptor that attaches the stored bearer token (if any) to
/// every outgoing request.
Dio buildApiDio(TokenStorage tokenStorage) {
  final dio = Dio(BaseOptions(baseUrl: ApiConfig.baseUrl));

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await tokenStorage.getToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ),
  );

  return dio;
}
