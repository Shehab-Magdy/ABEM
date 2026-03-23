/**
 * Admin Dashboard — Sprint 5.
 * Shows building-wide financial overview: totals, overdue count, monthly trend, building summary.
 */
import { useEffect, useState, useCallback } from "react";
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TextField,
  Tooltip,
  Typography,
  Alert,
  Button,
} from "@mui/material";
import { TrendingUp, TrendingDown } from "@mui/icons-material";
import { BarChart } from "@mui/x-charts/BarChart";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../hooks/useAuth";
import axiosClient from "../../api/axiosClient";
import { formatCurrency } from "../../utils/formatters";
import { PrivateSEO } from "../../components/seo/SEO";

const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function TrendBadge({ pct, invertColors }) {
  if (pct === null || pct === undefined) return null;
  const up = pct >= 0;
  // invertColors=true for expenses: rising expenses = bad (red)
  const isGood = invertColors ? !up : up;
  const color = isGood ? "success.main" : "error.main";
  const Icon = up ? TrendingUp : TrendingDown;
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 0.5 }}>
      <Icon sx={{ fontSize: 14, color }} />
      <Typography variant="caption" sx={{ color, fontWeight: 600 }}>
        {up ? "+" : ""}{pct}% vs last month
      </Typography>
    </Box>
  );
}

