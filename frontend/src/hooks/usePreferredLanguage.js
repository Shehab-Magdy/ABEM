/**
 * Syncs the i18n language with the user's preferred_language from the server.
 * On mount, if the user has a preferred_language that differs from the current
 * i18n language, it changes the language to match the user's preference.
 * This ensures language follows the user across devices.
 */
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../contexts/authStore";

export function usePreferredLanguage() {
  const { i18n } = useTranslation();
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    const preferred = user?.preferred_language;
    if (preferred && preferred !== i18n.language && ["en", "ar"].includes(preferred)) {
      i18n.changeLanguage(preferred);
    }
  }, [user?.preferred_language, i18n]);
}
