/**
 * Expenses management page – Sprint 3.
 *
 * Features:
 * - List expenses for the selected building (admin sees all, owner read-only)
 * - Add / Edit expense with split type selector and recurring option
 * - Delete with confirmation (admin only)
 * - Bill image / PDF upload (admin only)
 * - Filter by date range and category
 * - Expense detail panel with per-unit share breakdown
 */
import { useEffect, useState, useCallback } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableFooter,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  Add as AddIcon,
  AttachFile as AttachFileIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  FilterList as FilterIcon,
  Repeat as RepeatIcon,
  Visibility as ViewIcon,
} from "@mui/icons-material";
import { expensesApi } from "../../api/expensesApi";
import { buildingsApi } from "../../api/buildingsApi";
import { useAuth } from "../../hooks/useAuth";

// ── Constants ──────────────────────────────────────────────────────────────────

const SPLIT_TYPES = [
  { value: "equal_all", label: "Equal – All Units" },
  { value: "equal_apartments", label: "Equal – Apartments Only" },
  { value: "equal_stores", label: "Equal – Stores Only" },
  { value: "custom", label: "Custom Subset" },
];

const FREQUENCIES = [
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "annual", label: "Annual" },
];

const EMPTY_FORM = {
  title: "",
  description: "",
  amount: "",
  expense_date: new Date().toISOString().slice(0, 10),
  due_date: "",
  split_type: "equal_all",
  is_recurring: false,
  frequency: "",
  category_id: "",
  building_id: "",
};

// ── Helpers ────────────────────────────────────────────────────────────────────

