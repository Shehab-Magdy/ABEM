import 'package:intl/intl.dart';

/// Format a monetary amount as EGP currency.
///
/// In Arabic locale, Eastern Arabic-Indic numerals are used automatically.
String formatCurrency(double amount, {String locale = 'en'}) {
  return NumberFormat.currency(
    locale: locale == 'ar' ? 'ar_EG' : 'en_EG',
    symbol: 'EGP ',
    decimalDigits: 2,
  ).format(amount);
}
