import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Divider,
  FormControlLabel,
  Link,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { authApi } from "../../api/authApi";

/**
 * Shared email-OTP + Google Sign-In form used by LoginPage, RegisterPage and
 * JoinPage.
 *
 * Flow:
 *  1. Email step — POST /auth/otp/request/. Two possible outcomes:
 *     - {detail} — a code was emailed, advance to the code step.
 *     - {access, user} — the browser already holds a valid `trusted_device`
 *       cookie for this email, so the backend skipped the code entirely.
 *       Treat this exactly like a successful verify.
 *  2. Code step — POST /auth/otp/verify/ {email, code} → {access, user} +
 *     sets refresh_token/trusted_device cookies.
 *  3. Optional "Sign in with Google" button (Google Identity Services) that
 *     posts the credential to /auth/google/ → same {access, user} shape.
 *
 * Props:
 *  - email: if provided, the email field is hidden and a code is requested
 *    for it automatically on mount (used mid-wizard in RegisterPage/JoinPage
 *    where the email was already collected). Otherwise the user types it in.
 *  - onSuccess(user, accessToken): called on any successful login outcome.
 *  - showGoogle: whether to render the Google button + divider (default true;
 *    RegisterPage/JoinPage pass false since the user already picked a name —
 *    Google auto-linking only matches by email and would skip that).
 */

let gisScriptPromise = null;
function loadGoogleIdentityScript() {
  if (gisScriptPromise) return gisScriptPromise;
  gisScriptPromise = new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }
    const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", reject);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = reject;
    document.head.appendChild(script);
  });
  return gisScriptPromise;
}

function mapRequestError(err, t) {
  const status = err.response?.status;
  if (status === 429) return t("too_many_attempts");
  if (status === 403) return t("account_deactivated");
  return err.response?.data?.detail || t("errors:server_error");
}

function mapVerifyError(err, t) {
  const status = err.response?.status;
  const code = err.response?.data?.code;
  if (status === 429 || code === "max_attempts") return t("too_many_attempts");
  if (code === "not_found") return t("code_not_found");
  if (code === "expired") return t("code_expired");
  if (code === "invalid") return t("code_invalid");
  if (status === 403) return t("account_deactivated");
  return err.response?.data?.detail || t("errors:server_error");
}

// Shared "accept Terms of Service / Privacy Policy" checkbox shown when the
// backend reports {code: "terms_required"} — i.e. this is a brand-new
// account (OTP or Google) that hasn't accepted terms yet. Reuses the exact
// copy/links RegisterPage's AccountStep uses for the same checkbox.
function AcceptTermsPrompt({ checked, onChange, error }) {
  const { t, i18n } = useTranslation("auth");
  return (
    <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 1 }}>
      <Typography variant="body2" sx={{ mb: 1 }}>
        {t("terms_required_prompt")}
      </Typography>
      <FormControlLabel
        control={
          <Checkbox checked={checked} onChange={(e) => onChange(e.target.checked)} />
        }
        label={
          <Typography variant="body2">
            {t("accept_terms_prefix")}{" "}
            <Link component={RouterLink} to="/terms" target="_blank" underline="hover">
              {t("terms_link")}
            </Link>
            {" "}{t("and")}{(i18n.language || "").startsWith("ar") ? "" : " "}
            <Link component={RouterLink} to="/privacy" target="_blank" underline="hover">
              {t("privacy_link")}
            </Link>
          </Typography>
        }
      />
      {error && (
        <Typography variant="caption" color="error" display="block">
          {error}
        </Typography>
      )}
    </Box>
  );
}

function mapGoogleError(err, t) {
  const status = err.response?.status;
  if (status === 401) return t("google_signin_failed");
  if (status === 403) return t("account_deactivated");
  if (status === 400) return t("google_not_configured");
  return err.response?.data?.detail || t("errors:server_error");
}

