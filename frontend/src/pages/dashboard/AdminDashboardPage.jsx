/**
 * Admin Dashboard — Sprint 5.
 * Shows building-wide financial overview: totals, overdue count, monthly trend, building summary.
 */
import { useTheme } from "@mui/material/styles";
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
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
  Alert,
  Button,
} from "@mui/material";
import { TrendingUp, TrendingDown, WhatsApp } from "@mui/icons-material";
import { BarChart } from "@mui/x-charts/BarChart";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../hooks/useAuth";
import axiosClient from "../../api/axiosClient";
import { formatCurrency, formatNumber, whatsappLink } from "../../utils/formatters";
import DataTable from "../../components/DataTable";
import { PrivateSEO } from "../../components/seo/SEO";
import TreasuryCard from "../../components/TreasuryCard";
import PendingClaimsCard from "../../components/PendingClaimsCard";
import UnitClaimRequestsCard from "../../components/UnitClaimRequestsCard";

const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function TrendBadge({ pct, invertColors }) {
  const { t } = useTranslation("dashboard");
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
        <bdi dir="ltr">{up ? "+" : ""}{formatNumber(pct)}%</bdi> {t("vs_last_month")}
      </Typography>
    </Box>
  );
}

export default function AdminDashboardPage() {
  const theme = useTheme();
  const { t } = useTranslation("dashboard");
  const { isAdmin } = useAuth();
  const navigate = useNavigate();

  const [buildings, setBuildings] = useState([]);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  const incomeValues = data?.monthly_trend?.map((m) => parseFloat(m.income)) ?? [];
  const expenseValues = data?.monthly_trend?.map((m) => parseFloat(m.expenses)) ?? [];
  const hasData = data !== null;

  return (
    <>
    <PrivateSEO title="3maracom – Dashboard" />
    <Box sx={{ p: 3 }}>
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
          <UnitClaimRequestsCard />

          <PendingClaimsCard />

          <TreasuryCard />

          {/* ── Top KPI cards (4 columns) ── */}
          <Grid container spacing={3} sx={{ mb: 3 }}>

            {/* Total Income */}
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ height: "100%", border: "2px solid transparent" }}>
                <CardContent>
                  <Typography variant="overline" color="text.secondary">{t("total_income")}</Typography>
                  <Typography variant="h5" fontWeight={700} color="success.main" data-testid="total-income">
                    {formatCurrency(data?.total_income ?? 0)}
                  </Typography>
                  <TrendBadge pct={data?.income_change_pct} invertColors={false} />
                  <Stack spacing={0.25} sx={{ mt: 1 }}>
                    {parseFloat(data?.starting_balance ?? 0) !== 0 && (
                      <Typography variant="caption" color={parseFloat(data?.starting_balance ?? 0) < 0 ? "error.main" : "text.secondary"}>
                        {parseFloat(data?.starting_balance ?? 0) < 0 ? t("opening_deficit") : t("starting_balance")}: {formatCurrency(data?.starting_balance ?? 0)}
                      </Typography>
                    )}
                    <Typography variant="caption" color="text.secondary">
                      {t("payments_income")}: {formatCurrency(data?.payment_income ?? 0)}
                    </Typography>
                    {parseFloat(data?.asset_sale_income ?? 0) > 0 && (
                      <Typography variant="caption" color="text.secondary">
                        {t("asset_sale_income")}: {formatCurrency(data?.asset_sale_income ?? 0)}
                      </Typography>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* Total Expenses */}
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ height: "100%", border: "2px solid transparent" }}>
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
                  height: "100%",
                  cursor: data?.overdue_units_count > 0 ? "pointer" : "default",
                  border: "2px solid",
                  borderColor: data?.overdue_units_count > 0 ? "error.main" : "transparent",
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
                sx={{ height: "100%", cursor: "pointer", border: "2px solid transparent" }}
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
                          title={t("units_settled_of", { paid: data.payment_coverage.paid, total: data.payment_coverage.total_billed })}
                        >
                          <LinearProgress
                            variant="determinate"
                            value={(data.payment_coverage.paid / data.payment_coverage.total_billed) * 100}
                            color={data.payment_coverage.paid === data.payment_coverage.total_billed ? "success" : "primary"}
                            sx={{ height: 12, borderRadius: 6 }}
                          />
                        </Tooltip>
                      </Box>
                      <Typography variant="body2" fontWeight={600} sx={{ minWidth: 80, whiteSpace: "nowrap" }}>
                        {t("progress_of", { paid: formatNumber(data.payment_coverage.paid), total: formatNumber(data.payment_coverage.total_billed) })}
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
                <DataTable
                  size="small"
                  rowKey={(row, i) => i}
                  rows={data?.recent_expenses ?? []}
                  searchable={false}
                  pagination={false}
                  minWidth={0}
                  testId="recent-expenses-table"
                  columns={[
                    { id: "title", label: t("expense") },
                    {
                      id: "category",
                      label: t("category"),
                      sortValue: (row) => t(`categories:${row.category}`, row.category),
                      render: (row) => t(`categories:${row.category}`, row.category),
                    },
                    {
                      id: "amount",
                      label: t("amount_egp"),
                      align: "right",
                      sortValue: (row) => parseFloat(row.amount),
                      render: (row) => parseFloat(row.amount).toLocaleString("en-US", { minimumFractionDigits: 2 }),
                    },
                    {
                      id: "status",
                      label: t("status"),
                      align: "center",
                      render: (row) => (
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
                      ),
                    },
                  ]}
                />
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
                <DataTable
                  size="small"
                  rowKey={(row, i) => `${row.unit_number}-${row.building_name}-${i}`}
                  rows={data.unpaid_units}
                  initialSort={{ id: "balance", direction: "desc" }}
                  testId="unpaid-units-table"
                  columns={[
                    { id: "unit_number", label: t("unit_col") },
                    { id: "building_name", label: t("building_col"), hideOnMobile: true },
                    { id: "owner_name", label: t("owner_col") },
                    { id: "owner_email", label: t("email_col"), hideOnMobile: true },
                    {
                      id: "remind",
                      label: t("remind_col"),
                      sortable: false,
                      render: (row) => {
                        const link = whatsappLink(
                          row.owner_phone,
                          t("remind_whatsapp_text", {
                            name: row.owner_name,
                            building: row.building_name,
                            unit: row.unit_number,
                            amount: formatCurrency(row.balance),
                          }),
                        );
                        return link ? (
                          <Button
                            size="small"
                            color="success"
                            variant="outlined"
                            startIcon={<WhatsApp fontSize="small" />}
                            href={link}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ minHeight: 44 }}
                          >
                            {t("remind_whatsapp")}
                          </Button>
                        ) : (
                          <Typography variant="caption" color="text.disabled">{t("remind_no_phone")}</Typography>
                        );
                      },
                    },
                    {
                      id: "balance",
                      label: t("balance_due_egp"),
                      align: "right",
                      sortValue: (row) => parseFloat(row.balance),
                      searchValue: (row) => String(row.balance),
                      cellSx: { color: "error.main", fontWeight: 600 },
                      render: (row) => parseFloat(row.balance).toLocaleString("en-US", { minimumFractionDigits: 2 }),
                    },
                  ]}
                />
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
                    { data: incomeValues, label: t("income"), color: theme.palette.success.main },
                    { data: expenseValues, label: t("expenses"), color: theme.palette.warning.main },
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

