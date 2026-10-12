import 'package:equatable/equatable.dart';

class Suburb extends Equatable {
  final String name;
  final double latitude;
  final double longitude;

  const Suburb({required this.name, required this.latitude, required this.longitude});

  factory Suburb.fromJson(Map<String, dynamic> json) {
    return Suburb(
      name: json['name'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
    );
  }

  @override
  List<Object?> get props => [name, latitude, longitude];
}
