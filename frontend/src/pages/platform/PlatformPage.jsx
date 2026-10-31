import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Box, Card, CardContent, Chip, CircularProgress, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import { analyticsApi } from "../../api/analyticsApi";
import { formatDate } from "../../utils/formatters";
import PlansAdmin from "./PlansAdmin";
import { PrivateSEO } from "../../components/seo/SEO";

const HEALTH_COLOR = { active: "success", quiet: "warning", dormant: "error", new: "default" };

function Stat({ label, value }) {
  return (
    <Card sx={{ flex: 1, minWidth: 140 }}>
      <CardContent>
        <Typography variant="caption" color="text.secondary">{label}</Typography>
        <Typography variant="h5" fontWeight={800} sx={{ fontVariantNumeric: "tabular-nums" }}>{value}</Typography>
      </CardContent>
    </Card>
  );
}

/** Current plan of a building row: localized name plus a small status / paid-until hint. Tolerates null or partial data. */
function planCell(plan, isAr, t) {
  const name = plan && (isAr ? plan.name_ar || plan.name_en : plan.name_en || plan.name_ar);
  if (!name) return "—";
  const hints = [];
  if (plan.status) hints.push(t(`plan_status_${plan.status}`, { defaultValue: String(plan.status) }));
  if (plan.paid_until) hints.push(t("paid_until", { date: formatDate(plan.paid_until) }));
  return (
    <>
      <Typography variant="body2" fontWeight={600}>{name}</Typography>
      {hints.length > 0 && <Typography variant="caption" color="text.secondary">{hints.join(" · ")}</Typography>}
    </>
  );
}

/** لوحة المنصة — usage numbers for the people who run 3maracom (superusers only). */
export default function PlatformPage() {
  const { t, i18n } = useTranslation("platform");
  const isAr = (i18n.language || "en").startsWith("ar");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    analyticsApi.platform().then((res) => setData(res.data)).catch(() => setError(t("load_error")));
  }, [t]);

  if (error) return <Box sx={{ p: 3 }}><Alert severity="error">{error}</Alert></Box>;
  if (!data) return <Box sx={{ p: 3 }}><CircularProgress /></Box>;

  const totals = [["buildings", data.totals.buildings], ["units", data.totals.units], ["admins", data.totals.admins], ["residents", data.totals.residents]];
  const recent = ["active_buildings", "new_admins", "new_buildings", "payments_recorded", "expenses_added", "reminders_sent"];

  return (
    <>
      <PrivateSEO title="3maracom – Platform" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>{t("title")}</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>{t("help")}</Typography>
        <Stack direction="row" flexWrap="wrap" useFlexGap spacing={1.5} sx={{ mb: 3 }}>
          {totals.map(([key, value]) => <Stat key={key} label={t(key)} value={value} />)}
        </Stack>

        <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("last30")}</Typography>
        <Stack direction="row" flexWrap="wrap" useFlexGap spacing={1.5} sx={{ mb: 3 }}>
          {recent.map((key) => <Stat key={key} label={t(key)} value={data.last_30_days[key]} />)}
        </Stack>

        <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("activation")}</Typography>
        <Stack direction="row" flexWrap="wrap" useFlexGap spacing={1.5} sx={{ mb: 3 }}>
          <Stat label={t("with_units")} value={`${data.activation.with_units}/${data.totals.buildings}`} />
          <Stat label={t("with_activity")} value={`${data.activation.with_activity}/${data.totals.buildings}`} />
        </Stack>

        <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("signups")}</Typography>
        <Stack direction="row" flexWrap="wrap" useFlexGap spacing={1} sx={{ mb: 3 }}>
          {data.signups_by_month.map((s) => <Chip key={s.month} label={`${s.month} · ${s.count}`} variant="outlined" />)}
        </Stack>

        <PlansAdmin />

        <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("health_list")}</Typography>
        <Card>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t("name")}</TableCell>
                <TableCell>{t("plan")}</TableCell>
                <TableCell>{t("units")}</TableCell>
                <TableCell>{t("last_activity")}</TableCell>
                <TableCell>{t("status")}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.buildings.map((b) => (
                <TableRow key={b.id}>
                  <TableCell>{b.name}</TableCell>
                  <TableCell>{planCell(b.plan, isAr, t)}</TableCell>
                  <TableCell>{b.units}</TableCell>
                  <TableCell>{b.last_activity ?? t("never")}</TableCell>
                  <TableCell><Chip size="small" color={HEALTH_COLOR[b.health]} label={t(`health_${b.health}`)} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </Box>
    </>
  );
}
