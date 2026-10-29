/**
 * Resolves the effective colour mode and keeps it in sync with the user's
 * server-side preferred_theme (mirrors usePreferredLanguage).
 */
import { useEffect, useState } from "react";
import { useAuthStore } from "../contexts/authStore";
import { useThemeStore } from "../contexts/themeStore";

const MODES = ["light", "dark", "system"];

function systemPrefersDark() {
  return typeof window !== "undefined" && !!window.matchMedia?.("(prefers-color-scheme: dark)").matches;
}

export function useSyncPreferredTheme() {
  const preferred = useAuthStore((s) => s.user?.preferred_theme);
  const setMode = useThemeStore((s) => s.setMode);
  useEffect(() => {
    if (MODES.includes(preferred)) setMode(preferred);
  }, [preferred, setMode]);
}

/** @returns {"light"|"dark"} */
export function useResolvedMode() {
  const mode = useThemeStore((s) => s.mode);
  const [dark, setDark] = useState(systemPrefersDark);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return undefined;
    const onChange = (e) => setDark(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return mode === "system" ? (dark ? "dark" : "light") : mode;
}
