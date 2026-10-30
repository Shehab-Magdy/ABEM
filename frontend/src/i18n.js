import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import HttpBackend from "i18next-http-backend";

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    defaultNS: "common",
    fallbackLng: "ar", // Arabic-first: visitors who have not picked a language get Arabic
    supportedLngs: ["en", "ar"],
    ns: [
      "common",
      "auth",
      "dashboard",
      "buildings",
      "expenses",
      "payments",
      "notifications",
      "users",
      "categories",
      "profile",
      "errors",
      "audit",
      "exports",
      "tutorial",
      "maintenance",
      "statement",
      "legal",
      "governance",
      "subscription",
      "board",
      "records",
    ],
    backend: { loadPath: "/locales/{{lng}}/{{ns}}.json" },
    detection: {
      // Saved choice first, then <html lang="ar">; the phone/browser language is deliberately not used
      order: ["localStorage", "htmlTag"],
      caches: ["localStorage"],
      lookupLocalStorage: "abem_language",
    },
    interpolation: { escapeValue: false },
    react: { useSuspense: true },
  });

export default i18n;
