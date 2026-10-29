// Drop into tailwind.config.js. Requires Tailwind >= 3.3 (logical utilities: ms-*, me-*, ps-*, pe-*, text-start).
// Theme colors are CSS variables so light/dark switch by toggling the `dark` class on <html>.
// Add the :root / .dark variable block (below) to your global CSS.

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#EEF3FA", 100: "#D9E4F3", 200: "#B3C8E6", 300: "#85A5D2", 400: "#5680BA",
          500: "#345F9C", 600: "#254A80", 700: "#1C3B67", 800: "#152D4F", 900: "#0E1F38",
          DEFAULT: "#254A80",
        },
        accent: {
          50: "#FDF3EE", 100: "#FAE1D3", 200: "#F4C2A6", 300: "#EC9C73", 400: "#E27A4A",
          500: "#D2602F", 600: "#B84C22", 700: "#953C1C", 800: "#732F19", 900: "#4F2113",
          DEFAULT: "#B84C22",
        },
        success: { 50: "#F0FDF4", 100: "#DCFCE7", 500: "#22C55E", 600: "#16A34A", 700: "#15803D", 800: "#166534", DEFAULT: "#15803D" },
        warning: { 50: "#FFFBEB", 100: "#FEF3C7", 500: "#F59E0B", 600: "#D97706", 700: "#B45309", 800: "#92400E", DEFAULT: "#B45309" },
        danger:  { 50: "#FEF2F2", 100: "#FEE2E2", 500: "#EF4444", 600: "#DC2626", 700: "#B91C1C", 800: "#991B1B", DEFAULT: "#B91C1C" },
        info:    { 50: "#F0F9FF", 100: "#E0F2FE", 500: "#0EA5E9", 600: "#0284C7", 700: "#0369A1", 800: "#075985", DEFAULT: "#0369A1" },
        neutral: {
          50: "#F6F7F9", 100: "#EDEFF3", 200: "#DDE1E8", 300: "#C3C9D4", 400: "#98A1B1",
          500: "#6B7589", 600: "#525B6E", 700: "#3B4354", 800: "#262C3A", 900: "#161B26", 950: "#0C1018",
        },
        // Semantic, theme-aware (use these in components)
        app:      "rgb(var(--c-bg) / <alpha-value>)",
        surface:  { DEFAULT: "rgb(var(--c-surface) / <alpha-value>)", raised: "rgb(var(--c-surface-raised) / <alpha-value>)" },
        line:     "rgb(var(--c-border) / <alpha-value>)",
        heading:  "rgb(var(--c-heading) / <alpha-value>)",
        body:     "rgb(var(--c-body) / <alpha-value>)",
        muted:    "rgb(var(--c-muted) / <alpha-value>)",
        brand:    "rgb(var(--c-brand) / <alpha-value>)",
        action:   { DEFAULT: "rgb(var(--c-action) / <alpha-value>)", hover: "rgb(var(--c-action-hover) / <alpha-value>)", on: "rgb(var(--c-on-action) / <alpha-value>)" },
      },
      fontFamily: {
        // Arabic first: Cairo covers Latin glyphs too, but Inter wins for English runs via unicode-range ordering below.
        sans: ["Inter", "Cairo", "IBM Plex Sans Arabic", "system-ui", "sans-serif"],
        arabic: ["Cairo", "IBM Plex Sans Arabic", "Segoe UI", "Tahoma", "sans-serif"],
        latin: ["Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        // [size, { lineHeight (Latin), fontWeight }] — Arabic needs the larger `ar-*` line heights
        micro:   ["0.6875rem", { lineHeight: "1.5",  fontWeight: "500", letterSpacing: "0.02em" }],
        caption: ["0.75rem",   { lineHeight: "1.5" }],
        "body-sm": ["0.875rem", { lineHeight: "1.57" }],
        body:    ["1rem",      { lineHeight: "1.6" }],
        "body-lg": ["1.125rem", { lineHeight: "1.6" }],
        title:   ["1.25rem",   { lineHeight: "1.4",  fontWeight: "600" }],
        h3:      ["1.5rem",    { lineHeight: "1.33", fontWeight: "700" }],
        h2:      ["1.75rem",   { lineHeight: "1.29", fontWeight: "700" }],
        h1:      ["2.25rem",   { lineHeight: "1.22", fontWeight: "700" }],
        display: ["3rem",      { lineHeight: "1.17", fontWeight: "700", letterSpacing: "-0.01em" }],
      },
      lineHeight: {
        "ar-caption": "1.8", "ar-body-sm": "1.85", "ar-body": "1.9", "ar-title": "1.7",
        "ar-h3": "1.6", "ar-h2": "1.55", "ar-h1": "1.5", "ar-display": "1.4",
      },
      borderRadius: { sm: "6px", md: "10px", lg: "12px", xl: "20px" },
      boxShadow: {
        micro: "0 1px 2px 0 rgb(22 27 38 / 0.06)",
        card:  "0 2px 8px -2px rgb(22 27 38 / 0.08), 0 1px 2px 0 rgb(22 27 38 / 0.04)",
        float: "0 12px 28px -8px rgb(14 31 56 / 0.12)",
        focus: "0 0 0 3px rgb(86 128 186 / 0.45)",
      },
    },
  },
  plugins: [],
};

/* ---- Global CSS (index.css) ----
:root {                      // light
  --c-bg: 246 247 249;  --c-surface: 255 255 255;  --c-surface-raised: 255 255 255;
  --c-border: 221 225 232;  --c-heading: 22 27 38;  --c-body: 82 91 110;  --c-muted: 107 117 137;
  --c-brand: 37 74 128;  --c-action: 184 76 34;  --c-action-hover: 149 60 28;  --c-on-action: 255 255 255;
}
.dark {                      // midnight navy
  --c-bg: 15 22 35;  --c-surface: 23 32 51;  --c-surface-raised: 31 42 64;
  --c-border: 43 55 80;  --c-heading: 244 246 250;  --c-body: 180 188 203;  --c-muted: 135 145 165;
  --c-brand: 133 165 210;  --c-action: 226 122 74;  --c-action-hover: 236 156 115;  --c-on-action: 12 16 24;
}
html:lang(ar) body { font-family: theme('fontFamily.arabic'); line-height: 1.9; }
.num { font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }  // balances, tables
---------------------------------- */
