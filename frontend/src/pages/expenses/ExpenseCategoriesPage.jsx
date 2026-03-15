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
import { expensesApi } from "../../api/expensesApi";
import { buildingsApi } from "../../api/buildingsApi";

const EMPTY_FORM = { name: "", description: "", icon: "", color: "#2563EB", parent_id: "" };

export default function ExpenseCategoriesPage() {
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
      setSnack({ open: true, msg: "Failed to load categories", severity: "error" });
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
      setFormError("Name is required.");
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
      setSnack({ open: true, msg: "Category added.", severity: "success" });
      loadCategories();
    } catch (err) {
      const detail =
        err.response?.data?.name?.[0] ||
        err.response?.data?.detail ||
        "Failed to add category.";
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
      setSnack({ open: true, msg: "Category removed.", severity: "success" });
      loadCategories();
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        "Cannot remove a category that has expenses assigned to it.";
      setSnack({ open: true, msg: detail, severity: "error" });
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          Expense Categories
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={openAdd}
          disabled={!selectedBuilding}
        >
          Add Category
        </Button>
      </Box>

      {/* Building selector */}
      <FormControl size="small" sx={{ minWidth: 260, mb: 3 }}>
        <InputLabel>Building</InputLabel>
        <Select
          value={selectedBuilding}
          label="Building"
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
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Icon / Color</strong></TableCell>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Description</strong></TableCell>
                <TableCell><strong>Subcategory of</strong></TableCell>
                <TableCell align="right"><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {categories.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4, color: "text.secondary" }}>
                    No categories found for this building.
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
                      <TableCell>{cat.name}</TableCell>
                      <TableCell sx={{ color: "text.secondary" }}>
                        {cat.description || "—"}
                      </TableCell>
                      <TableCell>
                        {parentCat ? (
                          <Chip label={parentCat.name} size="small" variant="outlined" />
                        ) : (
                          <Typography variant="caption" color="text.disabled">—</Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Remove category">
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
        <DialogTitle>Add Expense Category</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          <TextField
            label="Name"
            name="name"
            value={form.name}
            onChange={handleFormChange}
            fullWidth
            required
            autoFocus
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            label="Description"
            name="description"
            value={form.description}
            onChange={handleFormChange}
            fullWidth
            multiline
            rows={2}
            placeholder="Optional"
            sx={{ mb: 2 }}
          />
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <TextField
              label="Icon name"
              name="icon"
              value={form.icon}
              onChange={handleFormChange}
              fullWidth
              placeholder="e.g. build"
              size="small"
            />
            <TextField
              label="Color"
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
            <InputLabel>Subcategory of (optional)</InputLabel>
            <Select
              name="parent_id"
              value={form.parent_id}
              label="Subcategory of (optional)"
              onChange={handleFormChange}
            >
              <MenuItem value="">— None (top-level) —</MenuItem>
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
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Add"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Remove Category</DialogTitle>
        <DialogContent>
          <Typography>
            Remove <strong>{deleteTarget?.name}</strong>? This cannot be undone.
            Categories with expenses assigned cannot be removed.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)} disabled={deleting}>
            Cancel
          </Button>
          <Button variant="contained" color="error" onClick={handleDelete} disabled={deleting}>
            {deleting ? "Removing…" : "Remove"}
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
  );
}
