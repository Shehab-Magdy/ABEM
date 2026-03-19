/**
 * Compact language toggle: EN ↔ AR
 * Placed in the AppHeader and on public auth pages.
 */
import { useTranslation } from "react-i18next";
import { IconButton, Tooltip, Typography } from "@mui/material";
import { Translate } from "@mui/icons-material";
import { useAuthStore } from "../contexts/authStore";
import { authApi } from "../api/authApi";

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation("common");
  const user = useAuthStore((s) => s.user);

  const currentLang = i18n.language === "ar" ? "ar" : "en";
  const nextLang = currentLang === "ar" ? "en" : "ar";
  const label = currentLang === "ar" ? "EN" : "AR";

  const handleSwitch = () => {
    i18n.changeLanguage(nextLang);
    try {
      localStorage.setItem("abem_language", nextLang);
    } catch {
      // Storage disabled — ignore
    }
    // Fire-and-forget: sync preference to server if logged in
    if (user) {
      authApi.updateProfile({ preferred_language: nextLang }).catch(() => {});
    }
  };

  return (
    <Tooltip title={t("change_language")}>
      <IconButton
        onClick={handleSwitch}
        size="small"
        aria-label={t("change_language")}
        sx={{ mx: 0.5 }}
      >
        <Translate sx={{ fontSize: 18, mr: 0.3 }} />
        <Typography variant="caption" fontWeight={600} sx={{ fontSize: 11 }}>
          {label}
        </Typography>
      </IconButton>
    </Tooltip>
  );
}
