/**
 * Global auth state using Zustand.
 *
 * Tokens are cookie-based now (httponly `refresh_token` + `trusted_device`
 * cookies set by the backend — invisible to JS). There is no refresh token
 * on the client any more. The in-memory `accessToken` does NOT survive a
 * hard page reload by design (it must come from a fresh `/auth/refresh/`
 * call so a revoked/rotated session can't resurrect a stale token).
 *
 * `user` is persisted to localStorage purely for faster perceived load on
 * boot (it's non-secret profile display data, not a credential) — it gets
 * overwritten by the server response as soon as any request completes.
 *
 * `abem-has-session` is a separate non-secret boolean flag (NOT inside the
 * zustand-persisted blob) that records whether we believe the browser holds
 * a `refresh_token` cookie. The app uses it on boot to decide whether a
 * silent `/auth/refresh/` call is worth attempting at all — an anonymous
 * visitor with no flag skips straight past that doomed network request.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

const HAS_SESSION_KEY = "abem-has-session";

export function markHasSession() {
  try {
    localStorage.setItem(HAS_SESSION_KEY, "1");
  } catch {
    // localStorage unavailable (private mode, quota, etc.) — non-fatal.
  }
}

export function clearHasSession() {
  try {
    localStorage.removeItem(HAS_SESSION_KEY);
  } catch {
    // ignore
  }
}

export function hadSession() {
  try {
    return localStorage.getItem(HAS_SESSION_KEY) === "1";
  } catch {
    return false;
  }
}

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      accessToken: null,

      setAccessToken: (accessToken) => set({ accessToken }),

      setUser: (user) => set({ user }),

      // Called after otp/verify, google/, or a trusted-device-bypass response.
      login: (user, accessToken) => {
        markHasSession();
        set({ user, accessToken });
      },

      logout: () => {
        clearHasSession();
        set({ user: null, accessToken: null });
      },
    }),
    {
      name: "abem-auth",
      // Only `user` survives a reload; accessToken is always re-fetched via
      // a silent refresh (see App.jsx bootstrap) so a stale/revoked token
      // can never be replayed from localStorage.
      partialize: (state) => ({ user: state.user }),
    }
  )
);
