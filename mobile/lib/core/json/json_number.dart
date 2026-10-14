/// Reads a number the backend sent. Pydantic serialises `Decimal` fields
/// (money, rates, coordinates) as JSON strings such as `"40.00"`, while
/// plain floats (e.g. `distance_km`) arrive as numbers — accept both.
double? readDecimal(Object? value) {
  if (value == null) return null;
  if (value is num) return value.toDouble();
  if (value is String) return double.tryParse(value.trim());
  return null;
}

/// Like [readDecimal] for fields the backend always sends; a missing or
/// unreadable value becomes [fallback] rather than crashing the whole list.
double readRequiredDecimal(Object? value, {double fallback = 0}) {
  return readDecimal(value) ?? fallback;
}
