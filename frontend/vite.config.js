import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["abem-app-icon.svg", "apple-touch-icon.png", "favicon-16x16.png", "favicon-32x32.png"],
      manifest: {
        name: "ABEM - Apartment & Building Expense Management",
        short_name: "ABEM",
        description: "Manage buildings, shared expenses and payments.",
        start_url: "/",
        scope: "/",
        display: "standalone",
        theme_color: "#2563EB",
        background_color: "#FFFFFF",
        icons: [
          { src: "/pwa-192x192.png", sizes: "192x192", type: "image/png", purpose: "any" },
          { src: "/pwa-512x512.png", sizes: "512x512", type: "image/png", purpose: "any" },
          { src: "/pwa-maskable-512x512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
          { src: "/abem-app-icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
        ],
      },
      workbox: {
        // App shell only. Never cache API/media responses: they are per-user and per-tenant.
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//, /^\/media\//, /^\/admin\//],
        globPatterns: ["**/*.{js,css,html,svg,woff2}"],
        runtimeCaching: [],
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/media": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
