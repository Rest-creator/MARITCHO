import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/storage/token_storage.dart';
import 'package:mobile/features/accounts/data/models/code_request.dart';
import 'package:mobile/features/accounts/data/models/person.dart';
import 'package:mobile/features/accounts/data/repositories/auth_repository.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_cubit.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_state.dart';

import '../../support/fake_http_adapter.dart';

/// Scripted answers for the two sign-in calls.
class _FakeAuthRepository extends AuthRepository {
  final Result<CodeRequest, Failure> codeResult;
  final String acceptedCode = '123456';
  final List<String?> codesTried = <String?>[];

  _FakeAuthRepository({
    this.codeResult = const Ok(
      CodeRequest(isCodeRequired: true, resendAfterSeconds: 30),
    ),
  }) : super(Dio(), TokenStorage());

  @override
  Future<Result<CodeRequest, Failure>> requestCode({
    required String phone,
  }) async => codeResult;

  @override
  Future<Result<Person, Failure>> login({
    required String phone,
    required String role,
    String? code,
  }) async {
    codesTried.add(code);
    final bool needsCode = codeResult.isOk && codeResult.okValue.isCodeRequired;
    if (needsCode && code != acceptedCode) {
      return const Error(
        NetworkFailure(message: "That code isn't right, or it has expired."),
      );
    }
    return Ok(Person(id: '1', phone: phone, role: role));
  }
}

void main() {
  group('AuthRepository.normalisePhone', () {
    test('turns what people type into one international number', () {
      expect(
        AuthRepository.normalisePhone('+263 77 412 3089'),
        '+263774123089',
      );
      expect(AuthRepository.normalisePhone('0774123089'), '+263774123089');
      expect(AuthRepository.normalisePhone('77 412 3089'), '+263774123089');
    });
  });

  group('AuthRepository through the BFF', () {
    setUp(() => SharedPreferences.setMockInitialValues(<String, Object>{}));

    test('asks the BFF for a code', () async {
      final FakeHttpAdapter adapter = FakeHttpAdapter(
        (RequestOptions o) => const FakeReply(200, <String, Object?>{
          'code_required': true,
          'resend_after_seconds': 30,
        }),
      );
      final AuthRepository repository = AuthRepository(
        fakeDio(adapter),
        TokenStorage(),
      );

      final Result<CodeRequest, Failure> result = await repository.requestCode(
        phone: '+263774123089',
      );

      expect(
        result.okValue,
        const CodeRequest(isCodeRequired: true, resendAfterSeconds: 30),
      );
      expect(adapter.requests.single.path, '/session/code');
    });

    test('signs in as the app and keeps the token the BFF returns', () async {
      final FakeHttpAdapter adapter = FakeHttpAdapter(
        (RequestOptions o) => const FakeReply(200, <String, Object?>{
          'user': <String, Object?>{
            'id': 'u1',
            'phone': '+263774123089',
            'role': 'WORKER',
          },
          'access_token': 'jwt-123',
        }),
      );
      final TokenStorage storage = TokenStorage();
      final AuthRepository repository = AuthRepository(
        fakeDio(adapter),
        storage,
      );

      final Result<Person, Failure> result = await repository.login(
        phone: '+263774123089',
        role: 'WORKER',
        code: '482913',
      );

      expect(result.okValue.role, 'WORKER');
      expect(await storage.getToken(), 'jwt-123');
      final RequestOptions sent = adapter.requests.single;
      expect(sent.path, '/session');
      expect(sent.headers['X-Maricho-Client'], 'mobile');
      expect(sent.data, <String, Object?>{
        'phone': '+263774123089',
        'role': 'WORKER',
        'code': '482913',
      });
    });

    test("leaves the code out while the backend can't send one", () async {
      final FakeHttpAdapter adapter = FakeHttpAdapter(
        (RequestOptions o) => const FakeReply(200, <String, Object?>{
          'user': <String, Object?>{
            'id': 'u1',
            'phone': '+263774123089',
            'role': 'BUYER',
          },
          'access_token': 'jwt-1',
        }),
      );
      await AuthRepository(
        fakeDio(adapter),
        TokenStorage(),
      ).login(phone: '+263774123089', role: 'BUYER');
      expect(adapter.requests.single.data, <String, Object?>{
        'phone': '+263774123089',
        'role': 'BUYER',
      });
    });

    test("shows the BFF's reason when sign-in is refused", () async {
      final FakeHttpAdapter adapter = FakeHttpAdapter(
        (RequestOptions o) => const FakeReply(400, <String, Object?>{
          'detail': "That code isn't right, or it has expired.",
        }),
      );
      final Result<Person, Failure> result = await AuthRepository(
        fakeDio(adapter),
        TokenStorage(),
      ).login(phone: '+263774123089', role: 'BUYER', code: '000000');
      expect(
        result.errorValue.message,
        "That code isn't right, or it has expired.",
      );
    });
  });

  group('AuthCubit', () {
    test('starts in AuthInitial', () async {
      final AuthCubit cubit = AuthCubit(_FakeAuthRepository());
      expect(cubit.state, isA<AuthInitial>());
      await cubit.close();
    });

    test('asks for the code that was sent, then signs in with it', () async {
      final _FakeAuthRepository repository = _FakeAuthRepository();
      final AuthCubit cubit = AuthCubit(repository);

      await cubit.start(phone: '0774123089', role: 'WORKER');
      expect(cubit.state, const AuthCodeRequired(phone: '+263774123089'));

      await cubit.verify('123456');
      expect(cubit.state, isA<AuthSuccess>());
      expect((cubit.state as AuthSuccess).person.role, 'WORKER');
      expect(repository.codesTried, <String?>['123456']);
      await cubit.close();
    });

    test('a wrong code keeps the code screen and says why', () async {
      final AuthCubit cubit = AuthCubit(_FakeAuthRepository());
      await cubit.start(phone: '0774123089', role: 'BUYER');

      await cubit.verify('000000');

      final AuthState state = cubit.state;
      expect(state, isA<AuthCodeRequired>());
      expect((state as AuthCodeRequired).errorMessage, contains("isn't right"));
      await cubit.close();
    });

    test("signs straight in while the backend can't send codes", () async {
      final _FakeAuthRepository repository = _FakeAuthRepository(
        codeResult: const Ok(CodeRequest(isCodeRequired: false)),
      );
      final AuthCubit cubit = AuthCubit(repository);

      await cubit.start(phone: '0774123089', role: 'BUYER');

      expect(cubit.state, isA<AuthSuccess>());
      expect(repository.codesTried, <String?>[null]);
      await cubit.close();
    });

    test('ends in AuthFailure when the code request fails', () async {
      final AuthCubit cubit = AuthCubit(
        _FakeAuthRepository(
          codeResult: const Error(NetworkFailure(message: 'No signal')),
        ),
      );
      await cubit.start(phone: '0774123089', role: 'BUYER');
      expect(cubit.state, const AuthFailure('No signal'));
      await cubit.close();
    });
  });
}
