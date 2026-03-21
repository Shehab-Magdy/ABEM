/**
 * Owner Dashboard — Sprint 5.
 * Shows personal financial overview: balance summary, expense breakdown, recent payments.
 */
import { useEffect, useState, useCallback } from "react";
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Grid,
  TextField,
  Typography,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Paper,
  Button,
  Stack,
} from "@mui/material";
import { VpnKey } from "@mui/icons-material";
import { PieChart } from "@mui/x-charts/PieChart";
import { useTranslation } from "react-i18next";
import axiosClient from "../../api/axiosClient";
import { apartmentsApi } from "../../api/apartmentsApi";
import { PrivateSEO } from "../../components/seo/SEO";

const PAYMENT_METHOD_KEYS = {
  cash: "payments:methodCash",
  bank_transfer: "payments:methodBankTransfer",
  cheque: "payments:methodCheque",
  mobile_wallet: "payments:methodMobileWallet",
  other: "payments:methodOther",
};

export default function OwnerDashboardPage() {
  const { t } = useTranslation(["dashboard", "payments"]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchDashboard = useCallback(() => {
    setLoading(true);
    setError("");
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    axiosClient
      .get("/dashboard/owner/", { params })
      .then((r) => setData(r.data))
      .catch(() => setError("Failed to load dashboard data."))
      .finally(() => setLoading(false));
  }, [dateFrom, dateTo]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // ── Claim unit by code ────────────────────────────────────────────────────
  const [claimOpen, setClaimOpen] = useState(false);
  const [regCode, setRegCode] = useState("");
  const [codeInfo, setCodeInfo] = useState(null);
  const [codeError, setCodeError] = useState(null);
  const [validating, setValidating] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [claimSuccess, setClaimSuccess] = useState(null);

  const handleValidateCode = async () => {
    setCodeError(null);
    setCodeInfo(null);
    setValidating(true);
    try {
      const res = await apartmentsApi.validateInvite(undefined, regCode.trim().toUpperCase());
      setCodeInfo(res.data);
    } catch (err) {
      setCodeError(err.response?.data?.detail || "Invalid or expired code.");
    } finally {
      setValidating(false);
    }
  };

  const handleClaimCode = async () => {
    setClaiming(true);
    setCodeError(null);
    try {
      await apartmentsApi.useInviteCode(regCode.trim().toUpperCase());
      setClaimSuccess(`Unit ${codeInfo.unit_number} in ${codeInfo.building_name} claimed successfully!`);
      setCodeInfo(null);
      setRegCode("");
      fetchDashboard();
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 409) {
        setCodeError("This unit has already been claimed by another owner.");
      } else if (status === 410) {
        setCodeError("This code has already been used or has expired.");
      } else {
        setCodeError(detail || "Could not claim unit.");
      }
    } finally {
      setClaiming(false);
    }
  };

  const balance = parseFloat(data?.balance_summary?.current_balance ?? 0);
  const isCredit = balance < 0;
  const isSettled = balance === 0;

  const pieData = (data?.expense_breakdown ?? []).map((row, idx) => ({
    id: idx,
    value: parseFloat(row.total),
    label: t(`categories:${row.category_name}`, row.category_name),
  }));

  const hasPayments = (data?.recent_payments ?? []).length > 0;
  const hasBreakdown = pieData.length > 0;
  // Show content sections whenever data is loaded (even with zeros)
  const dataLoaded = data !== null;

  return (
    <>
    <PrivateSEO title="ABEM – Dashboard" />
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        {t("owner_dashboard")}
      </Typography>

      {/* ── Claim unit by code ── */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent sx={{ pb: claimOpen ? undefined : "16px !important" }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={1}>
              <VpnKey fontSize="small" color="primary" />
              <Typography variant="subtitle1" fontWeight={600}>{t("claim_unit")}</Typography>
            </Stack>
            <Button size="small" variant="outlined" onClick={() => { setClaimOpen((p) => !p); setCodeError(null); setCodeInfo(null); setClaimSuccess(null); }}>
              {claimOpen ? t("hide") : t("enter_code")}
            </Button>
          </Stack>
          <Collapse in={claimOpen}>
            <Stack spacing={1.5} sx={{ mt: 2 }}>
              {claimSuccess && (
                <Alert severity="success" onClose={() => setClaimSuccess(null)}>{claimSuccess}</Alert>
              )}
              {codeError && (
                <Alert severity="error" onClose={() => setCodeError(null)}>{codeError}</Alert>
              )}
              {codeInfo && (
                <Alert severity="success">
                  Found: <strong>Unit {codeInfo.unit_number}</strong> in <strong>{codeInfo.building_name}</strong> — {codeInfo.building_city}
                </Alert>
              )}
              <Stack direction="row" spacing={1} alignItems="flex-start">
                <TextField
                  label={t("registration_code")}
                  value={regCode}
                  onChange={(e) => { setRegCode(e.target.value.toUpperCase()); setCodeInfo(null); setCodeError(null); }}
                  size="small"
                  inputProps={{ maxLength: 8, style: { fontFamily: "monospace", letterSpacing: 2 } }}
                  placeholder="e.g. AB12CD34"
                  sx={{ flex: 1 }}
                />
                <Button
                  variant="outlined"
                  size="small"
                  disabled={regCode.length < 8 || validating}
                  onClick={handleValidateCode}
                  sx={{ mt: 0.5 }}
                >
                  {validating ? <CircularProgress size={18} /> : t("validate")}
                </Button>
              </Stack>
              {codeInfo && (
                <Button variant="contained" disabled={claiming} onClick={handleClaimCode}>
                  {claiming ? <CircularProgress size={20} color="inherit" /> : t("claim_unit_number", { unit: codeInfo.unit_number })}
                </Button>
              )}
            </Stack>
          </Collapse>
        </CardContent>
      </Card>

      {/* ── Filters ── */}
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 3 }}>
        <TextField
          size="small"
          label={t("date_from")}
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          InputLabelProps={{ shrink: true }}
          inputProps={{ "data-testid": "date-from" }}
        />
        <TextField
          size="small"
          label={t("date_to")}
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          InputLabelProps={{ shrink: true }}
          inputProps={{ "data-testid": "date-to" }}
        />
        <Button size="small" variant="outlined" data-testid="download-report"
          onClick={() => window.print()}>
          {t("download_report")}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 6 }}>
          <CircularProgress />
        </Box>
      ) : !dataLoaded ? (
        <Alert severity="info" data-testid="empty-state">
          {t("no_data_available")}
        </Alert>
      ) : (
        <>
          {/* ── Balance summary ── */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>{t("balance_summary")}</Typography>
              <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap", alignItems: "center" }}>
                <Box>
                  <Typography variant="overline" color="text.secondary">{t("current_balance")}</Typography>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography
                      variant="h5"
                      fontWeight={700}
                      color={isCredit ? "info.main" : isSettled ? "success.main" : "error.main"}
                      data-testid="current-balance"
                    >
                      {Math.abs(balance).toLocaleString()} EGP
                    </Typography>
                    {isCredit && (
                      <Chip label={t("credit_label")} size="small" color="info" data-testid="credit-label" />
                    )}
                    {isSettled && (
                      <Chip label={t("settled_label")} size="small" color="success" data-testid="settled-label" />
                    )}
                    {!isCredit && !isSettled && (
                      <Chip label={t("owed_label")} size="small" color="error" data-testid="owed-label" />
                    )}
                  </Box>
                </Box>
                <Box>
                  <Typography variant="overline" color="text.secondary">{t("total_paid_ytd")}</Typography>
                  <Typography variant="h5" fontWeight={700} color="success.main" data-testid="total-paid-ytd">
                    {parseFloat(data?.balance_summary?.total_paid_ytd ?? 0).toLocaleString()} EGP
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Grid container spacing={3}>
            {/* ── Expense breakdown chart ── */}
            {hasBreakdown && (
              <Grid item xs={12} md={5}>
                <Card sx={{ height: "100%" }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>{t("expense_breakdown")}</Typography>
                    <Box
                      aria-label="Expense breakdown by category pie chart"
                      role="img"
                      data-testid="expense-breakdown-chart"
                    >
                      <PieChart
                        series={[{ data: pieData, innerRadius: 40 }]}
                        height={260}
                        tooltip={{ trigger: "item" }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* ── Recent payments ── */}
            <Grid item xs={12} md={hasBreakdown ? 7 : 12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>{t("recent_payments")}</Typography>
                  {!hasPayments ? (
                    <Typography color="text.secondary">{t("no_payments_yet")}</Typography>
                  ) : (
                    <Paper variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>{t("date_col")}</TableCell>
                            <TableCell>{t("amount_col")}</TableCell>
                            <TableCell>{t("method_col")}</TableCell>
                            <TableCell>{t("notes_col")}</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {(data?.recent_payments ?? []).map((p) => (
                            <TableRow key={p.id}>
                              <TableCell>{p.payment_date}</TableCell>
                              <TableCell>
                                {parseFloat(p.amount_paid).toLocaleString()} EGP
                              </TableCell>
                              <TableCell>{PAYMENT_METHOD_KEYS[p.payment_method] ? t(PAYMENT_METHOD_KEYS[p.payment_method]) : p.payment_method}</TableCell>
                              <TableCell>{p.notes}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Paper>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
    </>
  );
}
