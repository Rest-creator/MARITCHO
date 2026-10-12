import 'package:equatable/equatable.dart';

class Person extends Equatable {
  final String id;
  final String phone;
  final String role;

  const Person({required this.id, required this.phone, required this.role});

  factory Person.fromJson(Map<String, dynamic> json) {
    return Person(
      id: json['id'] as String,
      phone: json['phone'] as String,
      role: json['role'] as String,
    );
  }

  @override
  List<Object?> get props => [id, phone, role];
}
