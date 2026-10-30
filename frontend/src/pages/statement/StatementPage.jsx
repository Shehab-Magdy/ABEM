import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, MenuItem, Stack, Table, TableBody,
  TableCell, TableHead, TableRow, TextField, ToggleButton, ToggleButtonGroup, Typography,
} from "@mui/material";
import { Download, Share } from "@mui/icons-material";
import { buildingsApi } from "../../api/buildingsApi";
import { formatCurrency } from "../../utils/formatters";
import AnnualReportPanel from "./AnnualReportPanel";
import { PrivateSEO } from "../../components/seo/SEO";

const thisMonth = () => new Date().toISOString().slice(0, 7);

/** كشف حساب شهري — what came in, what went out, where the treasury stands; shareable as a PDF. */
export default function StatementPage() {
  const { t } = useTranslation("statement");
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [view, setView] = useState("month");
  const [month, setMonth] = useState(thisMonth());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    buildingsApi
      .list({ page_size: 50 })
      .then((res) => {
        const list = res.data?.results ?? res.data ?? [];
        setBuildings(list);
        if (list[0]) setBuildingId(list[0].id);
      })
      .catch(() => setError(t("load_error")));
  }, [t]);

  useEffect(() => {
    if (view !== "month" || !buildingId || !month) return;
    setLoading(true);
    setError(null);
    buildingsApi
      .statement(buildingId, month)
      .then((res) => setData(res.data))
      .catch(() => setError(t("load_error")))
      .finally(() => setLoading(false));
  }, [buildingId, month, view, t]);

  const getPdf = async () => {
    const res = await buildingsApi.statementPdf(buildingId, month);
    return new File([res.data], `3maracom-statement-${month}.pdf`, { type: "application/pdf" });
  };

  const download = async () => {
    setBusy(true);
    try {
      const file = await getPdf();
      const url = URL.createObjectURL(file);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError(t("pdf_error"));
    } finally {
      setBusy(false);
    }
  };

  // Share sheet (WhatsApp etc.) where the phone supports sharing files; plain download otherwise
  const share = async () => {
    setBusy(true);
    try {
      const file = await getPdf();
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: `${t("title")} ${data?.building ?? ""} ${month}` });
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
      <PrivateSEO title="3maracom – Statement" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>{t("title")}</Typography>
        <ToggleButtonGroup exclusive size="small" value={view} onChange={(_, v) => v && setView(v)} sx={{ mb: 2 }}>
          <ToggleButton value="month">{t("view_month")}</ToggleButton>
          <ToggleButton value="year" data-testid="view-annual">{t("view_year")}</ToggleButton>
        </ToggleButtonGroup>
        {view === "year" && (
          <>
            {buildings.length > 1 && (
              <TextField select size="small" label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)} sx={{ mb: 2, minWidth: 200, display: "block" }}>
                {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
              </TextField>
            )}
            <AnnualReportPanel buildingId={buildingId} />
          </>
        )}
        {view === "month" && <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mb: 2 }}>
          {buildings.length > 1 && (
            <TextField select size="small" label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)} sx={{ minWidth: 200 }}>
              {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
            </TextField>
          )}
          <TextField size="small" type="month" label={t("month")} value={month} onChange={(e) => setMonth(e.target.value)} InputLabelProps={{ shrink: true }} />
          <Button variant="contained" startIcon={<Share />} onClick={share} disabled={busy || !data} sx={{ minHeight: 40 }} data-testid="share-statement">
            {t("share")}
          </Button>
          <Button variant="outlined" startIcon={<Download />} onClick={download} disabled={busy || !data} sx={{ minHeight: 40 }}>
            {t("download")}
          </Button>
        </Stack>}
        {view === "month" && error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {view === "month" && loading && <CircularProgress />}
        {view === "month" && data && !loading && (
          <Stack spacing={2}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
              {[
                ["opening", data.opening_balance],
                ["received", data.total_received],
                ["spent", data.total_expenses],
                ["closing", data.closing_balance],
              ].map(([key, value]) => (
                <Card key={key} sx={key === "closing" ? { bgcolor: "success.dark", color: "#fff", flex: 1 } : { flex: 1 }}>
                  <CardContent>
                    <Typography variant="caption" sx={{ opacity: 0.8 }}>{t(key)}</Typography>
                    <Typography variant="h6" fontWeight={800} sx={{ fontVariantNumeric: "tabular-nums" }}>{formatCurrency(value)}</Typography>
                  </CardContent>
                </Card>
              ))}
            </Stack>

            <Card>
              <CardContent>
                <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("received")}</Typography>
                {data.received.length === 0 ? (
                  <Typography color="text.secondary">{t("none")}</Typography>
                ) : (
                  <Table size="small">
                    <TableHead>
                      <TableRow><TableCell>{t("date")}</TableCell><TableCell>{t("unit")}</TableCell><TableCell align="right">{t("amount")}</TableCell></TableRow>
                    </TableHead>
                    <TableBody>
                      {data.received.map((r, i) => (
                        <TableRow key={i}>
                          <TableCell>{r.date}</TableCell>
                          <TableCell>{r.kind === "payment" ? r.unit : r.label}</TableCell>
                          <TableCell align="right">{formatCurrency(r.amount)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="subtitle1" fontWeight={700} gutterBottom>{t("spent")}</Typography>
                {data.expenses.length === 0 ? (
                  <Typography color="text.secondary">{t("none")}</Typography>
                ) : (
                  <Table size="small">
                    <TableHead>
                      <TableRow><TableCell>{t("date")}</TableCell><TableCell>{t("details")}</TableCell><TableCell align="right">{t("amount")}</TableCell></TableRow>
                    </TableHead>
                    <TableBody>
                      {data.expenses.map((e, i) => (
                        <TableRow key={i}>
                          <TableCell>{e.date}</TableCell>
                          <TableCell>{e.title}</TableCell>
                          <TableCell align="right">{formatCurrency(e.amount)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                  {t("units")} ({data.units_paid}/{data.units_total})
                </Typography>
                <Stack direction="row" flexWrap="wrap" useFlexGap spacing={1}>
                  {data.units.map((u) => (
                    <Chip
                      key={u.unit}
                      label={`${u.unit}${parseFloat(u.balance_due) > 0 ? ` · ${formatCurrency(u.balance_due)}` : ""}`}
                      color={u.paid_this_month ? "success" : "default"}
                      variant={u.paid_this_month ? "filled" : "outlined"}
                    />
                  ))}
                </Stack>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>{t("units_hint")}</Typography>
              </CardContent>
            </Card>
          </Stack>
        )}
      </Box>
    </>
  );
}
