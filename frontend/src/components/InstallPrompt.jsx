import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, IconButton, Paper, Typography } from "@mui/material";
import { Close, InstallMobile } from "@mui/icons-material";

const DISMISS_KEY = "pwa-install-dismissed";

const isStandalone = () =>
  window.matchMedia?.("(display-mode: standalone)").matches || window.navigator.standalone === true;

const isIos = () =>
  /iphone|ipad|ipod/i.test(window.navigator.userAgent) ||
  (window.navigator.platform === "MacIntel" && window.navigator.maxTouchPoints > 1);

function wasDismissed() {
  try {
    return localStorage.getItem(DISMISS_KEY) === "1";
  } catch {
    return false;
  }
}

/**
 * Floating "install the app" banner.
 * Android/Chrome: uses the captured beforeinstallprompt event (one tap).
 * iOS Safari has no install API, so we show the Share -> Add to Home Screen steps.
 */
export default function InstallPrompt() {
  const { t } = useTranslation("common");
  const [deferred, setDeferred] = useState(null);
  const [showIos, setShowIos] = useState(false);
  const [hidden, setHidden] = useState(wasDismissed());

  useEffect(() => {
    if (isStandalone()) return undefined;
    const onPrompt = (e) => {
      e.preventDefault();
      setDeferred(e);
    };
    const onInstalled = () => setDeferred(null);
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    if (isIos()) setShowIos(true);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const dismiss = () => {
    setHidden(true);
    try {
      localStorage.setItem(DISMISS_KEY, "1");
    } catch {
      /* storage unavailable: dismissal lasts for this visit only */
    }
  };

  const install = async () => {
    if (!deferred) return;
    deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
  };

  if (hidden || (!deferred && !showIos)) return null;

  return (
    <Paper
      elevation={6}
      role="complementary"
      sx={{
        position: "fixed",
        insetInline: 16,
        bottom: "calc(16px + env(safe-area-inset-bottom))",
        zIndex: (theme) => theme.zIndex.snackbar,
        maxWidth: 480,
        mx: "auto",
        p: 1.5,
        display: "flex",
        alignItems: "center",
        gap: 1.5,
      }}
    >
      <InstallMobile color="primary" />
      <Box sx={{ flex: 1 }}>
        {deferred ? (
          <Button variant="contained" fullWidth onClick={install} sx={{ minHeight: 44 }}>
            {t("install_app", "تثبيت التطبيق على هاتفك")}
          </Button>
        ) : (
          <>
            <Typography variant="subtitle2" fontWeight={700}>
              {t("install_app", "تثبيت التطبيق على هاتفك")}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t("install_ios_hint", "اضغط على زر المشاركة ثم «إضافة إلى الشاشة الرئيسية»")}
            </Typography>
          </>
        )}
      </Box>
      <IconButton size="small" onClick={dismiss} aria-label={t("install_dismiss", "إغلاق")}>
        <Close fontSize="small" />
      </IconButton>
    </Paper>
  );
}
