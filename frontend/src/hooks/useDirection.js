/**
 * Returns "ltr" | "rtl" based on the current i18n language.
 * Re-renders when the language changes.
 */
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";

export function useDirection() {
  const { i18n } = useTranslation();
  const [dir, setDir] = useState(i18n.language === "ar" ? "rtl" : "ltr");

  useEffect(() => {
    const handleChange = (lng) => setDir(lng === "ar" ? "rtl" : "ltr");
    handleChange(i18n.language);
    i18n.on("languageChanged", handleChange);
    return () => i18n.off("languageChanged", handleChange);
  }, [i18n]);

  return dir;
}
