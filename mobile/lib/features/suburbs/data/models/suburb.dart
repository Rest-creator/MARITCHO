import 'package:equatable/equatable.dart';
import 'package:mobile/core/json/json_number.dart';

class Suburb extends Equatable {
  final String name;
  final double latitude;
  final double longitude;

  const Suburb({
    required this.name,
    required this.latitude,
    required this.longitude,
  });

  factory Suburb.fromJson(Map<String, dynamic> json) {
    return Suburb(
      name: json['name'] as String,
      latitude: readRequiredDecimal(json['latitude']),
      longitude: readRequiredDecimal(json['longitude']),
    );
  }

  @override
  List<Object?> get props => [name, latitude, longitude];
}
