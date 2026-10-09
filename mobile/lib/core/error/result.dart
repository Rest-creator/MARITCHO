import 'package:equatable/equatable.dart';

abstract class Result<T, E> extends Equatable {
  const Result();

  bool get isOk => this is Ok<T, E>;
  bool get isError => this is Error<T, E>;

  T get okValue {
    if (this is Ok<T, E>) {
      return (this as Ok<T, E>).value;
    }
    throw StateError('Cannot get value from an Error Result.');
  }

  E get errorValue {
    if (this is Error<T, E>) {
      return (this as Error<T, E>).error;
    }
    throw StateError('Cannot get error from an Ok Result.');
  }

  void match({
    required void Function(T value) onOk,
    required void Function(E error) onError,
  }) {
    if (this is Ok<T, E>) {
      onOk((this as Ok<T, E>).value);
    } else if (this is Error<T, E>) {
      onError((this as Error<T, E>).error);
    }
  }

  R fold<R>({
    required R Function(T value) onOk,
    required R Function(E error) onError,
  }) {
    if (this is Ok<T, E>) {
      return onOk((this as Ok<T, E>).value);
    } else if (this is Error<T, E>) {
      return onError((this as Error<T, E>).error);
    }
    throw StateError('Unreachable');
  }
}

class Ok<T, E> extends Result<T, E> {
  final T value;

  const Ok(this.value);

  @override
  List<Object?> get props => [value];
}

class Error<T, E> extends Result<T, E> {
  final E error;

  const Error(this.error);

  @override
  List<Object?> get props => [error];
}
