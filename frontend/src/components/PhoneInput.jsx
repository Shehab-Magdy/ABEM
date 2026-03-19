/**
 * Phone input with country code selector.
 * Defaults to Egypt (+20). Stores the full international number.
 */
import { useState } from "react";
import {
  InputAdornment,
  MenuItem,
  Select,
  TextField,
} from "@mui/material";

const COUNTRY_CODES = [
  { code: "+20", country: "EG", flag: "🇪🇬", label: "Egypt" },
  { code: "+966", country: "SA", flag: "🇸🇦", label: "Saudi Arabia" },
  { code: "+971", country: "AE", flag: "🇦🇪", label: "UAE" },
  { code: "+962", country: "JO", flag: "🇯🇴", label: "Jordan" },
  { code: "+961", country: "LB", flag: "🇱🇧", label: "Lebanon" },
  { code: "+964", country: "IQ", flag: "🇮🇶", label: "Iraq" },
  { code: "+974", country: "QA", flag: "🇶🇦", label: "Qatar" },
  { code: "+965", country: "KW", flag: "🇰🇼", label: "Kuwait" },
  { code: "+968", country: "OM", flag: "🇴🇲", label: "Oman" },
  { code: "+973", country: "BH", flag: "🇧🇭", label: "Bahrain" },
  { code: "+1", country: "US", flag: "🇺🇸", label: "USA" },
  { code: "+44", country: "GB", flag: "🇬🇧", label: "UK" },
  { code: "+49", country: "DE", flag: "🇩🇪", label: "Germany" },
  { code: "+33", country: "FR", flag: "🇫🇷", label: "France" },
];

function parsePhone(value) {
  if (!value) return { countryCode: "+20", local: "" };
  const trimmed = value.trim();
  // Try to match a known country code prefix
  for (const cc of COUNTRY_CODES) {
    if (trimmed.startsWith(cc.code)) {
      return { countryCode: cc.code, local: trimmed.slice(cc.code.length).trim() };
    }
  }
  // If starts with + but no match, extract first part
  if (trimmed.startsWith("+")) {
    const match = trimmed.match(/^(\+\d{1,4})\s*(.*)/);
    if (match) return { countryCode: match[1], local: match[2] };
  }
  return { countryCode: "+20", local: trimmed };
}

export default function PhoneInput({
  value,
  onChange,
  label,
  helperText,
  error,
  size = "medium",
  fullWidth = true,
  ...rest
}) {
  const parsed = parsePhone(value);
  const [countryCode, setCountryCode] = useState(parsed.countryCode);
  const [localNumber, setLocalNumber] = useState(parsed.local);

  const handleCountryChange = (e) => {
    const newCode = e.target.value;
    setCountryCode(newCode);
    const full = localNumber ? `${newCode} ${localNumber}` : "";
    onChange(full);
  };

  const handleLocalChange = (e) => {
    const local = e.target.value.replace(/[^\d\s\-()]/g, "");
    setLocalNumber(local);
    const full = local ? `${countryCode} ${local}` : "";
    onChange(full);
  };

  const selectedCountry = COUNTRY_CODES.find((c) => c.code === countryCode) || COUNTRY_CODES[0];

  return (
    <TextField
      label={label}
      value={localNumber}
      onChange={handleLocalChange}
      error={error}
      helperText={helperText}
      size={size}
      fullWidth={fullWidth}
      type="tel"
      inputProps={{ dir: "ltr" }}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <Select
              value={countryCode}
              onChange={handleCountryChange}
              variant="standard"
              disableUnderline
              sx={{
                minWidth: 75,
                "& .MuiSelect-select": {
                  py: 0,
                  pr: "20px !important",
                  display: "flex",
                  alignItems: "center",
                  fontSize: 14,
                },
              }}
              renderValue={(val) => {
                const c = COUNTRY_CODES.find((cc) => cc.code === val);
                return c ? `${c.flag} ${c.code}` : val;
              }}
            >
              {COUNTRY_CODES.map((cc) => (
                <MenuItem key={cc.code} value={cc.code}>
                  {cc.flag} {cc.label} ({cc.code})
                </MenuItem>
              ))}
            </Select>
          </InputAdornment>
        ),
      }}
      {...rest}
    />
  );
}
