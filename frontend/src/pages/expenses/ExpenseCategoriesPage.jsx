/**
 * Expense Categories management page – admin only.
 *
 * Allows admins to view, add, and remove expense categories per building.
 */
import { useEffect, useState, useCallback } from "react";
import {
  Alert,
  Box,
  Button,
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

const EMPTY_FORM = { name: "", description: "" };

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
      await expensesApi.createCategory({
        name: form.name.trim(),
        description: form.description.trim(),
        building_id: selectedBuilding,
      });
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
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Description</strong></TableCell>
                <TableCell align="right"><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {categories.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} align="center" sx={{ py: 4, color: "text.secondary" }}>
                    No categories found for this building.
                  </TableCell>
                </TableRow>
              ) : (
                categories.map((cat) => (
                  <TableRow key={cat.id} hover>
                    <TableCell>{cat.name}</TableCell>
                    <TableCell sx={{ color: "text.secondary" }}>
                      {cat.description || "—"}
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
                ))
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
          />
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
