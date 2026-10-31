import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle, LinearProgress, MenuItem,
  Stack, TextField, ToggleButton, ToggleButtonGroup, Typography,
} from "@mui/material";
import { CheckCircle } from "@mui/icons-material";
import { plansApi } from "../../api/plansApi";
import { buildingsApi } from "../../api/buildingsApi";
import { formatCurrency } from "../../utils/formatters";
import { PrivateSEO } from "../../components/seo/SEO";

/** Name of a plan in the current language. */
export const planName = (plan, lang) => (lang === "ar" ? plan.name_ar : plan.name_en);

/** الباقة — which plan a building is on, what it allows, and how to move to another one by InstaPay. */
export default function PlanPage() {
  const { t, i18n } = useTranslation("plans");
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [current, setCurrent] = useState(null);
  const [tiers, setTiers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [paying, setPaying] = useState(null); // tier being bought
  const [period, setPeriod] = useState("monthly");
  const [reference, setReference] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    buildingsApi.list({ page_size: 50 }).then((res) => {
      const list = res.data?.results ?? res.data ?? [];
      setBuildings(list);
      if (list[0]) setBuildingId(list[0].id);
    });
    plansApi.tiers().then((res) => setTiers(res.data?.results ?? res.data));
  }, []);

  const load = useCallback(() => {
    if (!buildingId) return;
    plansApi.current(buildingId).then((res) => setCurrent(res.data)).catch(() => setMessage({ severity: "error", text: t("load_error") }));
    plansApi.payments().then((res) => setPayments((res.data?.results ?? res.data).filter((p) => p.building_id === buildingId)));
  }, [buildingId, t]);

  useEffect(() => {
    load();
  }, [load]);

  const price = (tier) => (period === "yearly" ? tier.price_yearly : tier.price_monthly);
  /** Whole-number percent saved by paying yearly instead of 12 months; 0 when there is no saving. */
  const yearlySaving = (tier) => {
    const full = Number(tier.price_monthly) * 12;
    const pct = full > 0 ? Math.round((1 - Number(tier.price_yearly) / full) * 100) : 0;
    return pct > 0 ? pct : 0;
  };

  const submit = async () => {
    setBusy(true);
    try {
      await plansApi.pay({ building_id: buildingId, plan_code: paying.code, period, reference });
      setPaying(null);
      setReference("");
      setMessage({ severity: "success", text: t("sent") });
      load();
    } catch (err) {
      const d = err.response?.data;
      setMessage({ severity: "error", text: d?.detail || Object.values(d ?? {}).flat().join(" ") || t("load_error") });
    } finally {
      setBusy(false);
    }
  };

  const limit = current?.plan.max_units;
  return (
    <>
      <PrivateSEO title="3maracom – Plan" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>{t("title")}</Typography>
        {buildings.length > 1 && (
          <TextField select size="small" label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)} sx={{ mb: 2, minWidth: 220 }}>
            {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
          </TextField>
        )}
        {message && <Alert severity={message.severity} sx={{ mb: 2 }} onClose={() => setMessage(null)}>{message.text}</Alert>}

        {current && (
          <Card sx={{ mb: 3 }} data-testid="current-plan">
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                <Typography variant="h6" fontWeight={800}>{planName(current.plan, i18n.language)}</Typography>
                {current.on_trial && <Chip size="small" color="info" label={t("trial_until", { date: current.paid_until })} />}
                {!current.on_trial && current.paid_until && <Chip size="small" color="success" label={t("paid_until", { date: current.paid_until })} />}
              </Stack>
              <Typography sx={{ mt: 1 }}>{limit == null ? t("units_unlimited", { n: current.units }) : t("units_of", { n: current.units, max: limit })}</Typography>
              {limit != null && <LinearProgress variant="determinate" value={Math.min(100, (current.units / limit) * 100)} sx={{ mt: 1, height: 8, borderRadius: 4 }} />}
            </CardContent>
          </Card>
        )}

        <ToggleButtonGroup exclusive size="small" value={period} onChange={(_, v) => v && setPeriod(v)} sx={{ mb: 2 }}>
          <ToggleButton value="monthly">{t("monthly")}</ToggleButton>
          <ToggleButton value="yearly">{t("yearly")}</ToggleButton>
        </ToggleButtonGroup>

        <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 3 }}>
          {tiers.map((tier) => {
            const mine = current?.plan.code === tier.code && !current?.on_trial;
            const free = Number(tier.price_monthly) === 0;
            return (
              <Card key={tier.code} variant="outlined" sx={{ flex: 1, ...(mine && { borderColor: "success.main", borderWidth: 2 }) }}>
                <CardContent>
                  <Typography variant="h6" fontWeight={800}>{planName(tier, i18n.language)}</Typography>
                  <Typography variant="h5" fontWeight={800} sx={{ mt: 1 }}>{free ? t("free") : formatCurrency(price(tier))}</Typography>
                  <Box sx={{ minHeight: 28, mb: 1 }}>
                    {!free && yearlySaving(tier) > 0 && (period === "yearly" ? (
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography variant="body2" color="text.secondary" sx={{ textDecoration: "line-through" }}>{formatCurrency(Number(tier.price_monthly) * 12)}</Typography>
                        <Chip size="small" color="success" label={t("save_percent", { pct: yearlySaving(tier) })} />
                      </Stack>
                    ) : (
                      <Typography variant="body2" color="success.main">{t("save_with_yearly", { pct: yearlySaving(tier) })}</Typography>
                    ))}
                  </Box>
                  <Stack spacing={0.5} sx={{ mb: 2 }}>
                    <Typography variant="body2">{tier.max_units == null ? t("limit_unlimited") : t("limit_units", { n: tier.max_units })}</Typography>
                    {["subscriptions", "annual_report"].map((f) => (
                      <Typography key={f} variant="body2" color={tier.features.includes(f) ? "text.primary" : "text.disabled"}>
                        {tier.features.includes(f) ? "✓ " : "— "}{t(`feature_${f}`)}
                      </Typography>
                    ))}
                  </Stack>
                  {mine ? <Chip icon={<CheckCircle />} color="success" label={t("your_plan")} /> : !free && (
                    <Button variant="contained" color="secondary" onClick={() => setPaying(tier)} sx={{ minHeight: 44 }}>{t("choose")}</Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </Stack>

        {payments.length > 0 && (
          <>
            <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("your_payments")}</Typography>
            <Stack spacing={1}>
              {payments.map((p) => (
                <Stack key={p.id} direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                  <Typography>{planName({ name_ar: p.plan_name.ar, name_en: p.plan_name.en }, i18n.language)} · {t(p.period)} · {formatCurrency(p.amount)}</Typography>
                  <Chip size="small" color={{ pending: "warning", confirmed: "success", rejected: "error" }[p.status]} label={t(`status_${p.status}`)} />
                </Stack>
              ))}
            </Stack>
          </>
        )}
      </Box>

      <Dialog open={!!paying} onClose={busy ? undefined : () => setPaying(null)} fullWidth maxWidth="xs">
        <DialogTitle>{paying && t("pay_title", { plan: planName(paying, i18n.language) })}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Typography>{paying && t("pay_amount", { amount: formatCurrency(price(paying)), period: t(period) })}</Typography>
            <Typography>{current?.instapay_address ? t("pay_to", { address: current.instapay_address }) : t("no_address")}</Typography>
            <TextField label={t("reference")} value={reference} onChange={(e) => setReference(e.target.value)} helperText={t("reference_help")} />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setPaying(null)} disabled={busy} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
          <Button variant="contained" onClick={submit} disabled={busy || !reference.trim()} sx={{ minHeight: 44 }}>{t("send")}</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
