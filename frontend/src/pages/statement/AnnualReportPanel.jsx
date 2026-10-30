import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Button, Card, CardContent, CircularProgress, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import { Download, Share } from "@mui/icons-material";
import { buildingsApi } from "../../api/buildingsApi";
import { formatCurrency } from "../../utils/formatters";

/** التقرير السنوي — the year for the general assembly, shareable as a PDF. */
export default function AnnualReportPanel({ buildingId }) {
  const { t, i18n } = useTranslation("statement");
  const [year, setYear] = useState(new Date().getFullYear());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!buildingId || !year) return;
    setLoading(true);
    setError(null);
    buildingsApi
      .annualReport(buildingId, year)
      .then((res) => setData(res.data))
      .catch(() => setError(t("annual_load_error")))
      .finally(() => setLoading(false));
  }, [buildingId, year, t]);

  const monthName = (m) => new Intl.DateTimeFormat(i18n.language === "ar" ? "ar-EG" : "en", { month: "long" }).format(new Date(2026, m - 1, 1));

  const pdf = async (share) => {
    setBusy(true);
    try {
      const res = await buildingsApi.annualReportPdf(buildingId, year);
      const file = new File([res.data], `3maracom-annual-report-${year}.pdf`, { type: "application/pdf" });
      if (share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: `${t("annual_title")} ${data?.building ?? ""} ${year}` });
      } else {
        const url = URL.createObjectURL(file);
        const a = document.createElement("a");
        a.href = url;
        a.download = file.name;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      if (err?.name !== "AbortError") setError(t("pdf_error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mb: 2 }}>
        <TextField size="small" type="number" label={t("year")} value={year} onChange={(e) => setYear(Number(e.target.value))} inputProps={{ min: 2000, max: 2100 }} sx={{ width: 120 }} />
        <Button variant="contained" startIcon={<Share />} onClick={() => pdf(true)} disabled={busy || !data} sx={{ minHeight: 40 }}>{t("share")}</Button>
        <Button variant="outlined" startIcon={<Download />} onClick={() => pdf(false)} disabled={busy || !data} sx={{ minHeight: 40 }}>{t("download")}</Button>
      </Stack>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading && <CircularProgress />}
      {data && !loading && (
        <Stack spacing={2} data-testid="annual-report">
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
            {[["annual_opening", data.opening_balance], ["annual_collected", data.total_collected], ["spent", data.total_expenses], ["annual_closing", data.closing_balance]].map(([key, value]) => (
              <Card key={key} sx={key === "annual_closing" ? { bgcolor: "success.dark", color: "#fff", flex: 1 } : { flex: 1 }}>
                <CardContent>
                  <Typography variant="caption" sx={{ opacity: 0.8 }}>{t(key)}</Typography>
                  <Typography variant="h6" fontWeight={800} sx={{ fontVariantNumeric: "tabular-nums" }}>{formatCurrency(value)}</Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>

          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("by_month")}</Typography>
              <Table size="small">
                <TableHead><TableRow><TableCell>{t("month")}</TableCell><TableCell align="right">{t("annual_collected")}</TableCell><TableCell align="right">{t("spent")}</TableCell></TableRow></TableHead>
                <TableBody>
                  {data.months.map((m) => (
                    <TableRow key={m.month}>
                      <TableCell>{monthName(m.month)}</TableCell>
                      <TableCell align="right">{formatCurrency(m.collected)}</TableCell>
                      <TableCell align="right">{formatCurrency(m.expenses)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("by_category")}</Typography>
              {data.expenses_by_category.length === 0 ? (
                <Typography color="text.secondary">{t("annual_none")}</Typography>
              ) : (
                <Table size="small">
                  <TableBody>
                    {data.expenses_by_category.map((c) => (
                      <TableRow key={c.category}><TableCell>{c.category}</TableCell><TableCell align="right">{formatCurrency(c.amount)}</TableCell></TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("unpaid")} — {formatCurrency(data.total_unpaid)}</Typography>
              {data.unpaid_units.length === 0 ? (
                <Typography color="text.secondary">{t("annual_none")}</Typography>
              ) : (
                <Table size="small">
                  <TableBody>
                    {data.unpaid_units.map((u) => (
                      <TableRow key={u.unit}><TableCell>{u.unit}</TableCell><TableCell align="right">{formatCurrency(u.balance_due)}</TableCell></TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Stack>
      )}
    </>
  );
}
