/**
 * Expense Categories management page – admin only.
 *
 * Allows admins to view, add, and remove expense categories per building.
 * Supports icons, colors, and optional parent (subcategory) assignment.
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
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { Add as AddIcon, Delete as DeleteIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { expensesApi } from "../../api/expensesApi";
import { buildingsApi } from "../../api/buildingsApi";
import { PrivateSEO } from "../../components/seo/SEO";

const EMPTY_FORM = { name: "", description: "", icon: "", color: "#2563EB", parent_id: "" };

export default function ExpenseCategoriesPage() {
  const { t } = useTranslation("categories");
  const [buildings, setBuildings] = useState([]);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);

  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const [snack, setSnack] = useState({ open: false, msg: "", severity: "success" });

  // ── Data fetching ────────────────────────────────────────────────────────────

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

  const loadCategories = useCallback(async () => {
    if (!selectedBuilding) return;
    setLoading(true);
    try {
      const res = await expensesApi.listCategories(selectedBuilding);
      setCategories(res.data.results ?? res.data);
    } catch {
      setSnack({ open: true, msg: t("load_error", "Failed to load categories"), severity: "error" });
    } finally {
      setLoading(false);
    }
  }, [selectedBuilding]);

  useEffect(() => { loadBuildings(); }, [loadBuildings]);
  useEffect(() => { loadCategories(); }, [loadCategories]);

  // Top-level categories (no parent) available for subcategory assignment
  const topLevelCategories = categories.filter((c) => !c.parent_id);

  // ── Add category ─────────────────────────────────────────────────────────────

  const openAdd = () => {
    setForm(EMPTY_FORM);
    setFormError("");
    setFormOpen(true);
  };

  const handleFormChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      setFormError(t("name_required", "Name is required."));
      return;
    }
    setSaving(true);
    setFormError("");
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        building_id: selectedBuilding,
      };
      if (form.icon.trim()) payload.icon = form.icon.trim();
      if (form.color.trim()) payload.color = form.color.trim();
      if (form.parent_id) payload.parent_id = form.parent_id;
      await expensesApi.createCategory(payload);
      setFormOpen(false);
      setSnack({ open: true, msg: t("category_added", "Category added."), severity: "success" });
      loadCategories();
    } catch (err) {
      const detail =
        err.response?.data?.name?.[0] ||
        err.response?.data?.detail ||
        t("add_error", "Failed to add category.");
      setFormError(detail);
    } finally {
      setSaving(false);
    }
  };

  // ── Delete category ──────────────────────────────────────────────────────────

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await expensesApi.removeCategory(deleteTarget.id);
      setDeleteTarget(null);
      setSnack({ open: true, msg: t("category_removed", "Category removed."), severity: "success" });
      loadCategories();
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        t("cannot_remove_with_expenses", "Cannot remove a category that has expenses assigned to it.");
      setSnack({ open: true, msg: detail, severity: "error" });
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <>
      <PrivateSEO title="ABEM – Expense Categories" />
      <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          {t("page_title")}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={openAdd}
          disabled={!selectedBuilding}
        >
          {t("add_category")}
        </Button>
      </Box>

      {/* Building selector */}
      <FormControl size="small" sx={{ minWidth: 260, mb: 3 }}>
        <InputLabel>{t("building")}</InputLabel>
        <Select
          value={selectedBuilding}
          label={t("building")}
          onChange={(e) => setSelectedBuilding(e.target.value)}
        >
          {buildings.map((b) => (
            <MenuItem key={b.id} value={b.id}>
              {b.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Categories table */}
      {loading ? (
        <Box display="flex" justifyContent="center" mt={6}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer id="categories-table" component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>{t("icon_color")}</strong></TableCell>
                <TableCell><strong>{t("name")}</strong></TableCell>
                <TableCell><strong>{t("description")}</strong></TableCell>
                <TableCell><strong>{t("subcategory_of")}</strong></TableCell>
                <TableCell align="right"><strong>{t("actions")}</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {categories.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4, color: "text.secondary" }}>
                    {t("no_categories")}
                  </TableCell>
                </TableRow>
              ) : (
                categories.map((cat) => {
                  const parentCat = cat.parent_id
                    ? categories.find((c) => c.id === cat.parent_id)
                    : null;
                  return (
                    <TableRow key={cat.id} hover>
                      <TableCell>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Box
                            sx={{
                              width: 20,
                              height: 20,
                              borderRadius: "50%",
                              bgcolor: cat.color || "#2563EB",
                              flexShrink: 0,
                            }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {cat.icon || "—"}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>{t(cat.name, cat.name)}</TableCell>
                      <TableCell sx={{ color: "text.secondary" }}>
                        {cat.description || "—"}
                      </TableCell>
                      <TableCell>
                        {parentCat ? (
                          <Chip label={t(parentCat.name, parentCat.name)} size="small" variant="outlined" />
                        ) : (
                          <Typography variant="caption" color="text.disabled">—</Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title={t("remove_category")}>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setDeleteTarget(cat)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Add category dialog */}
      <Dialog open={formOpen} onClose={() => setFormOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{t("add_category_title")}</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          <TextField
            label={t("name")}
            name="name"
            value={form.name}
            onChange={handleFormChange}
            fullWidth
            required
            autoFocus
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            label={t("description")}
            name="description"
            value={form.description}
            onChange={handleFormChange}
            fullWidth
            multiline
            rows={2}
            placeholder={t("common:optional", "Optional")}
            sx={{ mb: 2 }}
          />
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <TextField
              label={t("icon_name")}
              name="icon"
              value={form.icon}
              onChange={handleFormChange}
              fullWidth
              placeholder="e.g. build"
              size="small"
            />
            <TextField
              label={t("color")}
              name="color"
              value={form.color}
              onChange={handleFormChange}
              fullWidth
              placeholder="#2563EB"
              size="small"
              InputProps={{
                startAdornment: (
                  <Box
                    sx={{
                      width: 16,
                      height: 16,
                      borderRadius: "50%",
                      bgcolor: form.color || "#2563EB",
                      mr: 0.5,
                      flexShrink: 0,
                    }}
                  />
                ),
              }}
            />
          </Stack>
          <FormControl fullWidth size="small">
            <InputLabel>{t("subcategory_of_optional")}</InputLabel>
            <Select
              name="parent_id"
              value={form.parent_id}
              label={t("subcategory_of_optional")}
              onChange={handleFormChange}
            >
              <MenuItem value="">{t("none_top_level")}</MenuItem>
              {topLevelCategories.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormOpen(false)} disabled={saving}>
            {t("cancel")}
          </Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? t("saving") : t("add")}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>{t("remove_category_title")}</DialogTitle>
        <DialogContent>
          <Typography>
            {t("remove_confirm_text", { name: deleteTarget?.name })}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)} disabled={deleting}>
            {t("cancel")}
          </Button>
          <Button variant="contained" color="error" onClick={handleDelete} disabled={deleting}>
            {deleting ? t("removing") : t("remove")}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snack.open}
        autoHideDuration={4000}
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
