import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1565C0",       // Deep blue
      light: "#1E88E5",
      dark: "#0D47A1",
    },
    secondary: {
      main: "#00897B",       // Teal
      light: "#26A69A",
      dark: "#00695C",
    },
    error: { main: "#D32F2F" },
    warning: { main: "#F57C00" },
    success: { main: "#388E3C" },
    background: {
      default: "#F5F7FA",
      paper: "#FFFFFF",
    },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 500 },
  },
  shape: { borderRadius: 10 },
  components: {
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
  },
});

export default theme;
