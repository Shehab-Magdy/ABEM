import { createTheme } from "@mui/material/styles";
import { arEG as coreArEG } from "@mui/material/locale";
import { arSD as gridArSD } from "@mui/x-data-grid/locales";

const lightPalette = {
  mode: "light",
  primary: {
    main: "#1E3A8A", // Deep Cobalt
    light: "#3B82F6",
    dark: "#1E40AF",
  },
  secondary: {
    main: "#10B981", // Mint Green
    light: "#34D399",
    dark: "#059669",
  },
  error: { main: "#EF4444" }, // Alert Crimson
  warning: { main: "#F59E0B" },
  success: { main: "#10B981" },
  background: {
    default: "#F3F4F6", // Soft Light Gray
    paper: "#FFFFFF", // Pure White
  },
  text: {
    primary: "#1E293B", // Slate Gray
    secondary: "#64748B",
  },
};

const darkPalette = {
  mode: "dark",
  primary: {
    main: "#3B82F6", // Electric Blue
    light: "#60A5FA",
    dark: "#2563EB",
  },
  secondary: {
    main: "#10B981",
    light: "#34D399",
    dark: "#059669",
  },
  error: { main: "#EF4444" },
  warning: { main: "#F59E0B" },
  success: { main: "#10B981" },
  background: {
    default: "#0F172A", // Deep Charcoal
    paper: "#0F172A", // Changed to match
  },
  text: {
    primary: "#F8FAFC", // Off-White
    secondary: "#CBD5E1",
  },
};

const sharedComponents = (mode) => ({
  MuiButton: {
    styleOverrides: {
      root: { 
        textTransform: "none", 
        fontWeight: 600,
        minHeight: 44, // Touch target
        minWidth: 44,
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: { 
        boxShadow: mode === 'dark' ? "0 2px 12px rgba(0,0,0,0.3)" : "0 2px 12px rgba(0,0,0,0.08)",
        minHeight: 44, // Touch target
      },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: { 
        boxShadow: mode === 'dark' ? "0 1px 4px rgba(0,0,0,0.5)" : "0 1px 4px rgba(0,0,0,0.12)",
        backdropFilter: "blur(10px)",
        backgroundColor: mode === 'dark' ? "rgba(30, 41, 59, 0.8)" : "rgba(255, 255, 255, 0.8)",
      },
    },
  },
  MuiBottomNavigation: {
    styleOverrides: {
      root: {
        backdropFilter: "blur(10px)",
        backgroundColor: mode === 'dark' ? "rgba(30, 41, 59, 0.8)" : "rgba(255, 255, 255, 0.8)",
      },
    },
  },
  MuiTableHead: {
    styleOverrides: {
      root: {
        backgroundColor: mode === 'dark' ? '#0F172A' : '#FFFFFF',
        '& .MuiTableCell-head': {
          color: mode === 'dark' ? "#F8FAFC" : "#1E293B",
          fontWeight: 600,
        },
      },
    },
  },
});

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

export const createLTRTheme = (mode) => createTheme({
  direction: "ltr",
  palette: mode === 'dark' ? darkPalette : lightPalette,
  typography: ltrTypography,
  shape: sharedShape,
  components: sharedComponents(mode),
});

export const createRTLTheme = (mode) => createTheme(
  {
    direction: "rtl",
    palette: mode === 'dark' ? darkPalette : lightPalette,
    typography: rtlTypography,
    shape: sharedShape,
    components: sharedComponents(mode),
  },
  coreArEG,
  gridArSD,
);

// Default export for backward compatibility
export default createLTRTheme('light');
