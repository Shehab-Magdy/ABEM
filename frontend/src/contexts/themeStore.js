/**
 * Colour-mode preference ("light" | "dark" | "system").
 * Cached in localStorage for instant paint; the server copy
 * (user.preferred_theme) wins after login and syncs across devices.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useThemeStore = create(
  persist(
    (set) => ({
      mode: "system",
      setMode: (mode) => set({ mode }),
    }),
    { name: "abem-theme" }
  )
);
