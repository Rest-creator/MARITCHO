import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// Answers Dio requests from a function instead of the network. Return a
/// status/body pair, or throw a [DioException] to simulate no signal.
class FakeHttpAdapter implements HttpClientAdapter {
  final FakeReply Function(RequestOptions options) _reply;
  final List<RequestOptions> requests = <RequestOptions>[];

  FakeHttpAdapter(this._reply);

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final FakeReply reply = _reply(options);
    return ResponseBody.fromString(
      jsonEncode(reply.body),
      reply.status,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>[Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

class FakeReply {
  final int status;
  final Object? body;

  const FakeReply(this.status, [this.body]);
}

/// A Dio wired to [adapter], with no interceptors (no retries, no breaker).
Dio fakeDio(FakeHttpAdapter adapter) =>
    Dio(BaseOptions(baseUrl: 'http://backend.test'))
      ..httpClientAdapter = adapter;

/// What a dropped connection looks like to Dio.
Never noSignal(RequestOptions options) => throw DioException(
  requestOptions: options,
  type: DioExceptionType.connectionError,
);
