import { useEffect, useState, useCallback, useMemo } from "react";
import { Box, CircularProgress, ThemeProvider, CssBaseline } from "@mui/material";
import { CacheProvider } from "@emotion/react";
import { useTranslation } from "react-i18next";
import AppRouter from "./routes/AppRouter";
import SessionExpiryModal from "./components/SessionExpiryModal";
import InstallPrompt from "./components/InstallPrompt";
import { ltrTheme, rtlTheme, ltrDarkTheme, rtlDarkTheme } from "./theme/theme";
import { useResolvedMode, useSyncPreferredTheme } from "./hooks/useThemeMode";
import { createDirectionCache } from "./theme/rtlCache";
import { useEasternArabicInput } from "./hooks/useEasternArabicInput";
import { useAuthStore, hadSession, clearHasSession } from "./contexts/authStore";
import { authApi } from "./api/authApi";

export default function App() {
  const { i18n } = useTranslation();
  const [dir, setDir] = useState((i18n.language || "en").startsWith("ar") ? "rtl" : "ltr");
  const [bootstrapped, setBootstrapped] = useState(!hadSession());

  // On a hard reload, the in-memory accessToken is gone by design (see
  // authStore.js). If we previously believed the browser holds a
  // refresh_token cookie (abem-has-session flag), try a single silent
  // refresh to restore it before rendering protected routes — this avoids
  // bouncing an already-signed-in user to /login on every page reload.
  useEffect(() => {
    if (!hadSession()) return;
    let cancelled = false;
    authApi
      .refresh()
      .then(({ data }) => {
        if (cancelled) return;
        useAuthStore.getState().setAccessToken(data.access);
        // /auth/refresh/ only returns {access}; repopulate the user profile.
        return authApi.getProfile().then((res) => {
          if (!cancelled) useAuthStore.getState().setUser(res.data);
        });
      })
      .catch(() => {
        // Refresh failed (expired/revoked/missing cookie) — fall back to
        // a signed-out state; no redirect needed, route guards handle it.
        if (!cancelled) {
          clearHasSession();
          useAuthStore.getState().logout();
        }
      })
      .finally(() => {
        if (!cancelled) setBootstrapped(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const updateDir = useCallback((lng) => {
    const newDir = (lng || "en").startsWith("ar") ? "rtl" : "ltr";
    setDir(newDir);
    document.documentElement.dir = newDir;
    document.documentElement.lang = lng;
  }, []);

  useEffect(() => {
    updateDir(i18n.language);
    i18n.on("languageChanged", updateDir);
    return () => i18n.off("languageChanged", updateDir);
  }, [i18n, updateDir]);

  // T-01: convert Eastern Arabic-Indic digits (٠-٩) → ASCII in number fields
  useEasternArabicInput();

  useSyncPreferredTheme();
  const mode = useResolvedMode();
  const theme =
    dir === "rtl" ? (mode === "dark" ? rtlDarkTheme : rtlTheme) : mode === "dark" ? ltrDarkTheme : ltrTheme;

  useEffect(() => {
    document.documentElement.style.colorScheme = mode;
  }, [mode]);

  // Create a fresh Emotion cache every time direction changes.
  // This is critical: Emotion caches are singletons that keep their
  // injected <style> tags. Swapping CacheProvider value does NOT remove
  // old styles. A new cache forces Emotion to re-process all CSS from
  // scratch with the correct stylis RTL/LTR plugin.
  const cache = useMemo(() => createDirectionCache(dir), [dir]);

  return (
    <CacheProvider value={cache} key={dir}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {bootstrapped ? (
          <>
            <AppRouter />
            <SessionExpiryModal />
            <InstallPrompt />
          </>
        ) : (
          // Restoring the session from the refresh_token cookie — render
          // nothing meaningful yet to avoid a flash of the login page for
          // an already-signed-in user on a hard reload.
          <Box display="flex" alignItems="center" justifyContent="center" minHeight="100vh">
            <CircularProgress />
          </Box>
        )}
      </ThemeProvider>
    </CacheProvider>
  );
}
