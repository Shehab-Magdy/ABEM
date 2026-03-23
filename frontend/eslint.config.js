import js from "@eslint/js";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";

export default [
  js.configs.recommended,
  {
    files: ["src/**/*.{js,jsx}"],
    plugins: {
      react: reactPlugin,
      "react-hooks": reactHooksPlugin,
    },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        // Browser globals
        window: "readonly",
        document: "readonly",
        console: "readonly",
        navigator: "readonly",
        localStorage: "readonly",
        sessionStorage: "readonly",
        fetch: "readonly",
        URL: "readonly",
        URLSearchParams: "readonly",
        FormData: "readonly",
        Blob: "readonly",
        File: "readonly",
        FileReader: "readonly",
        AbortController: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        requestAnimationFrame: "readonly",
        HTMLInputElement: "readonly",
        Event: "readonly",
        MutationObserver: "readonly",
        IntersectionObserver: "readonly",
        ResizeObserver: "readonly",
        CustomEvent: "readonly",
        atob: "readonly",
        btoa: "readonly",
        structuredClone: "readonly",
        // Vite / Node globals used in config
        process: "readonly",
      },
    },
    rules: {
      // React rules
      "react/jsx-uses-react": "off", // Not needed with React 18 JSX transform
      "react/react-in-jsx-scope": "off", // Not needed with React 18 JSX transform
      "react/prop-types": "off",
      "react/display-name": "off",

      // React Hooks rules
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",

      // General rules
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "no-console": "off",
    },
    settings: {
      react: { version: "detect" },
    },
  },
  {
    ignores: ["node_modules/**", "build/**", "dist/**", "public/**"],
  },
];
