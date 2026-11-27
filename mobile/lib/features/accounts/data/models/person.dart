import 'package:equatable/equatable.dart';

class Person extends Equatable {
  final String id;
  final String phone;
  final String role;
  final List<String> roles;
  final String? displayName;
  final bool isAvailable;
  final int travelKm;
  final String? homeSuburb;
  final String? nextOfKinPhone;

  const Person({
    required this.id,
    required this.phone,
    required this.role,
    this.roles = const [],
    this.displayName,
    this.isAvailable = true,
    this.travelKm = 50,
    this.homeSuburb,
    this.nextOfKinPhone,
  });

  factory Person.fromJson(Map<String, dynamic> json) {
    final rawRoles = json['roles'];
    final List<String> parsedRoles = rawRoles is List
        ? rawRoles.map((e) => e.toString()).toList()
        : [json['role'] as String? ?? 'BUYER'];

    return Person(
      id: json['id'] as String,
      phone: json['phone'] as String,
      role: json['role'] as String,
      roles: parsedRoles,
      displayName: json['display_name'] as String?,
      isAvailable: json['is_available'] as bool? ?? true,
      travelKm: (json['travel_km'] as num?)?.toInt() ?? 50,
      homeSuburb: json['home_suburb'] as String?,
      nextOfKinPhone: json['next_of_kin_phone'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'phone': phone,
      'role': role,
      'roles': roles,
      'display_name': displayName,
      'is_available': isAvailable,
      'travel_km': travelKm,
      'home_suburb': homeSuburb,
      'next_of_kin_phone': nextOfKinPhone,
    };
  }

  Person copyWith({
    String? id,
    String? phone,
    String? role,
    List<String>? roles,
    String? displayName,
    bool? isAvailable,
    int? travelKm,
    String? homeSuburb,
    String? nextOfKinPhone,
  }) {
    return Person(
      id: id ?? this.id,
      phone: phone ?? this.phone,
      role: role ?? this.role,
      roles: roles ?? this.roles,
      displayName: displayName ?? this.displayName,
      isAvailable: isAvailable ?? this.isAvailable,
      travelKm: travelKm ?? this.travelKm,
      homeSuburb: homeSuburb ?? this.homeSuburb,
      nextOfKinPhone: nextOfKinPhone ?? this.nextOfKinPhone,
    );
  }

  @override
  List<Object?> get props => [
    id,
    phone,
    role,
    roles,
    displayName,
    isAvailable,
    travelKm,
    homeSuburb,
    nextOfKinPhone,
  ];
}
