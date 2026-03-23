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
    fallbackLng: "en",
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
    ],
    backend: { loadPath: "/locales/{{lng}}/{{ns}}.json" },
    detection: {
      order: ["localStorage", "navigator", "htmlTag"],
      caches: ["localStorage"],
      lookupLocalStorage: "abem_language",
    },
    interpolation: { escapeValue: false },
    react: { useSuspense: true },
  });

export default i18n;
