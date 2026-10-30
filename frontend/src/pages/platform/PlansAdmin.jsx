import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Button, Card, CardContent, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, TextField, Typography,
} from "@mui/material";
import { plansApi } from "../../api/plansApi";
import { formatCurrency } from "../../utils/formatters";

const FEATURES = ["subscriptions", "annual_report"];

function TierDialog({ tier, onClose, onSaved }) {
  const { t } = useTranslation("platform");
  const [form, setForm] = useState({});
  const [error, setError] = useState(null);
  useEffect(() => {
    setForm(tier ? { ...tier, max_units: tier.max_units ?? "" } : {});
    setError(null);
  }, [tier]);
  const set = (name) => (e) => setForm((s) => ({ ...s, [name]: e.target.value }));
  const toggle = (f) => setForm((s) => ({ ...s, features: s.features.includes(f) ? s.features.filter((x) => x !== f) : [...s.features, f] }));
  const save = async () => {
    try {
      await plansApi.saveTier(tier.code, {
        name_ar: form.name_ar, name_en: form.name_en, price_monthly: form.price_monthly, price_yearly: form.price_yearly,
        max_units: form.max_units === "" ? null : Number(form.max_units), features: form.features, is_active: form.is_active,
      });
      onSaved();
    } catch (err) {
      const d = err.response?.data;
      setError(d?.detail || Object.values(d ?? {}).flat().join(" ") || t("load_error"));
    }
  };
  return (
    <Dialog open={!!tier} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>{tier?.name_en}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label={t("plan_name_ar")} value={form.name_ar ?? ""} onChange={set("name_ar")} />
          <TextField label={t("plan_name_en")} value={form.name_en ?? ""} onChange={set("name_en")} />
          <TextField label={t("price_monthly")} type="number" value={form.price_monthly ?? ""} onChange={set("price_monthly")} />
          <TextField label={t("price_yearly")} type="number" value={form.price_yearly ?? ""} onChange={set("price_yearly")} />
          <TextField label={t("max_units")} type="number" value={form.max_units ?? ""} onChange={set("max_units")} helperText={t("max_units_help")} />
          {FEATURES.map((f) => (
            <FormControlLabel key={f} control={<Checkbox checked={!!form.features?.includes(f)} onChange={() => toggle(f)} />} label={t(`feature_${f}`)} />
          ))}
          <FormControlLabel control={<Checkbox checked={!!form.is_active} onChange={(e) => setForm((s) => ({ ...s, is_active: e.target.checked }))} />} label={t("plan_active")} />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" onClick={save} sx={{ minHeight: 44 }}>{t("save")}</Button>
      </DialogActions>
    </Dialog>
  );
}

/** Plans, prices, the InstaPay address and the transfers waiting for confirmation — platform owners only. */
export default function PlansAdmin() {
  const { t, i18n } = useTranslation("platform");
  const [tiers, setTiers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [settings, setSettings] = useState({ instapay_address: "", trial_days: 14 });
  const [editing, setEditing] = useState(null);
  const [message, setMessage] = useState(null);

  const load = useCallback(() => {
    plansApi.tiers().then((res) => setTiers(res.data?.results ?? res.data));
    plansApi.payments().then((res) => setPayments(res.data?.results ?? res.data));
    plansApi.settings().then((res) => setSettings(res.data));
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  const review = async (fn, id) => {
    try {
      await fn(id);
      load();
    } catch {
      setMessage({ severity: "error", text: t("load_error") });
    }
  };
  const saveSettings = async () => {
    try {
      setSettings((await plansApi.saveSettings(settings)).data);
      setMessage({ severity: "success", text: t("saved") });
    } catch {
      setMessage({ severity: "error", text: t("load_error") });
    }
  };
  const name = (p) => (i18n.language === "ar" ? p.name_ar : p.name_en);
  const pending = payments.filter((p) => p.status === "pending");

  return (
    <Stack spacing={2} sx={{ mb: 4 }} data-testid="plans-admin">
      {message && <Alert severity={message.severity} onClose={() => setMessage(null)}>{message.text}</Alert>}
      <Typography variant="subtitle1" fontWeight={700}>{t("plans_title")}</Typography>
      <Stack direction={{ xs: "column", md: "row" }} spacing={1.5}>
        {tiers.map((tier) => (
          <Card key={tier.code} variant="outlined" sx={{ flex: 1, opacity: tier.is_active ? 1 : 0.6 }}>
            <CardContent>
              <Typography fontWeight={800}>{name(tier)}</Typography>
              <Typography variant="body2">{formatCurrency(tier.price_monthly)} / {formatCurrency(tier.price_yearly)}</Typography>
              <Typography variant="body2" color="text.secondary">{tier.max_units == null ? t("unlimited") : t("units_n", { n: tier.max_units })} · {tier.features.map((f) => t(`feature_${f}`)).join("، ") || "—"}</Typography>
              <Button size="small" onClick={() => setEditing(tier)} sx={{ mt: 1 }}>{t("edit")}</Button>
            </CardContent>
          </Card>
        ))}
      </Stack>

      <Typography variant="subtitle1" fontWeight={700}>{t("payments_title")}</Typography>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
        <TextField size="small" label={t("instapay_address")} value={settings.instapay_address} onChange={(e) => setSettings((s) => ({ ...s, instapay_address: e.target.value }))} sx={{ minWidth: 240 }} />
        <TextField size="small" type="number" label={t("trial_days")} value={settings.trial_days} onChange={(e) => setSettings((s) => ({ ...s, trial_days: e.target.value }))} sx={{ width: 140 }} />
        <TextField size="small" type="number" label={t("grace_days")} value={settings.grace_days ?? 7} onChange={(e) => setSettings((s) => ({ ...s, grace_days: e.target.value }))} helperText={t("grace_help")} sx={{ width: 180 }} />
        <Button variant="outlined" onClick={saveSettings} sx={{ minHeight: 40 }}>{t("save")}</Button>
      </Stack>
      {pending.length === 0 && <Typography color="text.secondary">{t("no_pending")}</Typography>}
      {pending.map((p) => (
        <Card key={p.id} variant="outlined">
          <CardContent>
            <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={1}>
              <Typography>
                {p.building_name} · {name({ name_ar: p.plan_name.ar, name_en: p.plan_name.en })} · {t(p.period)} · {formatCurrency(p.amount)} · <Chip size="small" label={p.reference} />
              </Typography>
              <Stack direction="row" spacing={1}>
                <Button size="small" variant="contained" color="success" onClick={() => review(plansApi.confirm, p.id)}>{t("confirm")}</Button>
                <Button size="small" variant="outlined" color="error" onClick={() => review(plansApi.reject, p.id)}>{t("reject")}</Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      ))}
      <TierDialog tier={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />
    </Stack>
  );
}
