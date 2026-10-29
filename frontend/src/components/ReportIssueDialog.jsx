import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField } from "@mui/material";
import { buildingsApi } from "../api/buildingsApi";
import { maintenanceApi } from "../api/maintenanceApi";

export const CATEGORIES = ["elevator", "stairs", "cleaning", "electricity", "water", "other"];

/** بلاغ صيانة سريع — pick what is wrong, add a line if you want, send. */
export default function ReportIssueDialog({ open, onClose, onSent }) {
  const { t } = useTranslation("maintenance");
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [category, setCategory] = useState("elevator");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!open) return;
    setSent(false);
    setError(null);
    setDescription("");
    buildingsApi
      .list({ page_size: 50 })
      .then((res) => {
        const list = res.data?.results ?? res.data ?? [];
        setBuildings(list);
        if (list[0]) setBuildingId(list[0].id);
      })
      .catch(() => setError(t("load_error")));
  }, [open, t]);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      await maintenanceApi.create({ building_id: buildingId, category, description });
      setSent(true);
      onSent?.();
    } catch (err) {
      setError(err.response?.data?.detail || t("send_error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>{t("report_title")}</DialogTitle>
      <DialogContent>
        {sent ? (
          <Alert severity="success">{t("sent")}</Alert>
        ) : (
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            {buildings.length > 1 && (
              <TextField select label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)}>
                {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
              </TextField>
            )}
            <TextField select label={t("category")} value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => <MenuItem key={c} value={c}>{t(`cat_${c}`)}</MenuItem>)}
            </TextField>
            <TextField label={t("description")} value={description} onChange={(e) => setDescription(e.target.value)} multiline minRows={2} />
          </Stack>
        )}
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} sx={{ minHeight: 44 }}>{t("close")}</Button>
        {!sent && (
          <Button variant="contained" onClick={submit} disabled={loading || !buildingId} sx={{ minHeight: 44 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : t("send")}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
