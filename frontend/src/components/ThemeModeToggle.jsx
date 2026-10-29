/**
 * Light/dark toggle. Applies instantly, then saves to the profile when signed in.
 */
import { useTranslation } from "react-i18next";
import { IconButton, Tooltip } from "@mui/material";
import { DarkMode, LightMode } from "@mui/icons-material";
import { useAuthStore } from "../contexts/authStore";
import { useThemeStore } from "../contexts/themeStore";
import { useResolvedMode } from "../hooks/useThemeMode";
import { authApi } from "../api/authApi";

export default function ThemeModeToggle() {
  const { t } = useTranslation("common");
  const resolved = useResolvedMode();
  const setMode = useThemeStore((s) => s.setMode);
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);

  const handleClick = async () => {
    const next = resolved === "dark" ? "light" : "dark";
    setMode(next);
    if (!user) return;
    try {
      const res = await authApi.updateProfile({ preferred_theme: next });
      setUser(res.data);
    } catch {
      // Keep the local choice; it will re-sync on the next successful save
    }
  };

  const label = resolved === "dark" ? t("switch_to_light") : t("switch_to_dark");
  return (
    <Tooltip title={label}>
      <IconButton color="inherit" onClick={handleClick} aria-label={label} data-testid="theme-toggle" sx={{ mr: 1 }}>
        {resolved === "dark" ? <LightMode /> : <DarkMode />}
      </IconButton>
    </Tooltip>
  );
}
