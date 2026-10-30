import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Radio, RadioGroup,
  Stack, TextField, Typography,
} from "@mui/material";
import { apartmentsApi } from "../api/apartmentsApi";

const modeOf = (unit) => (unit?.billing_paused ? "paused" : Number(unit?.rate_factor) !== 1 ? "percent" : "full");

/**
 * How one unit pays the monthly subscription: the full amount, a percent of it (50% for a part-time unit,
 * 150% for a shop), or not at all while paused. A reason is kept for anything other than full price.
 */
export default function UnitBillingDialog({ unit, onClose, onSaved }) {
  const { t } = useTranslation("subscription");
  const [mode, setMode] = useState("full");
  const [percent, setPercent] = useState("100");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!unit) return;
    setMode(modeOf(unit));
    setPercent(String(Math.round(Number(unit.rate_factor || 1) * 100)));
    setReason(unit.billing_pause_reason || "");
    setError(null);
  }, [unit]);

  const pct = Number(percent);
  const percentOk = mode !== "percent" || (pct >= 10 && pct <= 1000);

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      await apartmentsApi.update(unit.id, {
        billing_paused: mode === "paused",
        rate_factor: mode === "percent" ? (pct / 100).toFixed(2) : mode === "full" ? "1.00" : unit.rate_factor,
        billing_pause_reason: mode === "full" ? "" : reason.trim(),
      });
      onSaved();
    } catch (err) {
      const d = err.response?.data;
      setError(d?.detail || Object.values(d?.errors ?? {}).flat().join(" ") || t("error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={!!unit} onClose={busy ? undefined : onClose} fullWidth maxWidth="xs">
      <DialogTitle>{t("billing_for_unit", { unit: unit?.unit_number })}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <RadioGroup value={mode} onChange={(e) => setMode(e.target.value)}>
            <FormControlLabel value="full" control={<Radio />} label={t("mode_full")} />
            <FormControlLabel value="percent" control={<Radio />} label={t("mode_percent")} />
            <FormControlLabel value="paused" control={<Radio />} label={t("mode_paused")} />
          </RadioGroup>
          {mode === "percent" && (
            <TextField type="number" label={t("percent_of_subscription")} helperText={t("percent_help")} value={percent}
              onChange={(e) => setPercent(e.target.value)} inputProps={{ min: 10, max: 1000, step: 5 }} error={!percentOk} />
          )}
          {mode !== "full" && (
            <TextField label={t("billing_reason")} value={reason} onChange={(e) => setReason(e.target.value)} inputProps={{ maxLength: 200 }} multiline minRows={2} />
          )}
          <Typography variant="caption" color="text.secondary">{t(`mode_${mode}_help`)}</Typography>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" onClick={save} disabled={busy || !percentOk} sx={{ minHeight: 44 }}>
          {busy ? <CircularProgress size={22} color="inherit" /> : t("save")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
