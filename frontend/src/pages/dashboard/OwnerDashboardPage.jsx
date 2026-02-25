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
} from "@mui/material";
import { PieChart } from "@mui/x-charts/PieChart";
import axiosClient from "../../api/axiosClient";

export default function OwnerDashboardPage() {
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

  const balance = parseFloat(data?.balance_summary?.current_balance ?? 0);
  const isCredit = balance < 0;
  const isSettled = balance === 0;

  const pieData = (data?.expense_breakdown ?? []).map((row, idx) => ({
    id: idx,
    value: parseFloat(row.total),
    label: row.category_name,
  }));

  const hasPayments = (data?.recent_payments ?? []).length > 0;
  const hasBreakdown = pieData.length > 0;
  // Show content sections whenever data is loaded (even with zeros)
  const dataLoaded = data !== null;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Owner Dashboard
      </Typography>

      {/* ── Filters ── */}
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 3 }}>
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
        <Button size="small" variant="outlined" data-testid="download-report"
          onClick={() => window.print()}>
          Download Report
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 6 }}>
          <CircularProgress />
        </Box>
      ) : !dataLoaded ? (
        <Alert severity="info" data-testid="empty-state">
          No data available for the selected period.
        </Alert>
      ) : (
        <>
          {/* ── Balance summary ── */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Balance Summary</Typography>
              <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap", alignItems: "center" }}>
                <Box>
                  <Typography variant="overline" color="text.secondary">Current Balance</Typography>
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
                      <Chip label="Credit" size="small" color="info" data-testid="credit-label" />
                    )}
                    {isSettled && (
                      <Chip label="Settled" size="small" color="success" data-testid="settled-label" />
                    )}
                    {!isCredit && !isSettled && (
                      <Chip label="Owed" size="small" color="error" data-testid="owed-label" />
                    )}
                  </Box>
                </Box>
                <Box>
                  <Typography variant="overline" color="text.secondary">Total Paid (YTD)</Typography>
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
                    <Typography variant="h6" gutterBottom>Expense Breakdown</Typography>
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
                  <Typography variant="h6" gutterBottom>Recent Payments</Typography>
                  {!hasPayments ? (
                    <Typography color="text.secondary">No payments yet.</Typography>
                  ) : (
                    <Paper variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Date</TableCell>
                            <TableCell>Amount</TableCell>
                            <TableCell>Method</TableCell>
                            <TableCell>Notes</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {(data?.recent_payments ?? []).map((p) => (
                            <TableRow key={p.id}>
                              <TableCell>{p.payment_date}</TableCell>
                              <TableCell>
                                {parseFloat(p.amount_paid).toLocaleString()} EGP
                              </TableCell>
                              <TableCell>{p.payment_method}</TableCell>
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
  );
}
