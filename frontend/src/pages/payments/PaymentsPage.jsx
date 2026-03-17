/**
 * Payments management page – Sprint 4.
 *
 * Features:
 * - Building selector → Apartment selector (filtered by building)
 * - Balance summary card: current balance with color coding
 * - Payment history table: Date | Amount | Method | Notes | Balance After
 * - Record Payment dialog (admin only)
 */
import { useEffect, useState, useCallback } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Paper,
  Select,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { Add as AddIcon, AccountBalance as BalanceIcon, PictureAsPdf } from "@mui/icons-material";
import { paymentsApi } from "../../api/paymentsApi";
import { buildingsApi } from "../../api/buildingsApi";
import { expensesApi } from "../../api/expensesApi";
import axiosClient from "../../api/axiosClient";
import { useAuth } from "../../hooks/useAuth";

// ── Constants ──────────────────────────────────────────────────────────────────

const PAYMENT_METHODS = [
  { value: "cash", label: "Cash" },
  { value: "bank_transfer", label: "Bank Transfer" },
  { value: "cheque", label: "Cheque" },
  { value: "other", label: "Other" },
];

const EMPTY_FORM = {
  apartment_id: "",
  expense_ids: [],
  amount_paid: "",
  payment_date: new Date().toISOString().slice(0, 10),
  payment_method: "cash",
  other_method_detail: "",
  notes: "",
};

// ── Helpers ────────────────────────────────────────────────────────────────────

function balanceColor(balance) {
  const n = parseFloat(balance) || 0;
  if (n === 0) return "success";
  if (n < 0) return "info";    // credit
  return "error";              // owes money
}

function balanceLabel(balance) {
  const n = parseFloat(balance) || 0;
  if (n === 0) return "Settled";
  if (n < 0) return `Credit: ${Math.abs(n).toFixed(2)}`;
  return `Owes: ${n.toFixed(2)}`;
}

