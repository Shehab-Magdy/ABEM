import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Box, Button, Card, CardContent, FormControlLabel, MenuItem, Stack, Switch, Table, TableBody, TableCell,
  TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import { buildingsApi } from "../../api/buildingsApi";
import { apartmentsApi } from "../../api/apartmentsApi";
import { PrivateSEO } from "../../components/seo/SEO";

const EMPTY = { amount: "", billing_day: 1, due_days: 10, is_active: true };

/** الاشتراك الشهري — one fixed amount per unit, billed automatically each month. */
export default function SubscriptionPage() {
  const { t } = useTranslation("subscription");
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [form, setForm] = useState(EMPTY);
  const [hasPlan, setHasPlan] = useState(false);
  const [units, setUnits] = useState([]);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    buildingsApi
      .list({ page_size: 50 })
      .then((res) => {
        const list = res.data?.results ?? res.data ?? [];
        setBuildings(list);
        if (list[0]) setBuildingId(list[0].id);
      })
      .catch(() => setError(t("error")));
  }, [t]);

  const load = useCallback(async () => {
    if (!buildingId) return;
    setMessage(null);
    setError(null);
    try {
      const [planRes, unitsRes] = await Promise.all([
        buildingsApi.subscription(buildingId),
        buildingsApi.apartments(buildingId, { page_size: 500 }),
      ]);
      const plan = planRes.data.plan;
      setHasPlan(!!plan);
      setForm(plan ? { amount: plan.amount, billing_day: plan.billing_day, due_days: plan.due_days, is_active: plan.is_active } : EMPTY);
      setUnits(unitsRes.data?.results ?? unitsRes.data ?? []);
    } catch {
      setError(t("error"));
    }
  }, [buildingId, t]);

  useEffect(() => {
    load();
  }, [load]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const save = async () => {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      await buildingsApi.saveSubscription(buildingId, form);
      setHasPlan(true);
      setMessage(t("saved"));
    } catch (err) {
      setError(err.response?.data?.detail || t("error"));
    } finally {
      setSaving(false);
    }
  };

  const togglePause = async (unit) => {
    const paused = !unit.billing_paused;
    const reason = paused ? window.prompt(t("pause_reason_prompt"), unit.billing_pause_reason || "") ?? "" : "";
    try {
      await apartmentsApi.update(unit.id, { billing_paused: paused, billing_pause_reason: reason });
      load();
    } catch {
      setError(t("error"));
    }
  };

  const billable = units.filter((u) => !u.billing_paused).length;

  return (
    <>
      <PrivateSEO title="3maracom – Subscription" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>{t("title")}</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>{t("help")}</Typography>
        {buildings.length > 1 && (
          <TextField select size="small" label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)} sx={{ mb: 2, minWidth: 220 }}>
            {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
          </TextField>
        )}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Stack spacing={2}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField type="number" label={t("amount")} value={form.amount} onChange={(e) => set("amount", e.target.value)} inputProps={{ min: 0, step: "0.01" }} fullWidth />
                <TextField type="number" label={t("billing_day")} helperText={t("billing_day_help")} value={form.billing_day} onChange={(e) => set("billing_day", e.target.value)} inputProps={{ min: 1, max: 28 }} fullWidth />
                <TextField type="number" label={t("due_days")} helperText={t("due_days_help")} value={form.due_days} onChange={(e) => set("due_days", e.target.value)} inputProps={{ min: 0, max: 60 }} fullWidth />
              </Stack>
              <FormControlLabel control={<Switch checked={form.is_active} onChange={(e) => set("is_active", e.target.checked)} />} label={t("active")} />
              {form.amount > 0 && (
                <Typography variant="body2" color="text.secondary">
                  {t("monthly_total", { units: billable, total: (Number(form.amount) * billable).toLocaleString() })}
                </Typography>
              )}
              <Box>
                <Button variant="contained" onClick={save} disabled={saving || !(Number(form.amount) > 0)} sx={{ minHeight: 44 }}>
                  {hasPlan ? t("save") : t("start")}
                </Button>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        <Typography variant="h6" fontWeight={700} gutterBottom>{t("units")}</Typography>
        <Card>
          <Table size="small">
            <TableHead>
              <TableRow><TableCell>{t("unit")}</TableCell><TableCell>{t("billed")}</TableCell><TableCell>{t("pause_reason")}</TableCell></TableRow>
            </TableHead>
            <TableBody>
              {units.map((u) => (
                <TableRow key={u.id}>
                  <TableCell>{u.unit_number}</TableCell>
                  <TableCell>
                    <Switch checked={!u.billing_paused} onChange={() => togglePause(u)} inputProps={{ "aria-label": t("billed") }} />
                  </TableCell>
                  <TableCell>{u.billing_paused ? u.billing_pause_reason || "—" : ""}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </Box>
    </>
  );
}
