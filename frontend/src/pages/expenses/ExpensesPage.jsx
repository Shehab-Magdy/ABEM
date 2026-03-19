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
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
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
import { useTranslation } from "react-i18next";
import { PrivateSEO } from "../../components/seo/SEO";

// Resolve relative media paths to absolute backend URLs so the browser
// doesn't route them through React Router.
const mediaUrl = (url) => {
  if (!url || url.startsWith("http")) return url;
  const apiBase = import.meta.env.VITE_API_BASE_URL || "/api/v1";
  if (apiBase.startsWith("http")) {
    const origin = new URL(apiBase).origin;
    return origin + url;
  }
  return window.location.origin + url;
};

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
  const { t } = useTranslation("expenses");
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

  // Custom split — building apartments + per-unit weights
  const [buildingApartments, setBuildingApartments] = useState([]);
  const [customWeights, setCustomWeights] = useState({});

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

  const loadBuildingApartments = useCallback(async (buildingId) => {
    if (!buildingId) return;
    try {
      const res = await buildingsApi.apartments(buildingId, { page_size: 200 });
      setBuildingApartments(res.data?.results ?? res.data);
    } catch {
      setBuildingApartments([]);
    }
  }, []);

  const openCreate = () => {
    setEditTarget(null);
    setForm({ ...EMPTY_FORM, building_id: selectedBuilding });
    setFormError("");
    setSubcategoryId("");
    setCustomWeights({});
    setBuildingApartments([]);
    if (selectedBuilding) loadBuildingApartments(selectedBuilding);
    setFormOpen(true);
  };

  const openEdit = (expense) => {
    setEditTarget(expense);
    setSubcategoryId("");
    setCustomWeights({});
    setBuildingApartments([]);
    const bid = expense.building_id || selectedBuilding;
    if (bid) loadBuildingApartments(bid);
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
      title: form.title.trim(),
      description: form.description.trim(),
      amount: form.amount,
      expense_date: form.expense_date,
      split_type: form.split_type,
      is_recurring: form.is_recurring,
      category_id: effectiveCategoryId,
      building_id: form.building_id || selectedBuilding,
    };
    if (form.due_date) payload.due_date = form.due_date;
    if (form.is_recurring && form.frequency) payload.frequency = form.frequency;
    if (form.split_type === "custom" && Object.keys(customWeights).length > 0) {
      payload.custom_split_weights = customWeights;
    }

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
    <>
      <PrivateSEO title="ABEM – Expenses" />
      <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={600}>
          {t("page_title")}
        </Typography>
        {isAdmin && (
          <Button id="add-expense-btn" variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            {t("add_expense")}
          </Button>
        )}
      </Stack>

      {/* Building selector + filters */}
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
            value={filterDateFrom}
            onChange={(e) => setFilterDateFrom(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            size="small"
            label={t("date_to")}
            type="date"
            value={filterDateTo}
            onChange={(e) => setFilterDateTo(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />

          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>{t("category")}</InputLabel>
            <Select
              label={t("category")}
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
            >
              <MenuItem value="">{t("all_categories")}</MenuItem>
              {categories.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button variant="outlined" startIcon={<FilterIcon />} onClick={loadExpenses}>
            {t("apply")}
          </Button>
        </Stack>
      </Paper>

      {/* Expense table */}
      {loading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer id="expenses-table" component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: "grey.100" }}>
                <TableCell>{t("title")}</TableCell>
                <TableCell>{t("amount")}</TableCell>
                <TableCell>{t("date")}</TableCell>
                <TableCell>{t("split_type")}</TableCell>
                <TableCell>{t("status")}</TableCell>
                <TableCell>{t("recurring")}</TableCell>
                <TableCell align="center">{t("bill")}</TableCell>
                <TableCell align="right">{t("actions")}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {expenses.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4, color: "text.secondary" }}>
                    {t("no_expenses")}{" "}
                    {isAdmin && t("no_expenses_hint")}
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
                        {parseFloat(
                          !isAdmin && exp.my_share_amount != null
                            ? exp.my_share_amount
                            : exp.amount
                        ).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </Typography>
                      {!isAdmin && exp.my_share_amount != null && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {t("your_share")}
                        </Typography>
                      )}
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
                    <TableCell align="center">
                      {exp.attachments?.length > 0 && (
                        <Tooltip title={`${exp.attachments.length} attachment(s)`}>
                          <IconButton
                            size="small"
                            component="a"
                            href={mediaUrl(exp.attachments[0].url)}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <AttachFileIcon fontSize="small" color="action" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Stack id="expense-actions-btn" direction="row" spacing={0.5} justifyContent="flex-end">
                        <Tooltip title={t("view_details")}>
                          <IconButton size="small" onClick={() => setDetailExpense(exp)}>
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {isAdmin && (
                          <>
                            <Tooltip title={t("edit")}>
                              <IconButton size="small" onClick={() => openEdit(exp)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title={t("upload_bill")}>
                              <IconButton size="small" onClick={() => setUploadTarget(exp)}>
                                <AttachFileIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title={t("delete")}>
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
        <DialogTitle>{editTarget ? t("edit_expense") : t("add_expense")}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} pt={1}>
            {formError && <Alert severity="error">{formError}</Alert>}

            <TextField
              label={`${t("title")} *`}
              value={form.title}
              onChange={handleFormChange("title")}
              size="small"
              fullWidth
            />
            <TextField
              label={t("description")}
              value={form.description}
              onChange={handleFormChange("description")}
              size="small"
              fullWidth
              multiline
              rows={2}
            />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label={`${t("amount")} *`}
                type="number"
                inputProps={{ min: 0.01, step: 0.01 }}
                value={form.amount}
                onChange={handleFormChange("amount")}
                size="small"
                fullWidth
              />
              <TextField
                label={`${t("expense_date")} *`}
                type="date"
                value={form.expense_date}
                onChange={handleFormChange("expense_date")}
                size="small"
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Stack>
            <TextField
              label={t("due_date")}
              type="date"
              value={form.due_date}
              onChange={handleFormChange("due_date")}
              size="small"
              fullWidth
              InputLabelProps={{ shrink: true }}
            />

            <FormControl size="small" fullWidth>
              <InputLabel>{t("category")} *</InputLabel>
              <Select
                label={`${t("category")} *`}
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
                <InputLabel>{t("subcategory_optional")}</InputLabel>
                <Select
                  label={t("subcategory_optional")}
                  value={subcategoryId}
                  onChange={(e) => setSubcategoryId(e.target.value)}
                >
                  <MenuItem value="">{t("none_subcategory")}</MenuItem>
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
              <InputLabel>{t("split_type")}</InputLabel>
              <Select
                label={t("split_type")}
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

            {/* Custom subset: per-unit weight inputs */}
            {form.split_type === "custom" && (
              <Box>
                <Typography variant="caption" color="text.secondary" mb={0.5} display="block">
                  {t("custom_weight_hint")}
                </Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell padding="checkbox">
                        <Checkbox
                          size="small"
                          checked={buildingApartments.length > 0 && buildingApartments.every((a) => a.id in customWeights)}
                          indeterminate={buildingApartments.some((a) => a.id in customWeights) && !buildingApartments.every((a) => a.id in customWeights)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              const all = {};
                              buildingApartments.forEach((a) => { all[a.id] = 1; });
                              setCustomWeights(all);
                            } else {
                              setCustomWeights({});
                            }
                          }}
                        />
                      </TableCell>
                      <TableCell>{t("unit")}</TableCell>
                      <TableCell>{t("type")}</TableCell>
                      <TableCell width={100}>{t("weight")}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {buildingApartments.map((apt) => {
                      const checked = apt.id in customWeights;
                      return (
                        <TableRow key={apt.id} hover>
                          <TableCell padding="checkbox">
                            <Checkbox
                              size="small"
                              checked={checked}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setCustomWeights((prev) => ({ ...prev, [apt.id]: 1 }));
                                } else {
                                  setCustomWeights((prev) => {
                                    const next = { ...prev };
                                    delete next[apt.id];
                                    return next;
                                  });
                                }
                              }}
                            />
                          </TableCell>
                          <TableCell>{apt.unit_number}</TableCell>
                          <TableCell>{apt.type}</TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              type="number"
                              inputProps={{ min: 0, step: 0.1 }}
                              value={customWeights[apt.id] ?? ""}
                              disabled={!checked}
                              onChange={(e) =>
                                setCustomWeights((prev) => ({
                                  ...prev,
                                  [apt.id]: parseFloat(e.target.value) || 0,
                                }))
                              }
                              sx={{ width: 80 }}
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </Box>
            )}

            <Stack direction="row" alignItems="center" spacing={1}>
              <input
                type="checkbox"
                id="is_recurring"
                checked={form.is_recurring}
                onChange={handleFormChange("is_recurring")}
              />
              <label htmlFor="is_recurring">
                <Typography variant="body2">{t("recurring_expense")}</Typography>
              </label>
            </Stack>

            {form.is_recurring && (
              <FormControl size="small" fullWidth>
                <InputLabel>{t("frequency")} *</InputLabel>
                <Select
                  label={`${t("frequency")} *`}
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
          <Button onClick={() => setFormOpen(false)}>{t("cancel")}</Button>
          <Button variant="contained" onClick={handleFormSubmit}>
            {editTarget ? t("save_changes") : t("create_expense")}
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
                    {t("total_amount")}
                  </Typography>
                  <Typography fontWeight={600}>
                    {parseFloat(detailExpense.amount).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    {t("date")}
                  </Typography>
                  <Typography>{detailExpense.expense_date}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    {t("split_type")}
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
                      {t("description")}
                    </Typography>
                    <Typography variant="body2" sx={{ maxWidth: "60%", textAlign: "right" }}>
                      {detailExpense.description}
                    </Typography>
                  </Stack>
                )}

                <Divider />

                <Typography variant="subtitle2" fontWeight={600}>
                  {t("per_unit_breakdown", { count: (detailExpense.apartment_shares || []).length })}
                </Typography>
                {(detailExpense.apartment_shares || []).length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    {t("no_units_assigned")}
                  </Typography>
                ) : (
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>{t("unit")}</TableCell>
                        <TableCell align="right">{t("share_amount")}</TableCell>
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
                        <TableCell sx={{ fontWeight: 700 }}>{t("total_shares")}</TableCell>
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
                      {t("attachments")}
                    </Typography>
                    {detailExpense.attachments.map((att) => (
                      <Stack key={att.id} direction="row" alignItems="center" spacing={1}>
                        <AttachFileIcon fontSize="small" color="action" />
                        <Typography
                          variant="body2"
                          component="a"
                          href={mediaUrl(att.url)}
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
              <Button onClick={() => setDetailExpense(null)}>{t("close")}</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* ── Delete confirmation ───────────────────────────────────────────── */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>{t("delete_expense")}</DialogTitle>
        <DialogContent>
          <Typography>
            {t("confirm_delete")}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>{t("cancel")}</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>
            {t("delete")}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Bill upload dialog ────────────────────────────────────────────── */}
      <Dialog open={Boolean(uploadTarget)} onClose={() => setUploadTarget(null)}>
        <DialogTitle>{t("upload_bill_title", { title: uploadTarget?.title })}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} pt={1}>
            <Typography variant="body2" color="text.secondary">
              {t("accepted_formats")}
            </Typography>
            <Button variant="outlined" component="label" startIcon={<AttachFileIcon />}>
              {t("choose_file")}
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
          <Button onClick={() => setUploadTarget(null)}>{t("cancel")}</Button>
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
    </>
  );
}