export default function AdminDashboardPage() {
  const { t, i18n } = useTranslation("dashboard");
  const isRtl = (i18n.language || "en").startsWith("ar");
  const { isAdmin } = useAuth();
  const navigate = useNavigate();

  const [buildings, setBuildings] = useState([]);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [balanceSort, setBalanceSort] = useState({ field: "balance", order: "desc" });

  // Redirect non-admins away
  useEffect(() => {
    if (!isAdmin) navigate("/dashboard", { replace: true });
  }, [isAdmin, navigate]);

  // Fetch building list for the selector
  useEffect(() => {
    axiosClient.get("/buildings/").then((r) => setBuildings(r.data.results ?? r.data)).catch(() => {});
  }, []);

  const fetchDashboard = useCallback(() => {
    setLoading(true);
    setError("");
    const params = {};
    if (selectedBuilding) params.building_id = selectedBuilding;
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    axiosClient
      .get("/dashboard/admin/", { params })
      .then((r) => setData(r.data))
      .catch(() => setError("Failed to load dashboard data."))
      .finally(() => setLoading(false));
  }, [selectedBuilding, dateFrom, dateTo]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleBalanceSort = (field) => {
    setBalanceSort((prev) =>
      prev.field === field
        ? { field, order: prev.order === "asc" ? "desc" : "asc" }
        : { field, order: "asc" }
    );
  };

  const sortedUnpaidUnits = [...(data?.unpaid_units ?? [])].sort((a, b) => {
    const { field, order } = balanceSort;
    let aVal = a[field] ?? "";
    let bVal = b[field] ?? "";
    if (field === "balance") {
      aVal = parseFloat(aVal);
      bVal = parseFloat(bVal);
    } else {
      aVal = String(aVal).toLowerCase();
      bVal = String(bVal).toLowerCase();
    }
    if (aVal < bVal) return order === "asc" ? -1 : 1;
    if (aVal > bVal) return order === "asc" ? 1 : -1;
    return 0;
  });

  const incomeValues = data?.monthly_trend?.map((m) => parseFloat(m.income)) ?? [];
  const expenseValues = data?.monthly_trend?.map((m) => parseFloat(m.expenses)) ?? [];
  const hasData = data !== null;

  return (
    <>
    <PrivateSEO title="ABEM – Dashboard" />
    <Box sx={{ p: 3 }}>
      {/* ── Dashboard header banner ── */}
      <Box sx={{ mb: 3 }}>
        <img
          src="/abem-dashboard-header.svg"
          alt=""
          style={{
            width: '100%',
            height: 'auto',
            borderRadius: 8,
            display: 'block',
            transform: isRtl ? 'scaleX(-1)' : 'none',
          }}
        />
      </Box>

      <Typography variant="h4" fontWeight={700} gutterBottom>
        {t("admin_dashboard")}
      </Typography>

      {/* ── Filters ── */}
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel id="building-select-label">{t("building_filter")}</InputLabel>
          <Select
            labelId="building-select-label"
            label={t("building_filter")}
            value={selectedBuilding}
            onChange={(e) => setSelectedBuilding(e.target.value)}
            inputProps={{ "data-testid": "building-selector" }}
          >
            <MenuItem value="">{t("all_buildings")}</MenuItem>
            {buildings.map((b) => (
              <MenuItem key={b.id} value={b.id}>
                {b.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

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
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 6 }}>
          <CircularProgress />
        </Box>
      ) : !hasData ? (
        <Alert severity="info" data-testid="empty-state">
          {t("no_data_available")}
        </Alert>
      ) : (
        <>
          {/* ── Top KPI cards (4 columns) ── */}
          <Grid container spacing={3} sx={{ mb: 3 }}>

            {/* Total Income */}
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="overline" color="text.secondary">{t("total_income")}</Typography>
                  <Typography variant="h5" fontWeight={700} color="success.main" data-testid="total-income">
                    {formatCurrency(data?.total_income ?? 0)}
                  </Typography>
                  <TrendBadge pct={data?.income_change_pct} invertColors={false} />
                </CardContent>
              </Card>
            </Grid>

            {/* Total Expenses */}
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="overline" color="text.secondary">{t("total_expenses")}</Typography>
                  <Typography variant="h5" fontWeight={700} color="warning.main" data-testid="total-expenses">
                    {formatCurrency(data?.total_expenses ?? 0)}
                  </Typography>
                  <TrendBadge pct={data?.expense_change_pct} invertColors={true} />
                </CardContent>
              </Card>
            </Grid>

            {/* Overdue Units */}
            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  cursor: data?.overdue_units_count > 0 ? "pointer" : "default",
                  border: data?.overdue_units_count > 0 ? "2px solid" : undefined,
                  borderColor: data?.overdue_units_count > 0 ? "error.main" : undefined,
                }}
                onClick={() => data?.overdue_units_count > 0 && navigate("/payments")}
                data-testid="overdue-units-card"
              >
                <CardContent>
                  <Typography variant="overline" color="text.secondary">{t("overdue_units")}</Typography>
                  <Typography
                    variant="h5"
                    fontWeight={700}
                    color={data?.overdue_units_count > 0 ? "error.main" : "success.main"}
                    data-testid="overdue-units-count"
                  >
                    {data?.overdue_units_count ?? 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t("units_past_due")}
                  </Typography>
                  {data?.overdue_units_count > 0 && (
                    <Box sx={{ mt: 0.5 }}>
                      <Chip label={t("view_payments")} size="small" color="error" />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Buildings */}
            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{ cursor: "pointer" }}
                onClick={() => navigate("/buildings")}
                data-testid="buildings-card"
              >
                <CardContent>
                  <Typography variant="overline" color="text.secondary">{t("buildings_label")}</Typography>
                  <Typography variant="h5" fontWeight={700} color="primary.main">
                    {data?.building_summary?.total_buildings ?? 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {t("total_units", { count: data?.building_summary?.total_units ?? 0 })}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {t("occupied_units", { count: data?.building_summary?.occupied ?? 0 })}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* ── Payment collection progress ── */}
          {data?.payment_coverage && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t("payment_collection_progress")}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {t("payment_collection_desc")}
                </Typography>
                {data.payment_coverage.total_billed === 0 ? (
                  <Typography variant="body2" color="text.secondary">{t("no_billed_units")}</Typography>
                ) : (
                  <>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 0.5 }}>
                      <Box sx={{ flex: 1 }}>
                        <Tooltip
                          title={`${data.payment_coverage.paid} of ${data.payment_coverage.total_billed} units settled`}
                        >
                          <LinearProgress
                            variant="determinate"
                            value={(data.payment_coverage.paid / data.payment_coverage.total_billed) * 100}
                            color={data.payment_coverage.paid === data.payment_coverage.total_billed ? "success" : "primary"}
                            sx={{ height: 12, borderRadius: 6 }}
                          />
                        </Tooltip>
                      </Box>
                      <Typography variant="body2" fontWeight={600} sx={{ minWidth: 80 }}>
                        {data.payment_coverage.paid} / {data.payment_coverage.total_billed}
                      </Typography>
                      {data.payment_coverage.paid === data.payment_coverage.total_billed && (
                        <Chip label={t("all_paid")} color="success" size="small" />
                      )}
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {t("units_outstanding", { count: data.payment_coverage.total_billed - data.payment_coverage.paid })}
                    </Typography>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* ── Recent Expenses (last 30 days) ── */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>{t("recent_expenses_30_days")}</Typography>
              {(data?.recent_expenses ?? []).length === 0 ? (
                <Typography variant="body2" color="text.secondary">{t("no_expenses_30_days")}</Typography>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: "grey.100" }}>
                        <TableCell><strong>{t("expense")}</strong></TableCell>
                        <TableCell><strong>{t("category")}</strong></TableCell>
                        <TableCell align="right"><strong>{t("amount_egp")}</strong></TableCell>
                        <TableCell align="center"><strong>{t("status")}</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(data?.recent_expenses ?? []).map((row, i) => (
                        <TableRow key={i} hover>
                          <TableCell>{row.title}</TableCell>
                          <TableCell>{t(`categories:${row.category}`, row.category)}</TableCell>
                          <TableCell align="right">
                            {parseFloat(row.amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={{
                                'Paid': t('status_paid'),
                                'Unpaid': t('status_unpaid'),
                                'Partial': t('status_partial'),
                                'Overdue': t('status_overdue'),
                                'paid': t('status_paid'),
                                'unpaid': t('status_unpaid'),
                                'partial': t('status_partial'),
                                'overdue': t('status_overdue'),
                              }[row.status] || row.status}
                              size="small"
                              color={
                                row.status === "Overdue" || row.status === "overdue" ? "error" :
                                row.status === "Paid" || row.status === "paid" ? "success" : "warning"
                              }
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>

          {/* ── Unpaid dues table ── */}
          {data?.unpaid_units?.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t("outstanding_balances")}
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: "grey.100" }}>
                        {[
                          { label: t("unit_col"), field: "unit_number" },
                          { label: t("building_col"), field: "building_name" },
                          { label: t("owner_col"), field: "owner_name" },
                          { label: t("email_col"), field: "owner_email" },
                        ].map(({ label, field }) => (
                          <TableCell key={field}>
                            <TableSortLabel
                              active={balanceSort.field === field}
                              direction={balanceSort.field === field ? balanceSort.order : "asc"}
                              onClick={() => handleBalanceSort(field)}
                            >
                              <strong>{label}</strong>
                            </TableSortLabel>
                          </TableCell>
                        ))}
                        <TableCell align="right">
                          <TableSortLabel
                            active={balanceSort.field === "balance"}
                            direction={balanceSort.field === "balance" ? balanceSort.order : "asc"}
                            onClick={() => handleBalanceSort("balance")}
                          >
                            <strong>{t("balance_due_egp")}</strong>
                          </TableSortLabel>
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {sortedUnpaidUnits.map((row, i) => (
                        <TableRow key={i} hover>
                          <TableCell>{row.unit_number}</TableCell>
                          <TableCell>{row.building_name}</TableCell>
                          <TableCell>{row.owner_name}</TableCell>
                          <TableCell>{row.owner_email}</TableCell>
                          <TableCell align="right" sx={{ color: "error.main", fontWeight: 600 }}>
                            {parseFloat(row.balance).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {/* ── Monthly trend chart ── */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                <Typography variant="h6">{t("monthly_income_vs_expenses")}</Typography>
                <Button size="small" variant="outlined" data-testid="download-report"
                  onClick={() => window.print()}>
                  {t("download_report")}
                </Button>
              </Box>
              <Box
                aria-label="Monthly income and expenses trend bar chart"
                role="img"
                data-testid="monthly-trend-chart"
              >
                <BarChart
                  series={[
                    { data: incomeValues, label: t("income"), color: "#10B981" },
                    { data: expenseValues, label: t("expenses"), color: "#F59E0B" },
                  ]}
                  xAxis={[{ data: MONTH_LABELS, scaleType: "band" }]}
                  height={300}
                  tooltip={{ trigger: "item" }}
                />
              </Box>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
    </>
  );
}
