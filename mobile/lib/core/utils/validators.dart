/// Common validation functions for form fields.

String? validateEmail(String? value) {
  if (value == null || value.trim().isEmpty) return 'Email is required';
  final regex = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
  if (!regex.hasMatch(value.trim())) return 'Enter a valid email';
  return null;
}

String? validatePassword(String? value) {
  if (value == null || value.isEmpty) return 'Password is required';
  if (value.length < 8) return 'Password must be at least 8 characters';
  return null;
}

String? validateRequired(String? value, [String fieldName = 'This field']) {
  if (value == null || value.trim().isEmpty) return '$fieldName is required';
  return null;
}

String? validatePositiveNumber(String? value, [String fieldName = 'Amount']) {
  if (value == null || value.trim().isEmpty) return '$fieldName is required';
  final num? parsed = num.tryParse(value.trim());
  if (parsed == null || parsed <= 0) return '$fieldName must be a positive number';
  return null;
}

String? validateMinFloors(String? value) {
  if (value == null || value.trim().isEmpty) return 'Number of floors is required';
  final int? floors = int.tryParse(value.trim());
  if (floors == null || floors < 1) return 'Must be at least 1';
  return null;
}
