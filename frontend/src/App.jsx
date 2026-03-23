import { useEffect, useState, useCallback, useMemo } from "react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { CacheProvider } from "@emotion/react";
import { useTranslation } from "react-i18next";
import AppRouter from "./routes/AppRouter";
import SessionExpiryModal from "./components/SessionExpiryModal";
import { ltrTheme, rtlTheme } from "./theme/theme";
import { createDirectionCache } from "./theme/rtlCache";
import { useEasternArabicInput } from "./hooks/useEasternArabicInput";

export default function App() {
  const { i18n } = useTranslation();
  const [dir, setDir] = useState((i18n.language || "en").startsWith("ar") ? "rtl" : "ltr");

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

  const theme = dir === "rtl" ? rtlTheme : ltrTheme;

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
        <AppRouter />
        <SessionExpiryModal />
      </ThemeProvider>
    </CacheProvider>
  );
}