export default function OtpLoginForm({
  email: fixedEmail,
  initialEmail,
  onSuccess,
  showGoogle = true,
  autoFocusEmail = true,
}) {
  const { t } = useTranslation("auth");
  // fixedEmail hides the input and auto-requests a code for it (mid-wizard
  // flows). initialEmail just prefills the editable field (e.g. a ?email=
  // query param on the login page) without auto-submitting anything.
  const [email, setEmail] = useState(fixedEmail || initialEmail || "");
  const [step, setStep] = useState("email"); // "email" | "code"
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  // Brand-new account via OTP that hasn't accepted terms yet (code is still
  // valid/unconsumed — see backend contract on /auth/otp/verify/).
  const [codeNeedsTerms, setCodeNeedsTerms] = useState(false);
  const [codeAcceptTerms, setCodeAcceptTerms] = useState(false);
  const [codeTermsError, setCodeTermsError] = useState(null);
  // Same, for a brand-new account via Google Sign-In. The original id_token
  // is reused for the resubmit (short-lived but valid within its window).
  const [googleNeedsTerms, setGoogleNeedsTerms] = useState(false);
  const [googleAcceptTerms, setGoogleAcceptTerms] = useState(false);
  const [googleTermsError, setGoogleTermsError] = useState(null);
  const pendingGoogleTokenRef = useRef(null);
  const googleBtnRef = useRef(null);
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  const handleLoginResponse = (data) => {
    onSuccess(data.user, data.access);
  };

  const requestCode = async (e, explicitEmail) => {
    e?.preventDefault?.();
    const targetEmail = (explicitEmail ?? email).trim();
    if (!targetEmail) {
      setError(t("email_required"));
      return;
    }
    setError(null);
    setInfo(null);
    setLoading(true);
    try {
      const { data } = await authApi.requestOtp(targetEmail);
      if (data.access) {
        handleLoginResponse(data);
        return;
      }
      setStep("code");
      setInfo(t("code_sent"));
      setCodeNeedsTerms(false);
      setCodeAcceptTerms(false);
      setCodeTermsError(null);
    } catch (err) {
      setError(mapRequestError(err, t));
    } finally {
      setLoading(false);
    }
  };

  // For a fixed email (mid-wizard), request the first code automatically.
  // Guarded against React StrictMode's double-invoke (and any remount) so we
  // never fire two OTP requests for the same email.
  const firedForEmailRef = useRef(null);
  useEffect(() => {
    if (fixedEmail && firedForEmailRef.current !== fixedEmail) {
      firedForEmailRef.current = fixedEmail;
      setEmail(fixedEmail);
      requestCode(undefined, fixedEmail);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fixedEmail]);

  const resendCode = async () => {
    setError(null);
    setInfo(null);
    setResending(true);
    try {
      const { data } = await authApi.requestOtp(email.trim());
      if (data.access) {
        handleLoginResponse(data);
        return;
      }
      setInfo(t("code_sent"));
      setCodeNeedsTerms(false);
      setCodeAcceptTerms(false);
      setCodeTermsError(null);
    } catch (err) {
      setError(mapRequestError(err, t));
    } finally {
      setResending(false);
    }
  };

  const verifyCode = async (e) => {
    e?.preventDefault?.();
    if (!code.trim()) {
      setError(t("code_required"));
      return;
    }
    if (codeNeedsTerms && !codeAcceptTerms) {
      setCodeTermsError(t("accept_terms_required"));
      return;
    }
    setError(null);
    setCodeTermsError(null);
    setLoading(true);
    try {
      const { data } = await authApi.verifyOtp(email.trim(), code.trim(), codeAcceptTerms);
      handleLoginResponse(data);
    } catch (err) {
      if (err.response?.data?.code === "terms_required") {
        // Brand-new account, code is still valid/unconsumed — show the
        // terms checkbox instead of a generic error, keep the entered code.
        setCodeNeedsTerms(true);
      } else {
        setError(mapVerifyError(err, t));
      }
    } finally {
      setLoading(false);
    }
  };

  // ── Google Identity Services ────────────────────────────────────────────
  useEffect(() => {
    if (!showGoogle || !clientId) return;
    let cancelled = false;
    loadGoogleIdentityScript()
      .then(() => {
        if (cancelled || !window.google?.accounts?.id) return;
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: async (response) => {
            setError(null);
            pendingGoogleTokenRef.current = response.credential;
            setGoogleNeedsTerms(false);
            setGoogleAcceptTerms(false);
            setGoogleTermsError(null);
            setLoading(true);
            try {
              const { data } = await authApi.googleLogin(response.credential);
              handleLoginResponse(data);
            } catch (err) {
              if (err.response?.data?.code === "terms_required") {
                // Brand-new Google account — show the terms checkbox; the
                // id_token is still valid to reuse for the resubmit below.
                setGoogleNeedsTerms(true);
              } else {
                setError(mapGoogleError(err, t));
              }
            } finally {
              setLoading(false);
            }
          },
        });
        if (googleBtnRef.current) {
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            theme: "outline",
            size: "large",
            width: 320,
          });
        }
      })
      .catch(() => {
        // GIS failed to load (offline, blocked by an extension, etc.) —
        // the button area simply stays empty; OTP login remains available.
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showGoogle, clientId]);

  // Resubmit the original (still-valid) Google id_token now that the user
  // has checked the terms box, per the backend's terms_required contract.
  const submitGoogleWithTerms = async () => {
    if (!googleAcceptTerms) {
      setGoogleTermsError(t("accept_terms_required"));
      return;
    }
    setGoogleTermsError(null);
    setError(null);
    setLoading(true);
    try {
      const { data } = await authApi.googleLogin(pendingGoogleTokenRef.current, true);
      handleLoginResponse(data);
    } catch (err) {
      setGoogleNeedsTerms(false);
      setError(mapGoogleError(err, t));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack spacing={2.5}>
      {error && <Alert severity="error">{error}</Alert>}
      {info && !error && <Alert severity="success">{info}</Alert>}

      {step === "email" ? (
        <Box component="form" onSubmit={requestCode} noValidate>
          <Stack spacing={2.5}>
            {fixedEmail ? (
              <Typography variant="body2" color="text.secondary">
                {t("using_email", { email: fixedEmail })}
              </Typography>
            ) : (
              <TextField
                label={t("email_address")}
                type="email"
                fullWidth
                autoFocus={autoFocusEmail}
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            )}
            <Button type="submit" variant="contained" size="large" fullWidth disabled={loading}>
              {loading ? <CircularProgress size={24} color="inherit" /> : t("send_code")}
            </Button>
          </Stack>
        </Box>
      ) : (
        <Box component="form" onSubmit={verifyCode} noValidate>
          <Stack spacing={2.5}>
            <Typography variant="body2" color="text.secondary">
              {t("enter_code_sent_to", { email })}
            </Typography>
            <TextField
              label={t("otp_code")}
              fullWidth
              autoFocus
              autoComplete="one-time-code"
              inputMode="numeric"
              inputProps={{ maxLength: 6, style: { letterSpacing: 4, fontFamily: "monospace" } }}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            />
            {codeNeedsTerms && (
              <AcceptTermsPrompt
                checked={codeAcceptTerms}
                onChange={setCodeAcceptTerms}
                error={codeTermsError}
              />
            )}
            <Button type="submit" variant="contained" size="large" fullWidth disabled={loading}>
              {loading ? <CircularProgress size={24} color="inherit" /> : t("verify_code")}
            </Button>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              {!fixedEmail && (
                <Button
                  size="small"
                  onClick={() => {
                    setStep("email");
                    setCode("");
                    setError(null);
                    setInfo(null);
                    setCodeNeedsTerms(false);
                    setCodeAcceptTerms(false);
                    setCodeTermsError(null);
                  }}
                >
                  {t("change_email")}
                </Button>
              )}
              <Button size="small" onClick={resendCode} disabled={resending}>
                {resending ? <CircularProgress size={16} /> : t("resend_code")}
              </Button>
            </Stack>
          </Stack>
        </Box>
      )}

      {showGoogle && (
        <>
          <Divider>
            <Typography variant="caption" color="text.secondary">{t("or_divider")}</Typography>
          </Divider>
          {clientId ? (
            <Box ref={googleBtnRef} display="flex" justifyContent="center" />
          ) : (
            <Typography variant="caption" color="text.secondary" align="center">
              {t("google_signin_unavailable")}
            </Typography>
          )}
          {googleNeedsTerms && (
            <Stack spacing={2}>
              <AcceptTermsPrompt
                checked={googleAcceptTerms}
                onChange={setGoogleAcceptTerms}
                error={googleTermsError}
              />
              <Button
                variant="contained"
                size="large"
                fullWidth
                disabled={loading}
                onClick={submitGoogleWithTerms}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : t("continue")}
              </Button>
            </Stack>
          )}
        </>
      )}
    </Stack>
  );
}
