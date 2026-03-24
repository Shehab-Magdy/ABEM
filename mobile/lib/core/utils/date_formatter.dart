import 'package:intl/intl.dart';

/// Format a DateTime for display.
String formatDate(DateTime date, {String locale = 'en'}) {
  return DateFormat.yMMMd(locale).format(date);
}

/// Format a DateTime for API requests (ISO 8601 date only).
String formatDateForApi(DateTime date) {
  return DateFormat('yyyy-MM-dd').format(date);
}

/// Parse an ISO date string from the API.
DateTime? parseApiDate(String? dateStr) {
  if (dateStr == null || dateStr.isEmpty) return null;
  return DateTime.tryParse(dateStr);
}
