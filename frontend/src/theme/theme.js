import { createTheme } from "@mui/material/styles";
import { arEG as coreArEG } from "@mui/material/locale";
import { arSD as gridArSD } from "@mui/x-data-grid/locales";

// Tokens mirror branding/design-tokens.json (عِمارة.كوم / 3maracom).
const navy = {
  50: "#EEF3FA",
  100: "#D9E4F3",
  200: "#B3C8E6",
  300: "#85A5D2",
  400: "#5680BA",
  500: "#345F9C",
  600: "#254A80",
  700: "#1C3B67",
  800: "#152D4F",
  900: "#0E1F38",
};
const terracotta = {
  50: "#FDF3EE",
  100: "#FAE1D3",
  200: "#F4C2A6",
  300: "#EC9C73",
  400: "#E27A4A",
  500: "#D2602F",
  600: "#B84C22",
  700: "#953C1C",
  800: "#732F19",
  900: "#4F2113",
};
const neutral = {
  0: "#FFFFFF",
  50: "#F6F7F9",
  100: "#EDEFF3",
  200: "#DDE1E8",
  300: "#C3C9D4",
  400: "#98A1B1",
  500: "#6B7589",
  600: "#525B6E",
  700: "#3B4354",
  800: "#262C3A",
  900: "#161B26",
  950: "#0C1018",
};

const palettes = {
  light: {
    mode: "light",
    primary: {
      main: navy[600],
      light: navy[100],
      dark: navy[800],
      contrastText: "#fff",
    },
    secondary: {
      main: terracotta[600],
      light: terracotta[100],
      dark: terracotta[700],
      contrastText: "#fff",
    },
    success: {
      main: "#15803D",
      light: "#DCFCE7",
      dark: "#166534",
      contrastText: "#fff",
    },
    warning: {
      main: "#B45309",
      light: "#FEF3C7",
      dark: "#92400E",
      contrastText: "#fff",
    },
    error: {
      main: "#B91C1C",
      light: "#FEE2E2",
      dark: "#991B1B",
      contrastText: "#fff",
    },
    info: {
      main: "#0369A1",
      light: "#E0F2FE",
      dark: "#075985",
      contrastText: "#fff",
    },
    background: { default: neutral[50], paper: neutral[0] },
    text: {
      primary: neutral[900],
      secondary: neutral[600],
      disabled: neutral[400],
    },
    divider: neutral[200],
  },
  dark: {
    mode: "dark",
    primary: {
      main: navy[300],
      light: navy[200],
      dark: navy[500],
      contrastText: neutral[950],
    },
    secondary: {
      main: terracotta[400],
      light: terracotta[300],
      dark: terracotta[500],
      contrastText: neutral[950],
    },
    success: {
      main: "#4ADE80",
      light: "#86EFAC",
      dark: "#15803D",
      contrastText: neutral[950],
    },
    warning: {
      main: "#FBBF24",
      light: "#FCD34D",
      dark: "#B45309",
      contrastText: neutral[950],
    },
    error: {
      main: "#F87171",
      light: "#FCA5A5",
      dark: "#B91C1C",
      contrastText: neutral[950],
    },
    info: {
      main: "#38BDF8",
      light: "#7DD3FC",
      dark: "#0369A1",
      contrastText: neutral[950],
    },
    background: { default: "#0F1623", paper: "#172033" },
    text: { primary: "#F4F6FA", secondary: "#B4BCCB", disabled: "#8791A5" },
    divider: "#2B3750",
  },
};

const buildComponents = (mode) => ({
  MuiButton: {
    styleOverrides: {
      root: { textTransform: "none", fontWeight: 600 },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        boxShadow:
          mode === "light"
            ? "0 2px 8px -2px rgba(22,27,38,0.08), 0 1px 2px rgba(22,27,38,0.04)"
            : "none",
        // dark mode uses tonal elevation instead of shadows
        ...(mode === "dark" && { border: "1px solid #2B3750" }),
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      // MUI dark mode overlays a white gradient on Paper; keep our navy surfaces flat.
      root: { backgroundImage: "none" },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: { boxShadow: "0 1px 2px rgba(22,27,38,0.10)" },
    },
  },
});

const sharedShape = { borderRadius: 10 };

// Arabic glyphs need taller line boxes than Latin to avoid clipping diacritics.
const buildTypography = (rtl) => {
  const lh = rtl
    ? {
        caption: 1.8,
        body2: 1.85,
        body1: 1.9,
        h6: 1.7,
        h5: 1.6,
        h4: 1.55,
        h3: 1.5,
        h2: 1.45,
        h1: 1.4,
      }
    : {
        caption: 1.5,
        body2: 1.57,
        body1: 1.6,
        h6: 1.4,
        h5: 1.33,
        h4: 1.29,
        h3: 1.22,
        h2: 1.2,
        h1: 1.17,
      };
  return {
    fontFamily: rtl
      ? "'Cairo', 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, Arial, sans-serif"
      : "'Inter', 'Cairo', system-ui, sans-serif",
    h1: { fontSize: "3rem", fontWeight: 700, lineHeight: lh.h1 }, // Display: treasury balance
    h2: { fontSize: "2.25rem", fontWeight: 700, lineHeight: lh.h2 },
    h3: { fontSize: "1.75rem", fontWeight: 700, lineHeight: lh.h3 },
    h4: { fontSize: "1.5rem", fontWeight: 700, lineHeight: lh.h4 },
    h5: { fontSize: "1.25rem", fontWeight: 600, lineHeight: lh.h5 },
    h6: { fontSize: "1.125rem", fontWeight: 600, lineHeight: lh.h6 },
    subtitle1: { fontWeight: 500, lineHeight: lh.body1 },
    body1: { fontSize: "1rem", lineHeight: lh.body1 },
    body2: { fontSize: "0.875rem", lineHeight: lh.body2 },
    caption: { fontSize: "0.75rem", lineHeight: lh.caption },
    button: { textTransform: "none" },
  };
};

const build = (mode, direction, ...locales) =>
  createTheme(
    {
      direction,
      palette: palettes[mode],
      typography: buildTypography(direction === "rtl"),
      shape: sharedShape,
      components: buildComponents(mode),
    },
    ...locales,
  );

export const ltrTheme = build("light", "ltr");

// RTL theme merges MUI Arabic locale packs for:
// - Core components (TablePagination "Rows per page", etc.)
// - DataGrid (column menu, filter, pagination labels)
// - DatePicker (month/day names)
export const rtlTheme = build("light", "rtl", coreArEG, gridArSD);

// Dark variants (not yet selected anywhere; wire to a mode toggle in App.jsx).
export const ltrDarkTheme = build("dark", "ltr");
export const rtlDarkTheme = build("dark", "rtl", coreArEG, gridArSD);

// Default export for backward compatibility
export default ltrTheme;
