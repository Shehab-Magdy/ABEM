import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from "@mui/material";

/** "Are you sure?" for destructive actions. `onConfirm` may be async; an error stays inside the dialog. */
export default function ConfirmDialog({ open, title, text, confirmLabel, color = "error", onClose, onConfirm }) {
  const { t } = useTranslation("common");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      await onConfirm();
    } catch (err) {
      setError(err?.response?.data?.detail || t("something_went_wrong"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="xs">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}
        <DialogContentText>{text}</DialogContentText>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" color={color} onClick={run} disabled={busy} sx={{ minHeight: 44 }}>
          {busy ? <CircularProgress size={22} color="inherit" /> : confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
