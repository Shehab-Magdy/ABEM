import { useEffect, useState, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import {
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
} from "@mui/material";
import { Warning } from "@mui/icons-material";
import { useAuthStore } from "../contexts/authStore";
import axios from "axios";

const WARNING_SECONDS = 30;
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

/**
 * Decode the JWT payload and return the `exp` claim in milliseconds.
 * Returns null if the token is missing or malformed.
 */
function getTokenExpiry(token) {
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

/**
 * NF-05 -- Session expiry warning modal.
 *
 * 30 seconds before the JWT access token expires a non-dismissible dialog is
 * shown with a live countdown.  The user can extend the session (refresh the
 * token) or log out immediately.  When the countdown reaches 0 the user is
 * automatically logged out and redirected to /login.
 *
 * Rendered as a React portal on document.body so it sits above every other
 * layer, including the tutorial overlay.
 */
export default function SessionExpiryModal() {
  const { t } = useTranslation("common");
  const { accessToken, refreshToken, setTokens, logout } = useAuthStore();

  const [showModal, setShowModal] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(WARNING_SECONDS);

  const timerRef = useRef(null);
  const countdownRef = useRef(null);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleLogout = useCallback(() => {
    setShowModal(false);
    clearInterval(countdownRef.current);
    clearTimeout(timerRef.current);
    logout();
    window.location.replace("/login");
  }, [logout]);

  const handleExtend = useCallback(async () => {
    try {
      const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, {
        refresh: refreshToken,
      });
      setTokens(data.access, refreshToken);
      setShowModal(false);
      clearInterval(countdownRef.current);
      // The useEffect watching accessToken will re-schedule the next warning.
    } catch {
      handleLogout();
    }
  }, [refreshToken, setTokens, handleLogout]);

  // ── Schedule the warning when accessToken changes ────────────────────────

  useEffect(() => {
    if (!accessToken) {
      setShowModal(false);
      return;
    }

    const expiry = getTokenExpiry(accessToken);
    if (!expiry) return;

    const now = Date.now();
    const msUntilWarning = expiry - now - WARNING_SECONDS * 1000;

    if (msUntilWarning <= 0) {
      // Already inside the warning window (or expired).
      if (expiry <= now) {
        handleLogout();
        return;
      }
      const remaining = Math.max(0, Math.ceil((expiry - now) / 1000));
      setSecondsLeft(remaining);
      setShowModal(true);
    } else {
      timerRef.current = setTimeout(() => {
        setSecondsLeft(WARNING_SECONDS);
        setShowModal(true);
      }, msUntilWarning);
    }

    return () => {
      clearTimeout(timerRef.current);
      clearInterval(countdownRef.current);
    };
  }, [accessToken, handleLogout]);

  // ── Countdown tick ───────────────────────────────────────────────────────

  useEffect(() => {
    if (!showModal) return;

    countdownRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(countdownRef.current);
          handleLogout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(countdownRef.current);
  }, [showModal, handleLogout]);

  // ── Render ───────────────────────────────────────────────────────────────

  if (!showModal) return null;

  return createPortal(
    <Dialog
      open
      disableEscapeKeyDown
      onClose={(_event, reason) => {
        // Block backdrop clicks -- the modal is non-dismissible.
        if (reason === "backdropClick") return;
      }}
      sx={{ zIndex: 99999 }}
      PaperProps={{ sx: { borderRadius: 3, p: 1 } }}
    >
      <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Warning color="warning" />
        {t("session_expiring_title", "Session Expiring")}
      </DialogTitle>

      <DialogContent>
        <Typography variant="body1" sx={{ mb: 2 }}>
          {t(
            "session_expiring_message",
            "Your session is about to expire. You will be logged out automatically.",
          )}
        </Typography>

        <Typography
          variant="h3"
          align="center"
          color="warning.main"
          fontWeight={700}
          sx={{ mb: 3 }}
        >
          {secondsLeft}
        </Typography>

        <Stack direction="row" spacing={2} justifyContent="center">
          <Button variant="contained" color="primary" onClick={handleExtend}>
            {t("extend_session", "Extend Session")}
          </Button>
          <Button variant="outlined" color="error" onClick={handleLogout}>
            {t("log_out", "Log Out")}
          </Button>
        </Stack>
      </DialogContent>
    </Dialog>,
    document.body,
  );
}