function methodLabel(method) {
  return PAYMENT_METHODS.find((m) => m.value === method)?.label ?? method;
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function PaymentsPage() {
  const { isAdmin } = useAuth();

  const [buildings, setBuildings] = useState([]);
  const [apartments, setApartments] = useState([]);
  const [payments, setPayments] = useState([]);
  const [balance, setBalance] = useState(null);

  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [selectedApartment, setSelectedApartment] = useState("");

  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: "", severity: "success" });
  const [dialogExpenses, setDialogExpenses] = useState([]);

  // ── Data fetching ────────────────────────────────────────────────────────────

  const loadBuildings = useCallback(async () => {
    try {
      const res = await buildingsApi.list();
      const list = res.data?.results ?? res.data ?? [];
      setBuildings(list);
      if (list.length > 0 && !selectedBuilding) {
        setSelectedBuilding(list[0].id);
      }
    } catch {
      /* ignore */
    }
  }, [selectedBuilding]);

  const loadApartments = useCallback(async (buildingId) => {
    if (!buildingId) return;
    try {
      const res = await axiosClient.get("/apartments/", { params: { building_id: buildingId } });
      const list = res.data?.results ?? res.data ?? [];
      setApartments(list);
      setSelectedApartment(list.length > 0 ? list[0].id : "");
    } catch {
      setApartments([]);
    }
  }, []);

  const loadPayments = useCallback(async (apartmentId) => {
    if (!apartmentId) return;
    setLoading(true);
    try {
      const res = await paymentsApi.list({ apartment_id: apartmentId });
      setPayments(res.data?.results ?? res.data ?? []);
    } catch {
      setPayments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBalance = useCallback(async (apartmentId) => {
    if (!apartmentId) return;
    try {
      const res = await paymentsApi.getApartmentBalance(apartmentId);
      setBalance(res.data);
    } catch {
      setBalance(null);
    }
  }, []);

  useEffect(() => { loadBuildings(); }, []);
  useEffect(() => { if (selectedBuilding) loadApartments(selectedBuilding); }, [selectedBuilding]);
  useEffect(() => {
    if (selectedApartment) {
      loadPayments(selectedApartment);
      loadBalance(selectedApartment);
    } else {
      setPayments([]);
      setBalance(null);
    }
  }, [selectedApartment]);

  // ── Dialog helpers ───────────────────────────────────────────────────────────

  const openCreate = async () => {
    const currentBalance = parseFloat(balance?.current_balance) || 0;
    setForm({
      ...EMPTY_FORM,
      apartment_id: selectedApartment,
      amount_paid: currentBalance > 0 ? currentBalance.toFixed(2) : "",
    });
    setFormError("");
    setDialogOpen(true);
    // Load expenses for the building of the selected apartment
    const apt = apartments.find((a) => a.id === selectedApartment);
    if (apt?.building_id) {
      try {
        const res = await expensesApi.list({ building_id: apt.building_id, page_size: 200 });
        setDialogExpenses(res.data?.results ?? res.data ?? []);
      } catch {
        setDialogExpenses([]);
      }
    } else {
      setDialogExpenses([]);
    }
  };

  const handleFormChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setFormError("");
    const notesWithMethod =
      form.payment_method === "other" && form.other_method_detail.trim()
        ? `[Method: ${form.other_method_detail.trim()}]${form.notes.trim() ? " " + form.notes.trim() : ""}`
        : form.notes.trim();
    const payload = {
      apartment_id: form.apartment_id || selectedApartment,
      amount_paid: parseFloat(form.amount_paid),
      payment_date: form.payment_date,
      payment_method: form.payment_method,
      notes: notesWithMethod,
    };
    if (form.expense_ids.length) payload.expense_ids = form.expense_ids;

    setSaving(true);
    try {
      await paymentsApi.create(payload);
      setDialogOpen(false);
      setSnackbar({ open: true, message: "Payment recorded successfully.", severity: "success" });
      await Promise.all([loadPayments(selectedApartment), loadBalance(selectedApartment)]);
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        JSON.stringify(err.response?.data) ||
        "An error occurred.";
      setFormError(detail);
    } finally {
      setSaving(false);
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={600}>
          Payments
        </Typography>
        {isAdmin && selectedBuilding && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            Record Payment
          </Button>
        )}
      </Stack>

      {/* Building + Apartment selectors */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" spacing={2} flexWrap="wrap" alignItems="center">
          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>Building</InputLabel>
            <Select
              label="Building"
              value={selectedBuilding}
              onChange={(e) => setSelectedBuilding(e.target.value)}
            >
              {buildings.map((b) => (
                <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>Apartment</InputLabel>
            <Select
              label="Apartment"
              value={selectedApartment}
              onChange={(e) => setSelectedApartment(e.target.value)}
              disabled={apartments.length === 0}
            >
              {apartments.map((a) => (
                <MenuItem key={a.id} value={a.id}>
                  Unit {a.unit_number}{a.owner_names?.length > 0 ? ` — ${a.owner_names.join(", ")}` : ""}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      {/* Balance summary card */}
      {balance && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction="row" alignItems="center" spacing={1} mb={1}>
              <BalanceIcon color="primary" />
              <Typography variant="h6">Balance Summary</Typography>
            </Stack>
            <Divider sx={{ mb: 1.5 }} />
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">Total Owed</Typography>
                <Typography fontWeight={600}>
                  {parseFloat(balance.total_owed).toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">Total Paid</Typography>
                <Typography fontWeight={600}>
                  {parseFloat(balance.total_paid).toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">Current Balance</Typography>
                <Chip
                  label={balanceLabel(balance.current_balance)}
                  color={balanceColor(balance.current_balance)}
                  size="small"
                />
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">Status</Typography>
                <Typography variant="body2">
                  {balance.is_credit
                    ? "Credit (Overpaid)"
                    : parseFloat(balance.current_balance) === 0
                    ? "Settled"
                    : "Outstanding"}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Payment history table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: "primary.main" }}>
              {["Date", "Amount", "Method", "Notes", "Balance After", "Receipt"].map((h) => (
                <TableCell key={h} sx={{ color: "white", fontWeight: 600 }}>
                  {h}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            ) : payments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={isAdmin ? 6 : 5} align="center" sx={{ py: 4, color: "text.secondary" }}>
                  {selectedApartment
                    ? "No payment history for this apartment."
                    : "Select an apartment to view payment history."}
                </TableCell>
              </TableRow>
            ) : (
              payments.map((p) => (
                <TableRow key={p.id} hover>
                  <TableCell>{p.payment_date}</TableCell>
                  <TableCell>{parseFloat(p.amount_paid).toFixed(2)}</TableCell>
                  <TableCell>{methodLabel(p.payment_method)}</TableCell>
                  <TableCell
                    sx={{
                      maxWidth: 200,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {p.notes || "—"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={balanceLabel(p.balance_after)}
                      color={balanceColor(p.balance_after)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<PictureAsPdf fontSize="small" />}
                      data-testid="print-receipt"
                      onClick={async () => {
                        try {
                          const res = await paymentsApi.receipt(p.id);
                          const blob = new Blob([res.data], { type: "application/pdf" });
                          const url = URL.createObjectURL(blob);
                          const link = document.createElement("a");
                          link.href = url;
                          link.target = "_blank";
                          link.rel = "noopener noreferrer";
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                          setTimeout(() => URL.revokeObjectURL(url), 10000);
                        } catch (err) {
                          if (err?.response?.status === 401) {
                            alert("Session expired. Please log in again.");
                            window.location.replace("/login");
                          } else {
                            alert("Could not load receipt. Please try again.");
                          }
                        }
                      }}
                    >
                      Receipt
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Record Payment dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Record Payment</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {formError && <Alert severity="error">{formError}</Alert>}

            <FormControl fullWidth size="small" required>
              <InputLabel>Unit / Payer *</InputLabel>
              <Select
                label="Unit / Payer *"
                value={form.apartment_id}
                onChange={(e) => handleFormChange("apartment_id", e.target.value)}
              >
                {apartments.map((a) => (
                  <MenuItem key={a.id} value={a.id}>
                    Unit {a.unit_number}{a.type === "store" ? " (Store)" : ""}
                    {a.owner_names?.length > 0 ? ` — ${a.owner_names.join(", ")}` : " — (Unoccupied)"}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Amount Paid"
              type="number"
              inputProps={{ min: 0.01, step: 0.01 }}
              value={form.amount_paid}
              onChange={(e) => handleFormChange("amount_paid", e.target.value)}
              required
              fullWidth
              size="small"
              helperText={
                balance && parseFloat(balance.current_balance) > 0
                  ? `Current balance: ${parseFloat(balance.current_balance).toFixed(2)} — adjust if paying a different amount`
                  : undefined
              }
            />

            <TextField
              label="Payment Date"
              type="date"
              value={form.payment_date}
              onChange={(e) => handleFormChange("payment_date", e.target.value)}
              required
              fullWidth
              size="small"
              InputLabelProps={{ shrink: true }}
            />

            <FormControl fullWidth size="small">
              <InputLabel>Payment Method</InputLabel>
              <Select
                label="Payment Method"
                value={form.payment_method}
                onChange={(e) => handleFormChange("payment_method", e.target.value)}
              >
                {PAYMENT_METHODS.map((m) => (
                  <MenuItem key={m.value} value={m.value}>{m.label}</MenuItem>
                ))}
              </Select>
            </FormControl>

            {form.payment_method === "other" && (
              <TextField
                label="Specify payment method *"
                placeholder="e.g. Mobile Wallet, Instalment…"
                value={form.other_method_detail}
                onChange={(e) => handleFormChange("other_method_detail", e.target.value)}
                required
                fullWidth
                size="small"
              />
            )}

            <FormControl fullWidth size="small">
              <InputLabel>Expenses (optional)</InputLabel>
              <Select
                label="Expenses (optional)"
                multiple
                value={form.expense_ids}
                onChange={(e) => handleFormChange("expense_ids", e.target.value)}
                input={<OutlinedInput label="Expenses (optional)" />}
                renderValue={(selected) =>
                  selected.length === 0
                    ? <em>General payment</em>
                    : selected.map((id) => {
                        const exp = dialogExpenses.find((e) => e.id === id);
                        return exp ? exp.title : id;
                      }).join(", ")
                }
              >
                {dialogExpenses.map((exp) => (
                  <MenuItem key={exp.id} value={exp.id}>
                    <Checkbox checked={form.expense_ids.includes(exp.id)} />
                    <ListItemText
                      primary={exp.title}
                      secondary={`${parseFloat(exp.amount).toFixed(2)} EGP · ${exp.expense_date}`}
                    />
                  </MenuItem>
                ))}
                {dialogExpenses.length === 0 && (
                  <MenuItem disabled><em>No expenses for this building</em></MenuItem>
                )}
              </Select>
              {form.expense_ids.length === 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, ml: 1.5 }}>
                  No selection = general payment
                </Typography>
              )}
            </FormControl>

            <TextField
              label="Notes"
              multiline
              rows={2}
              value={form.notes}
              onChange={(e) => handleFormChange("notes", e.target.value)}
              fullWidth
              size="small"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={saving || !form.amount_paid || !form.payment_date || !form.apartment_id || (form.payment_method === "other" && !form.other_method_detail)}
          >
            {saving ? <CircularProgress size={18} /> : "Record"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
      >
        <Alert severity={snackbar.severity} sx={{ width: "100%" }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
