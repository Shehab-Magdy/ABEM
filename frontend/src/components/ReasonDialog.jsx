import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from "@mui/material";

/**
 * Asks for a short reason, then confirms an action (waive a fee, reject a request ...).
 * `onConfirm(reason)` may be async; a thrown error is shown inside the dialog.
 */
export default function ReasonDialog({ open, title, description, label, confirmLabel, color = "primary", required = false, onClose, onConfirm }) {
  const { t } = useTranslation("common");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open) {
      setReason("");
      setError(null);
    }
  }, [open]);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await onConfirm(reason.trim());
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
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          {description && <Typography variant="body2" color="text.secondary">{description}</Typography>}
          <TextField autoFocus label={label} value={reason} onChange={(e) => setReason(e.target.value)} inputProps={{ maxLength: 200 }} multiline minRows={2} />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" color={color} onClick={submit} disabled={busy || (required && !reason.trim())} sx={{ minHeight: 44 }}>
          {busy ? <CircularProgress size={22} color="inherit" /> : confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
