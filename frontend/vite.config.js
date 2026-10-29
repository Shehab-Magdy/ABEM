import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["abem-app-icon.svg", "apple-touch-icon.png", "favicon-16x16.png", "favicon-32x32.png", "favicon.ico"],
      manifest: {
        id: "/",
        name: "عِمارة.كوم - إدارة اتحاد الملاك",
        short_name: "عِمارة.كوم",
        description: "تطبيق إدارة اتحاد الملاك، تحصيل الاشتراكات ومتابعة مصاريف العمارة والخزينة.",
        lang: "ar",
        dir: "rtl",
        start_url: "/",
        scope: "/",
        display: "standalone",
        theme_color: "#254A80",
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
