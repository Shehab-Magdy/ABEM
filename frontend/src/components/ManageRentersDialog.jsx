import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Box, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, IconButton,
  MenuItem, Stack, TextField, Tooltip, Typography,
} from "@mui/material";
import { Check, ContentCopy, PersonRemove, WhatsApp } from "@mui/icons-material";
import { apartmentsApi } from "../api/apartmentsApi";

/**
 * The unit's owner invites a renter (مستأجر) with a one-time link and can end a renter's link later.
 * Renters see the unit's dues, pay, report problems and read the treasury; they cannot invite others.
 */
export default function ManageRentersDialog({ open, onClose, unitId: fixedUnitId }) {
  const { t } = useTranslation("dashboard");
  const [units, setUnits] = useState([]);
  const [unitId, setUnitId] = useState("");
  const [link, setLink] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadUnits = useCallback(async () => {
    try {
      const res = await apartmentsApi.list({ page_size: 500 });
      const all = res.data?.results ?? res.data ?? [];
      // Opened for one unit (admin, from the Buildings screen): show just that unit
      const list = fixedUnitId ? all.filter((u) => u.id === fixedUnitId) : all;
      setUnits(list);
      setUnitId((prev) => (fixedUnitId ? fixedUnitId : prev || list[0]?.id || ""));
    } catch {
      setError(t("renters_load_error"));
    }
  }, [t, fixedUnitId]);

  useEffect(() => {
    if (!open) return;
    setLink(null);
    setError(null);
    loadUnits();
  }, [open, loadUnits]);

  const unit = units.find((u) => u.id === unitId);

  const invite = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apartmentsApi.inviteRenter(unitId);
      setLink(`${window.location.origin}/join/${res.data.token}`);
    } catch (err) {
      setError(err.response?.data?.detail || t("renters_load_error"));
    } finally {
      setLoading(false);
    }
  };

  const remove = async (renterId) => {
    setError(null);
    try {
      await apartmentsApi.removeRenter(unitId, renterId);
      loadUnits();
    } catch (err) {
      setError(err.response?.data?.detail || t("renters_load_error"));
    }
  };

  const copy = () => {
    try {
      navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable: the link is still shown */
    }
  };

  const whatsapp = () => {
    const text = t("renters_whatsapp_text", { unit: unit?.unit_number ?? "", link });
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener");
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>{t("renters_title")}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <Typography variant="body2" color="text.secondary">{t("renters_help")}</Typography>
          {units.length > 1 && (
            <TextField select label={t("renters_unit")} value={unitId} onChange={(e) => { setUnitId(e.target.value); setLink(null); }}>
              {units.map((u) => <MenuItem key={u.id} value={u.id}>{u.unit_number}</MenuItem>)}
            </TextField>
          )}
          {(unit?.renters ?? []).length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>{t("renters_current")}</Typography>
              {unit.renters.map((r) => (
                <Stack key={r.id} direction="row" alignItems="center" justifyContent="space-between">
                  <Typography>{r.name}</Typography>
                  <Tooltip title={t("renters_remove")}>
                    <IconButton color="error" onClick={() => remove(r.id)} aria-label={t("renters_remove")}><PersonRemove /></IconButton>
                  </Tooltip>
                </Stack>
              ))}
            </Box>
          )}
          {link ? (
            <Stack spacing={1}>
              <Alert severity="success">{t("renters_link_ready")}</Alert>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Typography variant="caption" sx={{ wordBreak: "break-all", flex: 1 }}>{link}</Typography>
                <Tooltip title={t("renters_copy")}>
                  <IconButton onClick={copy}>{copied ? <Check color="success" /> : <ContentCopy />}</IconButton>
                </Tooltip>
              </Stack>
              <Button variant="contained" color="success" startIcon={<WhatsApp />} onClick={whatsapp} sx={{ minHeight: 44 }}>
                {t("renters_share")}
              </Button>
            </Stack>
          ) : (
            <Button variant="contained" onClick={invite} disabled={loading || !unitId} sx={{ minHeight: 44 }}>
              {loading ? <CircularProgress size={22} color="inherit" /> : t("renters_invite")}
            </Button>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} sx={{ minHeight: 44 }}>{t("renters_close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
