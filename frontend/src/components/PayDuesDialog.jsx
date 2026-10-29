import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Box, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle,
  IconButton, MenuItem, Stack, TextField, Tooltip, Typography,
} from "@mui/material";
import { Check, ContentCopy } from "@mui/icons-material";
import { apartmentsApi } from "../api/apartmentsApi";
import { buildingsApi } from "../api/buildingsApi";
import { paymentsApi } from "../api/paymentsApi";
import { formatCurrency } from "../utils/formatters";

const dueOf = (unit) => Math.max(parseFloat(unit?.balance || 0), 0);

/**
 * دفع الاشتراك — InstaPay display-and-confirm.
 * Shows the building's InstaPay address and the amount due; the resident transfers in their
 * banking app, then taps "تم الدفع". The building admin confirms before the balance changes.
 */
export default function PayDuesDialog({ open, onClose }) {
  const { t } = useTranslation("payments");
  const [units, setUnits] = useState([]);
  const [instapay, setInstapay] = useState({});
  const [unitId, setUnitId] = useState("");
  const [amount, setAmount] = useState("");
  const [reference, setReference] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!open) return;
    setSent(false);
    setError(null);
    (async () => {
      try {
        const [u, b] = await Promise.all([apartmentsApi.list({ page_size: 50 }), buildingsApi.list({ page_size: 50 })]);
        const list = u.data?.results ?? u.data ?? [];
        setUnits(list);
        setInstapay(Object.fromEntries((b.data?.results ?? b.data ?? []).map((x) => [x.id, x.instapay_address])));
        if (list[0]) {
          setUnitId(list[0].id);
          setAmount(dueOf(list[0]) || "");
        }
      } catch {
        setError(t("pay_load_error"));
      }
    })();
  }, [open, t]);

  const unit = units.find((x) => x.id === unitId);
  const address = unit ? instapay[unit.building_id] : "";

  const copy = () => {
    try {
      navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable: the address is still shown */
    }
  };

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      await paymentsApi.createClaim({ apartment_id: unitId, amount, reference });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || t("pay_send_error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>{t("pay_dues")}</DialogTitle>
      <DialogContent>
        {sent ? (
          <Alert severity="success">{t("pay_sent")}</Alert>
        ) : (
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            {units.length > 1 && (
              <TextField
                select
                label={t("pay_unit")}
                value={unitId}
                onChange={(e) => {
                  setUnitId(e.target.value);
                  setAmount(dueOf(units.find((x) => x.id === e.target.value)) || "");
                }}
              >
                {units.map((x) => <MenuItem key={x.id} value={x.id}>{x.unit_number}</MenuItem>)}
              </TextField>
            )}
            {unit && (
              <Typography variant="body2" color="text.secondary">
                {t("pay_amount_due")}: <strong>{formatCurrency(dueOf(unit))}</strong>
              </Typography>
            )}
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: "action.hover" }}>
              <Typography variant="caption" color="text.secondary">{t("pay_instapay_address")}</Typography>
              {address ? (
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Typography variant="h6" fontWeight={700} sx={{ wordBreak: "break-all" }}>{address}</Typography>
                  <Tooltip title={t("pay_copy")}>
                    <IconButton onClick={copy} aria-label={t("pay_copy")}>{copied ? <Check color="success" /> : <ContentCopy />}</IconButton>
                  </Tooltip>
                </Stack>
              ) : (
                <Typography>{t("pay_no_address")}</Typography>
              )}
              <Typography variant="caption" color="text.secondary">{t("pay_steps")}</Typography>
            </Box>
            <TextField label={t("pay_amount_sent")} type="number" value={amount} onChange={(e) => setAmount(e.target.value)} inputProps={{ step: "0.01", min: 0 }} />
            <TextField label={t("pay_reference")} value={reference} onChange={(e) => setReference(e.target.value)} />
          </Stack>
        )}
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} sx={{ minHeight: 44 }}>{t("pay_close")}</Button>
        {!sent && (
          <Button variant="contained" onClick={submit} disabled={loading || !unitId || !(parseFloat(amount) > 0)} sx={{ minHeight: 44 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : t("pay_done")}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
