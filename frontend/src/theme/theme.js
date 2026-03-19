import { createTheme } from "@mui/material/styles";
import { arEG as coreArEG } from "@mui/material/locale";
import { arSD as gridArSD } from "@mui/x-data-grid/locales";

const sharedPalette = {
  mode: "light",
  primary: {
    main: "#2563EB",
    light: "#DBEAFE",
    dark: "#1D4ED8",
  },
  secondary: {
    main: "#10B981",
    light: "#D1FAE5",
    dark: "#059669",
  },
  error: { main: "#EF4444" },
  warning: { main: "#F59E0B" },
  success: { main: "#10B981" },
  background: {
    default: "#F9FAFB",
    paper: "#FFFFFF",
  },
  text: {
    primary: "#1F2937",
    secondary: "#6B7280",
  },
};

const sharedComponents = {
  MuiButton: {
    styleOverrides: {
      root: { textTransform: "none", fontWeight: 600 },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: { boxShadow: "0 2px 12px rgba(0,0,0,0.08)" },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: { boxShadow: "0 1px 4px rgba(0,0,0,0.12)" },
    },
  },
};

const sharedShape = { borderRadius: 10 };

const ltrTypography = {
  fontFamily: "'Inter', sans-serif",
  h4: { fontWeight: 700 },
  h5: { fontWeight: 600 },
  h6: { fontWeight: 600 },
  subtitle1: { fontWeight: 500 },
};

const rtlTypography = {
  fontFamily: "'Cairo', 'Segoe UI', Tahoma, Arial, sans-serif",
  h4: { fontWeight: 700 },
  h5: { fontWeight: 600 },
  h6: { fontWeight: 600 },
  subtitle1: { fontWeight: 500 },
};

export const ltrTheme = createTheme({
  direction: "ltr",
  palette: sharedPalette,
  typography: ltrTypography,
  shape: sharedShape,
  components: sharedComponents,
});

// RTL theme merges MUI Arabic locale packs for:
// - Core components (TablePagination "Rows per page", etc.)
// - DataGrid (column menu, filter, pagination labels)
// - DatePicker (month/day names)
export const rtlTheme = createTheme(
  {
    direction: "rtl",
    palette: sharedPalette,
    typography: rtlTypography,
    shape: sharedShape,
    components: sharedComponents,
  },
  coreArEG,
  gridArSD,
);

// Default export for backward compatibility
export default ltrTheme;
