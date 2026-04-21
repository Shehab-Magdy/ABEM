/**
 * Global auth state using Zustand.
 * Persists tokens to localStorage for session continuity.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      theme: 'light', // default

      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken }),

      setUser: (user) => set({ user, theme: user?.theme_preference || 'light' }),

      setTheme: (theme) => set({ theme }),

      login: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken, theme: user?.theme_preference || 'light' }),

      logout: () =>
        set({ user: null, accessToken: null, refreshToken: null, theme: 'light' }),
    }),
    {
      name: "abem-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        theme: state.theme,
      }),
    }
  )
);
