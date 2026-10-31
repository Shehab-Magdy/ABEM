/**
 * Compact header button that switches between English and Arabic.
 * Shows the language you will switch TO ("ع" while English is active, "EN" while Arabic is).
 * Switching is instant (i18n + document dir + MUI rtl theme are driven by the languageChanged event
 * in App.jsx) and, when signed in, saved to the profile exactly like the Profile page does, so the
 * choice follows the user across devices (usePreferredLanguage reads it back).
 */
import { useTranslation } from "react-i18next";
import { Button, Tooltip } from "@mui/material";
import { authApi } from "../api/authApi";
import { useAuthStore } from "../contexts/authStore";

export default function LanguageToggleButton({ sx, color = "inherit" }) {
  const { t, i18n } = useTranslation("common");
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const isArabic = (i18n.language || "en").startsWith("ar");
  const target = isArabic ? "en" : "ar";
  const label = isArabic ? t("switch_to_english", "Switch to English") : t("switch_to_arabic", "Switch to Arabic");

  const handleClick = async () => {
    i18n.changeLanguage(target);
    try {
      localStorage.setItem("abem_language", target);
    } catch {
      // Storage disabled
    }
    if (!user) return;
    try {
      const res = await authApi.updateProfile({ preferred_language: target });
      setUser(res.data);
    } catch {
      // Keep the local choice; it re-syncs on the next successful save
    }
  };

  return (
    <Tooltip title={label}>
      <Button
        id="language-switch"
        color={color}
        onClick={handleClick}
        aria-label={label}
        data-testid="language-switch"
        lang={target}
        sx={{ minWidth: 40, px: 1, mr: 1, fontWeight: 700, fontSize: 15, lineHeight: 1.2, ...sx }}
      >
        {isArabic ? "EN" : "ع"}
      </Button>
    </Tooltip>
  );
}
