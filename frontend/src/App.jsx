import { useEffect, useState } from "react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { CacheProvider } from "@emotion/react";
import { useTranslation } from "react-i18next";
import AppRouter from "./routes/AppRouter";
import { ltrTheme, rtlTheme } from "./theme/theme";
import { ltrCache, rtlCache } from "./theme/rtlCache";

export default function App() {
  const { i18n } = useTranslation();
  const [dir, setDir] = useState(i18n.language === "ar" ? "rtl" : "ltr");

  useEffect(() => {
    const updateDir = (lng) => {
      const newDir = lng === "ar" ? "rtl" : "ltr";
      setDir(newDir);
      document.documentElement.dir = newDir;
      document.documentElement.lang = lng;
    };

    // Set initial direction
    updateDir(i18n.language);

    // Listen for language changes
    i18n.on("languageChanged", updateDir);
    return () => i18n.off("languageChanged", updateDir);
  }, [i18n]);

  const theme = dir === "rtl" ? rtlTheme : ltrTheme;
  const cache = dir === "rtl" ? rtlCache : ltrCache;

  return (
    <CacheProvider value={cache}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppRouter />
      </ThemeProvider>
    </CacheProvider>
  );
}
