/**
 * Language selector dropdown for public pages (login/register).
 * After login, the user's preferred_language from the server is used
 * and the switcher is not shown — language can only be changed from
 * the profile page.
 */
import { useTranslation } from "react-i18next";
import { FormControl, MenuItem, Select } from "@mui/material";
import { Translate } from "@mui/icons-material";

const LANGUAGES = [
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "ar", label: "العربية", flag: "🇪🇬" },
];

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const currentLang = (i18n.language || "en").startsWith("ar") ? "ar" : "en";

  const handleChange = (e) => {
    const lang = e.target.value;
    i18n.changeLanguage(lang);
    try {
      localStorage.setItem("abem_language", lang);
    } catch {
      // Storage disabled
    }
  };

  return (
    <FormControl size="small" sx={{ minWidth: 120 }}>
      <Select
        value={currentLang}
        onChange={handleChange}
        variant="outlined"
        startAdornment={<Translate sx={{ fontSize: 18, mr: 0.5, color: "text.secondary" }} />}
        sx={{
          "& .MuiSelect-select": {
            py: 0.75,
            display: "flex",
            alignItems: "center",
            fontSize: 14,
          },
          bgcolor: "background.paper",
        }}
      >
        {LANGUAGES.map((lang) => (
          <MenuItem key={lang.code} value={lang.code}>
            {lang.flag} {lang.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
