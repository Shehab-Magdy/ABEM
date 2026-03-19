import { useEffect, useState, useCallback } from "react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { CacheProvider } from "@emotion/react";
import { useTranslation } from "react-i18next";
import AppRouter from "./routes/AppRouter";
import { ltrTheme, rtlTheme } from "./theme/theme";
import { ltrCache, rtlCache } from "./theme/rtlCache";

export default function App() {
  const { i18n } = useTranslation();
  const [dir, setDir] = useState(i18n.language === "ar" ? "rtl" : "ltr");

  const updateDir = useCallback((lng) => {
    const newDir = lng === "ar" ? "rtl" : "ltr";
    setDir(newDir);
    document.documentElement.dir = newDir;
    document.documentElement.lang = lng;
  }, []);

  useEffect(() => {
    updateDir(i18n.language);
    i18n.on("languageChanged", updateDir);
    return () => i18n.off("languageChanged", updateDir);
  }, [i18n, updateDir]);

  const theme = dir === "rtl" ? rtlTheme : ltrTheme;
  const cache = dir === "rtl" ? rtlCache : ltrCache;

  // key={dir} forces React to remount the entire MUI tree when direction
  // changes, ensuring Emotion re-injects all CSS with the correct stylis
  // RTL plugin. Without this, components rendered before the switch keep
  // their old LTR/RTL styles.
  return (
    <CacheProvider value={cache}>
      <ThemeProvider theme={theme} key={dir}>
        <CssBaseline />
        <AppRouter />
      </ThemeProvider>
    </CacheProvider>
  );
}
