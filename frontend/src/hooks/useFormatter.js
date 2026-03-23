/**
 * Returns bound versions of all formatters pre-filled with the current locale.
 * Eliminates the need to pass locale in every call site.
 */
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  formatCurrency as _formatCurrency,
  formatDate as _formatDate,
  formatDateLong as _formatDateLong,
  formatNumber as _formatNumber,
  formatPhone as _formatPhone,
} from "../utils/formatters";

export function useFormatter() {
  const { i18n } = useTranslation();
  const locale = i18n.language || "en";

  return useMemo(
    () => ({
      formatCurrency: (amount) => _formatCurrency(amount, locale),
      formatDate: (date) => _formatDate(date, locale),
      formatDateLong: (date) => _formatDateLong(date, locale),
      formatNumber: (n) => _formatNumber(n, locale),
      formatPhone: (phone) => _formatPhone(phone, locale),
    }),
    [locale]
  );
}
