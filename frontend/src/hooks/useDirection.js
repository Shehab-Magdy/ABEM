/**
 * Returns "ltr" | "rtl" based on the current i18n language.
 * Re-renders when the language changes.
 */
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";

function langToDir(lng) {
  return (lng || "en").startsWith("ar") ? "rtl" : "ltr";
}

export function useDirection() {
  const { i18n } = useTranslation();
  const [dir, setDir] = useState(langToDir(i18n.language));

  useEffect(() => {
    const handleChange = (lng) => setDir(langToDir(lng));
    handleChange(i18n.language);
    i18n.on("languageChanged", handleChange);
    return () => i18n.off("languageChanged", handleChange);
  }, [i18n]);

  return dir;
}
