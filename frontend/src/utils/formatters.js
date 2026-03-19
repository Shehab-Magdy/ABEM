/**
 * Locale-aware formatters for currency, dates, numbers, and phone.
 * All functions default to the current i18n language if no locale is passed.
 */
import i18n from "../i18n";

function currentLocale() {
  return i18n.language || "en";
}

/**
 * Format a monetary amount with locale-appropriate digits and currency symbol.
 * en → "EGP 1,250.00"   ar → "١٬٢٥٠٫٠٠ ج.م"
 */
export function formatCurrency(amount, locale) {
  const loc = locale || currentLocale();
  const value = typeof amount === "string" ? parseFloat(amount) : amount;
  if (Number.isNaN(value)) return String(amount);
  try {
    return new Intl.NumberFormat(loc === "ar" ? "ar-EG" : "en-EG", {
      style: "currency",
      currency: "EGP",
    }).format(value);
  } catch {
    return `${value.toFixed(2)} EGP`;
  }
}

/**
 * Format a date in short form.
 * en → "15 Mar 2026"   ar → "١٥ مارس ٢٠٢٦"
 */
export function formatDate(date, locale) {
  const loc = locale || currentLocale();
  const d = date instanceof Date ? date : new Date(date);
  if (Number.isNaN(d.getTime())) return String(date);
  try {
    return new Intl.DateTimeFormat(loc === "ar" ? "ar-EG" : "en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(d);
  } catch {
    return String(date);
  }
}

/**
 * Format a date in long form.
 * en → "Saturday, 15 March 2026"   ar → "السبت، ١٥ مارس ٢٠٢٦"
 */
export function formatDateLong(date, locale) {
  const loc = locale || currentLocale();
  const d = date instanceof Date ? date : new Date(date);
  if (Number.isNaN(d.getTime())) return String(date);
  try {
    return new Intl.DateTimeFormat(loc === "ar" ? "ar-EG" : "en-GB", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(d);
  } catch {
    return String(date);
  }
}

/**
 * Format a number with thousands separator.
 * en → "1,250"   ar → "١٬٢٥٠"
 */
export function formatNumber(n, locale) {
  const loc = locale || currentLocale();
  const value = typeof n === "string" ? parseFloat(n) : n;
  if (Number.isNaN(value)) return String(n);
  try {
    return new Intl.NumberFormat(loc === "ar" ? "ar-EG" : "en-EG").format(value);
  } catch {
    return String(n);
  }
}

/**
 * Format a phone number for display.
 * en → "+20 100 000 0000"   ar → "+٢٠ ١٠٠ ٠٠٠ ٠٠٠٠"
 */
export function formatPhone(phone, locale) {
  const loc = locale || currentLocale();
  if (!phone) return "";
  if (loc === "ar") {
    return phone.replace(/[0-9]/g, (d) => String.fromCharCode(0x0660 + parseInt(d, 10)));
  }
  return phone;
}