function statusChip(expense) {
  const shares = expense.apartment_shares || [];
  if (!shares.length) return <Chip label="No Split" size="small" color="default" />;
  return <Chip label="Unpaid" size="small" color="error" />;
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function ExpensesPage() {
  const { isAdmin } = useAuth();

  const [buildings, setBuildings] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBuilding, setSelectedBuilding] = useState("");

  const [detailExpense, setDetailExpense] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [uploadTarget, setUploadTarget] = useState(null);
  const [snack, setSnack] = useState({ open: false, msg: "", severity: "success" });

  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");
  const [filterCategory, setFilterCategory] = useState("");

  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState("");
  const [subcategoryId, setSubcategoryId] = useState("");

  // ── Data fetching ──────────────────────────────────────────────────────────

  const loadBuildings = useCallback(async () => {
    try {
      const res = await buildingsApi.list();
      const list = res.data.results ?? res.data;
      setBuildings(list);
      if (list.length > 0) setSelectedBuilding((prev) => prev || list[0].id);
    } catch {
      /* ignore */
    }
  }, []);

  const loadExpenses = useCallback(async () => {
    if (!selectedBuilding) return;
    setLoading(true);
    try {
      const params = { building_id: selectedBuilding };
      if (filterDateFrom) params.date_from = filterDateFrom;
      if (filterDateTo) params.date_to = filterDateTo;
      if (filterCategory) params.category_id = filterCategory;
      const res = await expensesApi.list(params);
      setExpenses(res.data.results ?? res.data);
    } catch {
      setSnack({ open: true, msg: "Failed to load expenses", severity: "error" });
    } finally {
      setLoading(false);
    }
  }, [selectedBuilding, filterDateFrom, filterDateTo, filterCategory]);

  const loadCategories = useCallback(async () => {
    if (!selectedBuilding) return;
    try {
      const res = await expensesApi.listCategories(selectedBuilding);
      setCategories(res.data.results ?? res.data);
    } catch {
      /* ignore */
    }
  }, [selectedBuilding]);

  useEffect(() => {
    loadBuildings();
  }, [loadBuildings]);

  useEffect(() => {
    loadExpenses();
    loadCategories();
  }, [loadExpenses, loadCategories]);

  // ── Form helpers ───────────────────────────────────────────────────────────

  const openCreate = () => {
    setEditTarget(null);
    setForm({ ...EMPTY_FORM, building_id: selectedBuilding });
    setFormError("");
    setSubcategoryId("");
    setFormOpen(true);
  };

  const openEdit = (expense) => {
    setEditTarget(expense);
    setSubcategoryId("");
    setForm({
      title: expense.title || "",
      description: expense.description || "",
      amount: expense.amount || "",
      expense_date: expense.expense_date || "",
      due_date: expense.due_date || "",
      split_type: expense.split_type || "equal_all",
      is_recurring: expense.is_recurring || false,
      frequency: expense.recurring_config?.frequency || "",
      category_id: expense.category_id || "",
      building_id: expense.building_id || selectedBuilding,
    });
    setFormError("");
    setFormOpen(true);
  };

  const handleFormChange = (field) => (e) => {
    const val = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [field]: val }));
  };

  const handleFormSubmit = async () => {
    if (!form.title.trim()) return setFormError("Title is required");
    if (!form.amount || parseFloat(form.amount) <= 0) return setFormError("Amount must be > 0");
    if (!form.expense_date) return setFormError("Date is required");
    if (!form.category_id) return setFormError("Category is required");

    // Use subcategory if selected, otherwise use the parent category
    const effectiveCategoryId = subcategoryId || form.category_id;

    const payload = {
      title: form.title,
      description: form.description,
      amount: form.amount,
      expense_date: form.expense_date,
      split_type: form.split_type,
      is_recurring: form.is_recurring,
      category_id: effectiveCategoryId,
      building_id: form.building_id || selectedBuilding,
    };
    if (form.due_date) payload.due_date = form.due_date;
    if (form.is_recurring && form.frequency) payload.frequency = form.frequency;

    try {
      if (editTarget) {
        await expensesApi.update(editTarget.id, payload);
        setSnack({ open: true, msg: "Expense updated", severity: "success" });
      } else {
        await expensesApi.create(payload);
        setSnack({ open: true, msg: "Expense created", severity: "success" });
      }
      setFormOpen(false);
      loadExpenses();
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        JSON.stringify(err.response?.data) ||
        "Error saving expense";
      setFormError(detail);
    }
  };

  // ── Delete ─────────────────────────────────────────────────────────────────

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await expensesApi.remove(deleteTarget.id);
      setSnack({ open: true, msg: "Expense deleted", severity: "success" });
      setDeleteTarget(null);
      loadExpenses();
    } catch {
      setSnack({ open: true, msg: "Failed to delete expense", severity: "error" });
    }
  };

  // ── File upload ────────────────────────────────────────────────────────────

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !uploadTarget) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
      await expensesApi.uploadBill(uploadTarget.id, fd);
      setSnack({ open: true, msg: "Bill uploaded successfully", severity: "success" });
      setUploadTarget(null);
      loadExpenses();
    } catch (err) {
      const detail = err.response?.data?.detail || "Upload failed";
      setSnack({ open: true, msg: detail, severity: "error" });
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={600}>
          Expenses
        </Typography>
        {isAdmin && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            Add Expense
          </Button>
        )}
      </Stack>

      {/* Building selector + filters */}
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
            value={filterDateFrom}
            onChange={(e) => setFilterDateFrom(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            size="small"
            label="Date To"
            type="date"
            value={filterDateTo}
            onChange={(e) => setFilterDateTo(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />

          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Category</InputLabel>
            <Select
              label="Category"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
            >
              <MenuItem value="">All Categories</MenuItem>
              {categories.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button variant="outlined" startIcon={<FilterIcon />} onClick={loadExpenses}>
            Apply
          </Button>
        </Stack>
      </Paper>

      {/* Expense table */}
      {loading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: "grey.100" }}>
                <TableCell>Title</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Split</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Recurring</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {expenses.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4, color: "text.secondary" }}>
                    No expenses found.{" "}
                    {isAdmin && "Click 'Add Expense' to create one."}
                  </TableCell>
                </TableRow>
              ) : (
                expenses.map((exp) => (
                  <TableRow key={exp.id} hover>
                    <TableCell>
                      <Tooltip title={exp.description || ""} placement="top">
                        <Typography
                          variant="body2"
                          sx={{
                            maxWidth: 200,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {exp.title}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {parseFloat(exp.amount).toLocaleString("en-US", {
                          minimumFractionDigits: 2,
                        })}
                      </Typography>
                    </TableCell>
                    <TableCell>{exp.expense_date}</TableCell>
                    <TableCell>
                      <Chip
                        label={
                          SPLIT_TYPES.find((s) => s.value === exp.split_type)?.label ??
                          exp.split_type
                        }
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{statusChip(exp)}</TableCell>
                    <TableCell>
                      {exp.is_recurring && (
                        <Chip
                          icon={<RepeatIcon fontSize="small" />}
                          label={exp.recurring_config?.frequency ?? "recurring"}
                          size="small"
                          color="info"
                          variant="outlined"
                        />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        <Tooltip title="View details">
                          <IconButton size="small" onClick={() => setDetailExpense(exp)}>
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {isAdmin && (
                          <>
                            <Tooltip title="Edit">
                              <IconButton size="small" onClick={() => openEdit(exp)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Upload bill">
                              <IconButton size="small" onClick={() => setUploadTarget(exp)}>
                                <AttachFileIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => setDeleteTarget(exp)}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* ── Add / Edit Dialog ─────────────────────────────────────────────── */}
      <Dialog open={formOpen} onClose={() => setFormOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editTarget ? "Edit Expense" : "Add Expense"}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} pt={1}>
            {formError && <Alert severity="error">{formError}</Alert>}

            <TextField
              label="Title *"
              value={form.title}
              onChange={handleFormChange("title")}
              size="small"
              fullWidth
            />
            <TextField
              label="Description"
              value={form.description}
              onChange={handleFormChange("description")}
              size="small"
              fullWidth
              multiline
              rows={2}
            />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="Amount *"
                  type="number"
                  inputProps={{ min: 0.01, step: 0.01 }}
                  value={form.amount}
                  onChange={handleFormChange("amount")}
                  size="small"
                  fullWidth
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Expense Date *"
                  type="date"
                  value={form.expense_date}
                  onChange={handleFormChange("expense_date")}
                  size="small"
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>
            <TextField
              label="Due Date"
              type="date"
              value={form.due_date}
              onChange={handleFormChange("due_date")}
              size="small"
              fullWidth
              InputLabelProps={{ shrink: true }}
            />

            <FormControl size="small" fullWidth>
              <InputLabel>Category *</InputLabel>
              <Select
                label="Category *"
                value={form.category_id}
                onChange={(e) => {
                  handleFormChange("category_id")(e);
                  setSubcategoryId("");
                }}
              >
                {categories.filter((c) => !c.parent_id).map((c) => (
                  <MenuItem key={c.id} value={c.id}>
                    {c.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Show subcategory dropdown if the selected category has subcategories */}
            {form.category_id && categories.some((c) => c.parent_id === form.category_id) && (
              <FormControl size="small" fullWidth>
                <InputLabel>Subcategory (optional)</InputLabel>
                <Select
                  label="Subcategory (optional)"
                  value={subcategoryId}
                  onChange={(e) => setSubcategoryId(e.target.value)}
                >
                  <MenuItem value="">— None —</MenuItem>
                  {categories
                    .filter((c) => c.parent_id === form.category_id)
                    .map((c) => (
                      <MenuItem key={c.id} value={c.id}>
                        {c.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            )}

            <FormControl size="small" fullWidth>
              <InputLabel>Split Type</InputLabel>
              <Select
                label="Split Type"
                value={form.split_type}
                onChange={handleFormChange("split_type")}
              >
                {SPLIT_TYPES.map((s) => (
                  <MenuItem key={s.value} value={s.value}>
                    {s.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Stack direction="row" alignItems="center" spacing={1}>
              <input
                type="checkbox"
                id="is_recurring"
                checked={form.is_recurring}
                onChange={handleFormChange("is_recurring")}
              />
              <label htmlFor="is_recurring">
                <Typography variant="body2">Recurring expense</Typography>
              </label>
            </Stack>

            {form.is_recurring && (
              <FormControl size="small" fullWidth>
                <InputLabel>Frequency *</InputLabel>
                <Select
                  label="Frequency *"
                  value={form.frequency}
                  onChange={handleFormChange("frequency")}
                >
                  {FREQUENCIES.map((f) => (
                    <MenuItem key={f.value} value={f.value}>
                      {f.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleFormSubmit}>
            {editTarget ? "Save Changes" : "Create Expense"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Detail Dialog ─────────────────────────────────────────────────── */}
      <Dialog
        open={Boolean(detailExpense)}
        onClose={() => setDetailExpense(null)}
        maxWidth="sm"
        fullWidth
      >
        {detailExpense && (
          <>
            <DialogTitle>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography fontWeight={600}>{detailExpense.title}</Typography>
                {detailExpense.is_recurring && (
                  <Chip
                    icon={<RepeatIcon fontSize="small" />}
                    label={detailExpense.recurring_config?.frequency ?? "Recurring"}
                    size="small"
                    color="info"
                  />
                )}
              </Stack>
            </DialogTitle>
            <DialogContent dividers>
              <Stack spacing={1.5}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Total Amount
                  </Typography>
                  <Typography fontWeight={600}>
                    {parseFloat(detailExpense.amount).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Date
                  </Typography>
                  <Typography>{detailExpense.expense_date}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Split Type
                  </Typography>
                  <Chip
                    label={
                      SPLIT_TYPES.find((s) => s.value === detailExpense.split_type)?.label ??
                      detailExpense.split_type
                    }
                    size="small"
                    variant="outlined"
                  />
                </Stack>
                {detailExpense.description && (
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">
                      Description
                    </Typography>
                    <Typography variant="body2" sx={{ maxWidth: "60%", textAlign: "right" }}>
                      {detailExpense.description}
                    </Typography>
                  </Stack>
                )}

                <Divider />

                <Typography variant="subtitle2" fontWeight={600}>
                  Per-Unit Breakdown ({(detailExpense.apartment_shares || []).length} units)
                </Typography>
                {(detailExpense.apartment_shares || []).length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No units assigned.
                  </Typography>
                ) : (
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Unit</TableCell>
                        <TableCell align="right">Share Amount</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {detailExpense.apartment_shares.map((s) => (
                        <TableRow key={s.id}>
                          <TableCell>{s.unit_number}</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 500 }}>
                            {parseFloat(s.share_amount).toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                            })}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                    <TableFooter>
                      <TableRow sx={{ "& td": { borderTop: "2px solid", borderColor: "divider" } }}>
                        <TableCell sx={{ fontWeight: 700 }}>Total Shares</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>
                          {detailExpense.apartment_shares
                            .reduce((sum, s) => sum + parseFloat(s.share_amount), 0)
                            .toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </TableCell>
                      </TableRow>
                    </TableFooter>
                  </Table>
                )}

                {(detailExpense.attachments || []).length > 0 && (
                  <>
                    <Divider />
                    <Typography variant="subtitle2" fontWeight={600}>
                      Attachments
                    </Typography>
                    {detailExpense.attachments.map((att) => (
                      <Stack key={att.id} direction="row" alignItems="center" spacing={1}>
                        <AttachFileIcon fontSize="small" color="action" />
                        <Typography
                          variant="body2"
                          component="a"
                          href={att.url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {att.mime_type} ({(att.file_size_bytes / 1024).toFixed(1)} KB)
                        </Typography>
                      </Stack>
                    ))}
                  </>
                )}
              </Stack>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailExpense(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* ── Delete confirmation ───────────────────────────────────────────── */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete Expense</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete <strong>{deleteTarget?.title}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Bill upload dialog ────────────────────────────────────────────── */}
      <Dialog open={Boolean(uploadTarget)} onClose={() => setUploadTarget(null)}>
        <DialogTitle>Upload Bill — "{uploadTarget?.title}"</DialogTitle>
        <DialogContent>
          <Stack spacing={2} pt={1}>
            <Typography variant="body2" color="text.secondary">
              Accepted: JPEG, PNG, PDF · Max 10 MB
            </Typography>
            <Button variant="outlined" component="label" startIcon={<AttachFileIcon />}>
              Choose File
              <input
                hidden
                accept="image/jpeg,image/png,application/pdf"
                type="file"
                onChange={handleFileUpload}
              />
            </Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadTarget(null)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* ── Snackbar ──────────────────────────────────────────────────────── */}
      <Snackbar
        open={snack.open}
        autoHideDuration={3500}
        onClose={() => setSnack((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity={snack.severity}
          onClose={() => setSnack((s) => ({ ...s, open: false }))}
        >
          {snack.msg}
        </Alert>
      </Snackbar>
    </Box>
  );
}
