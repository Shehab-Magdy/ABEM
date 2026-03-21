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
import { useTranslation } from "react-i18next";
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
import { PrivateSEO } from "../../components/seo/SEO";

// ── Constants ──────────────────────────────────────────────────────────────────

const PAYMENT_METHOD_KEYS = [
  { value: "cash", key: "methodCash" },
  { value: "bank_transfer", key: "methodBankTransfer" },
  { value: "cheque", key: "methodCheque" },
  { value: "mobile_wallet", key: "methodMobileWallet" },
  { value: "other", key: "methodOther" },
];

const EMPTY_FORM = {
  apartment_id: "",
  expense_ids: [],
  allocations: {},  // { [expense_id]: allocated_amount_string }
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

function balanceLabel(balance, t) {
  const n = parseFloat(balance) || 0;
  if (n === 0) return t("balanceSettled");
  if (n < 0) return `${t("balanceCredit")}: ${Math.abs(n).toFixed(2)}`;
  return `${t("balanceOwes")}: ${n.toFixed(2)}`;
}

function methodLabel(method, t) {
  const found = PAYMENT_METHOD_KEYS.find((m) => m.value === method);
  return found ? t(found.key) : method;
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function PaymentsPage() {
  const { t } = useTranslation("payments");
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
  const [loadingReceipt, setLoadingReceipt] = useState(null); // payment id currently generating

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
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      // When expense selection changes, pre-populate allocations for newly added expenses
      if (field === "expense_ids") {
        const newAllocations = { ...prev.allocations };
        // Pre-populate newly added expenses with their share_amount for this apartment
        value.forEach((expId) => {
          if (!(expId in newAllocations)) {
            const exp = dialogExpenses.find((e) => e.id === expId);
            const share = exp?.apartment_shares?.find(
              (s) => s.apartment_id === (prev.apartment_id || selectedApartment)
            );
            newAllocations[expId] = share ? parseFloat(share.share_amount).toFixed(2) : "";
          }
        });
        // Remove allocations for deselected expenses
        Object.keys(newAllocations).forEach((key) => {
          if (!value.includes(key)) delete newAllocations[key];
        });
        next.allocations = newAllocations;
      }
      return next;
    });
  };

  // Compute total allocated from the allocations map
  const totalAllocated = Object.values(form.allocations).reduce(
    (sum, val) => sum + (parseFloat(val) || 0), 0
  );
  const amountPaidNum = parseFloat(form.amount_paid) || 0;
  const allocationExceeds = totalAllocated > amountPaidNum && amountPaidNum > 0;
  const creditRemainder = amountPaidNum - totalAllocated;

  const handleSubmit = async () => {
    setFormError("");

    if (allocationExceeds) {
      setFormError(
        t("allocationExceedsPayment", {
          sum: totalAllocated.toFixed(2),
          amount: amountPaidNum.toFixed(2),
        })
      );
      return;
    }

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

    // Build allocations array if any amounts have been entered
    const hasAllocations = Object.values(form.allocations).some((v) => v !== "" && v !== null);
    if (form.expense_ids.length && hasAllocations) {
      payload.allocations = form.expense_ids.map((expId) => ({
        expense_id: expId,
        allocated_amount: form.allocations[expId] ? parseFloat(form.allocations[expId]) : null,
      }));
    }

    setSaving(true);
    try {
      await paymentsApi.create(payload);
      setDialogOpen(false);
      setSnackbar({ open: true, message: t("paymentRecordedSuccess"), severity: "success" });
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
    <>
      <PrivateSEO title="ABEM – Payments" />
      <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={600}>
          {t("title")}
        </Typography>
        {isAdmin && selectedBuilding && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            {t("recordPayment")}
          </Button>
        )}
      </Stack>

      {/* Building + Apartment selectors */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" spacing={2} flexWrap="wrap" alignItems="center">
          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>{t("building")}</InputLabel>
            <Select
              label={t("building")}
              value={selectedBuilding}
              onChange={(e) => setSelectedBuilding(e.target.value)}
            >
              {buildings.map((b) => (
                <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>{t("apartment")}</InputLabel>
            <Select
              label={t("apartment")}
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
              <Typography variant="h6">{t("balanceSummary")}</Typography>
            </Stack>
            <Divider sx={{ mb: 1.5 }} />
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">{t("totalOwed")}</Typography>
                <Typography fontWeight={600}>
                  {parseFloat(balance.total_owed).toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">{t("totalPaid")}</Typography>
                <Typography fontWeight={600}>
                  {parseFloat(balance.total_paid).toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">{t("currentBalance")}</Typography>
                <Chip
                  label={balanceLabel(balance.current_balance, t)}
                  color={balanceColor(balance.current_balance)}
                  size="small"
                />
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">{t("status")}</Typography>
                <Typography variant="body2">
                  {balance.is_credit
                    ? t("statusCreditOverpaid")
                    : parseFloat(balance.current_balance) === 0
                    ? t("balanceSettled")
                    : t("statusOutstanding")}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Payment history table */}
      <TableContainer id="payments-table" component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: "primary.main" }}>
              {[
                { key: "colDate", label: t("colDate") },
                { key: "colAmount", label: t("colAmount") },
                { key: "colMethod", label: t("colMethod") },
                { key: "colNotes", label: t("colNotes") },
                { key: "colBalanceAfter", label: t("colBalanceAfter") },
                { key: "colReceipt", label: t("colReceipt") },
              ].map((h) => (
                <TableCell key={h.key} sx={{ color: "white", fontWeight: 600 }}>
                  {h.label}
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
                    ? t("noPaymentHistory")
                    : t("selectApartmentPrompt")}
                </TableCell>
              </TableRow>
            ) : (
              payments.map((p) => (
                <TableRow key={p.id} hover>
                  <TableCell>{p.payment_date}</TableCell>
                  <TableCell>{parseFloat(p.amount_paid).toFixed(2)}</TableCell>
                  <TableCell>{methodLabel(p.payment_method, t)}</TableCell>
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
                      label={balanceLabel(p.balance_after, t)}
                      color={balanceColor(p.balance_after)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={loadingReceipt === p.id ? <CircularProgress size={14} /> : <PictureAsPdf fontSize="small" />}
                      disabled={loadingReceipt === p.id}
                      data-testid="print-receipt"
                      onClick={async () => {
                        // Open blank tab synchronously (in the click handler)
                        // to avoid popup-blocker issues.
                        const newTab = window.open("", "_blank");
                        setLoadingReceipt(p.id);
                        try {
                          const res = await paymentsApi.receipt(p.id);
                          const blob = new Blob([res.data], { type: "application/pdf" });
                          const url = URL.createObjectURL(blob);
                          if (newTab) {
                            newTab.location.href = url;
                          } else {
                            // Fallback if popup was still blocked
                            window.location.href = url;
                          }
                          setTimeout(() => URL.revokeObjectURL(url), 30000);
                        } catch (err) {
                          if (newTab) newTab.close();
                          const isTimeout = err?.code === "ECONNABORTED" || err?.message?.includes("timeout");
                          let msg = t("receipt_load_error", "Could not load receipt.");
                          if (isTimeout) {
                            msg = t("receipt_timeout", "Receipt generation is taking too long.");
                          } else if (err?.response?.data instanceof Blob) {
                            try {
                              const text = await err.response.data.text();
                              const json = JSON.parse(text);
                              if (json.detail) msg = json.detail;
                            } catch { /* keep default msg */ }
                          }
                          setSnackbar({ open: true, message: msg, severity: "error" });
                        } finally {
                          setLoadingReceipt(null);
                        }
                      }}
                    >
                      {loadingReceipt === p.id ? t("generating") : t("colReceipt")}
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
        <DialogTitle>{t("recordPayment")}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {formError && <Alert severity="error">{formError}</Alert>}

            <FormControl fullWidth size="small" required>
              <InputLabel>{t("unitPayer")} *</InputLabel>
              <Select
                label={`${t("unitPayer")} *`}
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
              label={t("amountPaid")}
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
              label={t("paymentDate")}
              type="date"
              value={form.payment_date}
              onChange={(e) => handleFormChange("payment_date", e.target.value)}
              required
              fullWidth
              size="small"
              InputLabelProps={{ shrink: true }}
            />

            <FormControl fullWidth size="small">
              <InputLabel>{t("paymentMethod")}</InputLabel>
              <Select
                label={t("paymentMethod")}
                value={form.payment_method}
                onChange={(e) => handleFormChange("payment_method", e.target.value)}
              >
                {PAYMENT_METHOD_KEYS.map((m) => (
                  <MenuItem key={m.value} value={m.value}>{t(m.key)}</MenuItem>
                ))}
              </Select>
            </FormControl>

            {form.payment_method === "other" && (
              <TextField
                label={`${t("specifyPaymentMethod")} *`}
                placeholder={t("method_placeholder", "e.g. Mobile Wallet, Instalment…")}
                value={form.other_method_detail}
                onChange={(e) => handleFormChange("other_method_detail", e.target.value)}
                required
                fullWidth
                size="small"
              />
            )}

            <FormControl fullWidth size="small">
              <InputLabel>{t("expensesOptional")}</InputLabel>
              <Select
                label={t("expensesOptional")}
                multiple
                value={form.expense_ids}
                onChange={(e) => handleFormChange("expense_ids", e.target.value)}
                input={<OutlinedInput label={t("expensesOptional")} />}
                renderValue={(selected) =>
                  selected.length === 0
                    ? <em>{t("generalPayment")}</em>
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
                  <MenuItem disabled><em>{t("noExpensesForBuilding")}</em></MenuItem>
                )}
              </Select>
              {form.expense_ids.length === 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, ml: 1.5 }}>
                  {t("noSelectionGeneralPayment")}
                </Typography>
              )}
            </FormControl>

            {/* ── Per-expense allocation inputs ──────────────────────── */}
            {form.expense_ids.length > 1 && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  {t("allocation")}
                </Typography>
                <Stack spacing={1.5}>
                  {form.expense_ids.map((expId) => {
                    const exp = dialogExpenses.find((e) => e.id === expId);
                    return (
                      <Stack key={expId} direction="row" alignItems="center" spacing={1}>
                        <Typography variant="body2" sx={{ flex: 1, minWidth: 0 }} noWrap>
                          {exp ? exp.title : expId}
                        </Typography>
                        <TextField
                          label={t("allocatedAmount")}
                          type="number"
                          inputProps={{ min: 0, step: 0.01 }}
                          value={form.allocations[expId] ?? ""}
                          onChange={(e) =>
                            setForm((prev) => ({
                              ...prev,
                              allocations: { ...prev.allocations, [expId]: e.target.value },
                            }))
                          }
                          size="small"
                          sx={{ width: 140 }}
                        />
                      </Stack>
                    );
                  })}
                  <Divider />
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2" fontWeight={600}>
                      {t("totalAllocated")}
                    </Typography>
                    <Typography
                      variant="body2"
                      fontWeight={600}
                      color={allocationExceeds ? "error" : "text.primary"}
                    >
                      {totalAllocated.toFixed(2)}
                    </Typography>
                  </Stack>
                  {creditRemainder > 0 && !allocationExceeds && (
                    <Stack direction="row" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">
                        {t("creditRemainder")}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {creditRemainder.toFixed(2)}
                      </Typography>
                    </Stack>
                  )}
                  {allocationExceeds && (
                    <Alert severity="error" sx={{ py: 0 }}>
                      {t("allocationExceedsPayment", {
                        sum: totalAllocated.toFixed(2),
                        amount: amountPaidNum.toFixed(2),
                      })}
                    </Alert>
                  )}
                </Stack>
              </Paper>
            )}

            <TextField
              label={t("notes")}
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
            {t("cancel")}
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={saving || !form.amount_paid || !form.payment_date || !form.apartment_id || (form.payment_method === "other" && !form.other_method_detail) || allocationExceeds}
          >
            {saving ? <CircularProgress size={18} /> : t("record")}
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
    </>
  );
}
