import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import DataTable from "../../components/DataTable";
import {
  Alert, Box, Button, Card, CardContent, Chip, FormControlLabel, MenuItem, Stack, Switch,
  TextField, Typography,
} from "@mui/material";
import { PauseCircle } from "@mui/icons-material";
import { buildingsApi } from "../../api/buildingsApi";
import { expensesApi } from "../../api/expensesApi";
import { formatCurrency } from "../../utils/formatters";
import { PrivateSEO } from "../../components/seo/SEO";
import ReasonDialog from "../../components/ReasonDialog";
import UnitBillingDialog from "../../components/UnitBillingDialog";

const EMPTY = { amount: "", billing_day: 1, due_days: 10, is_active: true, late_fee_type: "none", late_fee_value: 0, grace_days: 0 };

/** الاشتراك الشهري — one fixed amount per unit, billed automatically each month. */
export default function SubscriptionPage() {
  const { t } = useTranslation("subscription");
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [form, setForm] = useState(EMPTY);
  const [hasPlan, setHasPlan] = useState(false);
  const [units, setUnits] = useState([]);
  const [lateFees, setLateFees] = useState([]);
  const [billingUnit, setBillingUnit] = useState(null);
  const [waiveTarget, setWaiveTarget] = useState(null);
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
      const [planRes, unitsRes, feesRes] = await Promise.all([
        buildingsApi.subscription(buildingId),
        buildingsApi.apartments(buildingId, { page_size: 500 }),
        expensesApi.lateFees({ building_id: buildingId, waived: "false" }),
      ]);
      setLateFees(feesRes.data?.results ?? feesRes.data ?? []);
      const plan = planRes.data.plan;
      setHasPlan(!!plan);
      setForm(plan ? { amount: plan.amount, billing_day: plan.billing_day, due_days: plan.due_days, is_active: plan.is_active, late_fee_type: plan.late_fee_type, late_fee_value: plan.late_fee_value, grace_days: plan.grace_days } : EMPTY);
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

  const waive = async (reason) => {
    await expensesApi.waiveLateFee(waiveTarget.id, reason);
    setWaiveTarget(null);
    load();
  };

  const billable = units.filter((u) => !u.billing_paused).length;
  const monthlyTotal = units.filter((u) => !u.billing_paused).reduce((sum, u) => sum + Number(form.amount || 0) * Number(u.rate_factor || 1), 0);

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
              <Typography variant="subtitle2" fontWeight={700}>{t("late_fee")}</Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField select label={t("late_fee_type")} value={form.late_fee_type} onChange={(e) => set("late_fee_type", e.target.value)} fullWidth>
                  <MenuItem value="none">{t("late_fee_none")}</MenuItem>
                  <MenuItem value="fixed">{t("late_fee_fixed")}</MenuItem>
                  <MenuItem value="percent">{t("late_fee_percent")}</MenuItem>
                </TextField>
                {form.late_fee_type !== "none" && (
                  <>
                    <TextField type="number" label={t("late_fee_value")} value={form.late_fee_value} onChange={(e) => set("late_fee_value", e.target.value)} inputProps={{ min: 0, step: "0.01" }} fullWidth />
                    <TextField type="number" label={t("grace_days")} helperText={t("grace_days_help")} value={form.grace_days} onChange={(e) => set("grace_days", e.target.value)} inputProps={{ min: 0, max: 60 }} fullWidth />
                  </>
                )}
              </Stack>
              <FormControlLabel control={<Switch checked={form.is_active} onChange={(e) => set("is_active", e.target.checked)} />} label={t("active")} />
              {form.amount > 0 && (
                <Typography variant="body2" color="text.secondary">
                  {t("monthly_total", { units: billable, total: monthlyTotal.toLocaleString() })}
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
        <DataTable
          size="small"
          rowKey="id"
          rows={units}
          testId="subscription-units-table"
          columns={[
            { id: "unit_number", label: t("unit") },
            {
              id: "billing",
              label: t("billing"),
              sortValue: (u) => (u.billing_paused ? 0 : Math.round(Number(u.rate_factor) * 100) !== 100 ? 1 : 2),
              searchable: false,
              render: (u) => {
                const pct = Math.round(Number(u.rate_factor) * 100);
                return u.billing_paused ? (
                  <Chip size="small" color="warning" icon={<PauseCircle />} label={t("status_paused")} />
                ) : pct !== 100 ? (
                  <Chip size="small" color="info" variant="outlined" label={t("status_percent", { pct })} />
                ) : (
                  <Chip size="small" variant="outlined" label={t("status_full")} />
                );
              },
            },
            {
              id: "billing_pause_reason",
              label: t("billing_reason"),
              hideOnMobile: true,
              render: (u) => (u.billing_paused || Math.round(Number(u.rate_factor) * 100) !== 100 ? u.billing_pause_reason || "—" : ""),
            },
            {
              id: "actions",
              label: t("actions", { ns: "common" }),
              align: "right",
              sortable: false,
              render: (u) => (
                <Button size="small" onClick={() => setBillingUnit(u)} sx={{ minHeight: 44 }}>{t("edit_billing")}</Button>
              ),
            },
          ]}
        />

        {lateFees.length > 0 && (
          <>
            <Typography variant="h6" fontWeight={700} sx={{ mt: 3 }} gutterBottom>{t("late_fees_list")}</Typography>
            <DataTable
              size="small"
              rowKey="id"
              rows={lateFees}
              testId="subscription-late-fees-table"
              minWidth={0}
              columns={[
                { id: "unit_number", label: t("unit") },
                {
                  id: "amount",
                  label: t("fee"),
                  sortValue: (f) => parseFloat(f.amount),
                  searchValue: (f) => String(f.amount),
                  render: (f) => formatCurrency(f.amount),
                },
                {
                  id: "actions",
                  label: t("actions", { ns: "common" }),
                  align: "right",
                  sortable: false,
                  render: (f) => (
                    <Button size="small" color="warning" onClick={() => setWaiveTarget(f)} sx={{ minHeight: 44 }}>{t("waive")}</Button>
                  ),
                },
              ]}
            />
          </>
        )}
      </Box>
      <UnitBillingDialog unit={billingUnit} onClose={() => setBillingUnit(null)} onSaved={() => { setBillingUnit(null); load(); }} />
      <ReasonDialog
        open={!!waiveTarget}
        title={t("waive_title")}
        description={t("waive_description")}
        label={t("waive_prompt")}
        confirmLabel={t("waive")}
        color="warning"
        onClose={() => setWaiveTarget(null)}
        onConfirm={waive}
      />
    </>
  );
}
