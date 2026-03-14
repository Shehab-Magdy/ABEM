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
  MenuItem,
  Select,
  TextField,
  Typography,
  Alert,
  Button,
} from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import axiosClient from "../../api/axiosClient";

const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export default function AdminDashboardPage() {
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
  // Show content sections whenever data is loaded (even with zero values)
  const hasData = data !== null;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Admin Dashboard
      </Typography>

      {/* ── Filters ── */}
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel id="building-select-label">Building</InputLabel>
          <Select
            labelId="building-select-label"
            label="Building"
            value={selectedBuilding}
            onChange={(e) => setSelectedBuilding(e.target.value)}
            inputProps={{ "data-testid": "building-selector" }}
          >
            <MenuItem value="">All Buildings</MenuItem>
            {buildings.map((b) => (
              <MenuItem key={b.id} value={b.id}>
                {b.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          size="small"
          label="Date From"
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          InputLabelProps={{ shrink: true }}
          inputProps={{ "data-testid": "date-from" }}
        />
        <TextField
          size="small"
          label="Date To"
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
          No data available for the selected period.
        </Alert>
      ) : (
        <>
          {/* ── Summary cards ── */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography variant="overline" color="text.secondary">
                    Total Income
                  </Typography>
                  <Typography variant="h5" fontWeight={700} color="success.main" data-testid="total-income">
                    {parseFloat(data?.total_income ?? 0).toLocaleString()} EGP
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography variant="overline" color="text.secondary">
                    Total Expenses
                  </Typography>
                  <Typography variant="h5" fontWeight={700} color="warning.main" data-testid="total-expenses">
                    {parseFloat(data?.total_expenses ?? 0).toLocaleString()} EGP
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Card
                sx={{
                  cursor: data?.overdue_count > 0 ? "pointer" : "default",
                  border: data?.overdue_count > 0 ? "2px solid" : undefined,
                  borderColor: data?.overdue_count > 0 ? "error.main" : undefined,
                }}
                onClick={() => data?.overdue_count > 0 && navigate("/buildings")}
                data-testid="overdue-card"
              >
                <CardContent>
                  <Typography variant="overline" color="text.secondary">
                    Overdue Accounts
                  </Typography>
                  <Typography
                    variant="h5"
                    fontWeight={700}
                    color={data?.overdue_count > 0 ? "error.main" : "success.main"}
                    data-testid="overdue-count"
                  >
                    {data?.overdue_count ?? 0}
                  </Typography>
                  {data?.overdue_count > 0 && (
                    <Chip label="Click to view" size="small" color="error" sx={{ mt: 1 }} />
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* ── Building summary ── */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Building Summary</Typography>
              <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                <Box>
                  <Typography variant="overline" color="text.secondary">Buildings</Typography>
                  <Typography variant="h6">{data?.building_summary?.total_buildings ?? 0}</Typography>
                </Box>
                <Box>
                  <Typography variant="overline" color="text.secondary">Apartments</Typography>
                  <Typography variant="h6">{data?.building_summary?.total_apartments ?? 0}</Typography>
                </Box>
                <Box>
                  <Typography variant="overline" color="text.secondary">Occupied</Typography>
                  <Typography variant="h6" color="success.main">{data?.building_summary?.occupied ?? 0}</Typography>
                </Box>
                <Box>
                  <Typography variant="overline" color="text.secondary">Vacant</Typography>
                  <Typography variant="h6" color="text.secondary">{data?.building_summary?.vacant ?? 0}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* ── Monthly trend chart ── */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                <Typography variant="h6">Monthly Income vs Expenses</Typography>
                <Button size="small" variant="outlined" data-testid="download-report"
                  onClick={() => window.print()}>
                  Download Report
                </Button>
              </Box>
              <Box
                aria-label="Monthly income and expenses trend bar chart"
                role="img"
                data-testid="monthly-trend-chart"
              >
                <BarChart
                  series={[
                    { data: incomeValues, label: "Income", color: "#10B981" },
                    { data: expenseValues, label: "Expenses", color: "#F59E0B" },
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
  );
}
