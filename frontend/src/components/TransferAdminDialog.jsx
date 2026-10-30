import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { buildingsApi } from "../api/buildingsApi";

/** The primary admin hands a building to one of its co-admins (the old admin stays on as co-admin). */
export default function TransferAdminDialog({ building, candidates, onClose, onDone }) {
  const { t } = useTranslation("buildings");
  const [userId, setUserId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      await buildingsApi.transferAdmin(building.id, userId);
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || t("errors:server_error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={!!building} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>{t("handover_title", { name: building?.name })}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <Typography variant="body2">{t("handover_help")}</Typography>
          {candidates.length === 0 ? (
            <Alert severity="info">{t("handover_no_coadmins")}</Alert>
          ) : (
            <TextField select label={t("handover_to")} value={userId} onChange={(e) => setUserId(e.target.value)}>
              {candidates.map((u) => <MenuItem key={u.id} value={u.id}>{u.name}</MenuItem>)}
            </TextField>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" color="warning" disabled={loading || !userId} onClick={submit} sx={{ minHeight: 44 }}>
          {loading ? <CircularProgress size={22} color="inherit" /> : t("handover_confirm")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
