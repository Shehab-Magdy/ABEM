/**
 * Building Assets management page – admin only.
 *
 * Features:
 * - List assets per building with status (Active / Sold)
 * - Add Asset dialog
 * - Record Sale dialog for active assets
 * - Summary stats: total asset value, total sale proceeds
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
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { Add as AddIcon, Sell as SellIcon } from "@mui/icons-material";
import { assetsApi } from "../../api/assetsApi";
import { buildingsApi } from "../../api/buildingsApi";

const ASSET_TYPES = [
  { value: "vehicle", label: "Vehicle" },
  { value: "equipment", label: "Equipment" },
  { value: "furniture", label: "Furniture" },
  { value: "electronics", label: "Electronics" },
  { value: "property", label: "Property" },
  { value: "other", label: "Other" },
];

const EMPTY_ASSET_FORM = {
  name: "",
  description: "",
  asset_type: "other",
  other_type_label: "",
  acquisition_date: "",
  acquisition_value: "",
};

const EMPTY_SALE_FORM = {
  sale_date: new Date().toISOString().slice(0, 10),
  sale_price: "",
  buyer_name: "",
  buyer_contact: "",
  notes: "",
};

export default function AssetsPage() {
  const [buildings, setBuildings] = useState([]);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);

  const [assetFormOpen, setAssetFormOpen] = useState(false);
  const [assetForm, setAssetForm] = useState(EMPTY_ASSET_FORM);
  const [assetFormError, setAssetFormError] = useState("");
  const [savingAsset, setSavingAsset] = useState(false);

  const [saleTarget, setSaleTarget] = useState(null);
  const [saleForm, setSaleForm] = useState(EMPTY_SALE_FORM);
  const [saleFormError, setSaleFormError] = useState("");
  const [recordingSale, setRecordingSale] = useState(false);

  const [snack, setSnack] = useState({ open: false, msg: "", severity: "success" });

  // ── Data fetching ───────────────────────────────────────────────────────────

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

  const loadAssets = useCallback(async () => {
    if (!selectedBuilding) return;
    setLoading(true);
    try {
      const res = await assetsApi.list({ building_id: selectedBuilding });
      setAssets(res.data.results ?? res.data);
    } catch {
      setSnack({ open: true, msg: "Failed to load assets", severity: "error" });
    } finally {
      setLoading(false);
    }
  }, [selectedBuilding]);

  useEffect(() => { loadBuildings(); }, [loadBuildings]);
  useEffect(() => { loadAssets(); }, [loadAssets]);

  // ── Summary stats ───────────────────────────────────────────────────────────

  const totalSaleProceeds = assets
    .filter((a) => a.is_sold && a.sale?.sale_price != null)
    .reduce((sum, a) => sum + parseFloat(a.sale.sale_price), 0);

  // ── Add asset ───────────────────────────────────────────────────────────────

  const handleAssetFormChange = (e) => {
    setAssetForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSaveAsset = async () => {
    if (!assetForm.name.trim()) {
      setAssetFormError("Name is required.");
      return;
    }
    setSavingAsset(true);
    setAssetFormError("");
    try {
      const descriptionWithType =
        assetForm.asset_type === "other" && assetForm.other_type_label.trim()
          ? `[Type: ${assetForm.other_type_label.trim()}]${assetForm.description.trim() ? " " + assetForm.description.trim() : ""}`
          : assetForm.description.trim();
      const payload = {
        name: assetForm.name.trim(),
        description: descriptionWithType,
        asset_type: assetForm.asset_type,
        building_id: selectedBuilding,
      };
      if (assetForm.acquisition_date) payload.acquisition_date = assetForm.acquisition_date;
      if (assetForm.acquisition_value) payload.acquisition_value = assetForm.acquisition_value;
      await assetsApi.create(payload);
      setAssetFormOpen(false);
      setSnack({ open: true, msg: "Asset added.", severity: "success" });
      loadAssets();
    } catch (err) {
      setAssetFormError(err.response?.data?.detail || "Failed to add asset.");
    } finally {
      setSavingAsset(false);
    }
  };

  // ── Record sale ─────────────────────────────────────────────────────────────

  const openSale = (asset) => {
    setSaleTarget(asset);
    setSaleForm(EMPTY_SALE_FORM);
    setSaleFormError("");
  };

  const handleSaleFormChange = (e) => {
    setSaleForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleRecordSale = async () => {
    if (!saleForm.sale_price || parseFloat(saleForm.sale_price) <= 0) {
      setSaleFormError("Sale price must be greater than 0.");
      return;
    }
    setRecordingSale(true);
    setSaleFormError("");
    try {
      await assetsApi.sell(saleTarget.id, {
        sale_date: saleForm.sale_date,
        sale_price: saleForm.sale_price,
        buyer_name: saleForm.buyer_name.trim(),
        buyer_contact: saleForm.buyer_contact.trim(),
        notes: saleForm.notes.trim(),
      });
      setSaleTarget(null);
      setSnack({ open: true, msg: "Sale recorded.", severity: "success" });
      loadAssets();
    } catch (err) {
      setSaleFormError(err.response?.data?.detail || "Failed to record sale.");
    } finally {
      setRecordingSale(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          Building Assets
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => { setAssetForm(EMPTY_ASSET_FORM); setAssetFormError(""); setAssetFormOpen(true); }}
          disabled={!selectedBuilding}
        >
          Add Asset
        </Button>
      </Stack>

      {/* Building selector */}
      <FormControl size="small" sx={{ minWidth: 260, mb: 3 }}>
        <InputLabel>Building</InputLabel>
        <Select
          value={selectedBuilding}
          label="Building"
          onChange={(e) => setSelectedBuilding(e.target.value)}
        >
          {buildings.map((b) => (
            <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Summary stats */}
      {assets.length > 0 && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="caption" color="text.secondary">Total Sale Proceeds</Typography>
              <Typography variant="h6" fontWeight={600} color="success.main">
                {totalSaleProceeds.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="caption" color="text.secondary">Total Assets</Typography>
              <Typography variant="h6" fontWeight={600}>{assets.length}</Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Assets table */}
      {loading ? (
        <Box display="flex" justifyContent="center" mt={6}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer id="assets-table" component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Type</strong></TableCell>
                <TableCell><strong>Acquired</strong></TableCell>
                <TableCell><strong>Acquisition Value</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell align="right"><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {assets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4, color: "text.secondary" }}>
                    No assets found. Click "Add Asset" to create one.
                  </TableCell>
                </TableRow>
              ) : (
                assets.map((asset) => (
                  <TableRow key={asset.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>{asset.name}</Typography>
                      {asset.description && (
                        <Typography variant="caption" color="text.secondary">{asset.description}</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={ASSET_TYPES.find((t) => t.value === asset.asset_type)?.label ?? asset.asset_type}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{asset.acquisition_date || "—"}</TableCell>
                    <TableCell>
                      {asset.acquisition_value != null
                        ? parseFloat(asset.acquisition_value).toLocaleString("en-US", { minimumFractionDigits: 2 })
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={asset.is_sold ? "Sold" : "Active"}
                        size="small"
                        color={asset.is_sold ? "default" : "success"}
                      />
                    </TableCell>
                    <TableCell align="right">
                      {!asset.is_sold && (
                        <Tooltip title="Record Sale">
                          <IconButton size="small" color="primary" onClick={() => openSale(asset)}>
                            <SellIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Add Asset dialog */}
      <Dialog open={assetFormOpen} onClose={() => setAssetFormOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Building Asset</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} pt={1}>
            {assetFormError && <Alert severity="error">{assetFormError}</Alert>}
            <TextField
              label="Name *"
              name="name"
              value={assetForm.name}
              onChange={handleAssetFormChange}
              fullWidth
              size="small"
              autoFocus
              InputLabelProps={{ shrink: true }}
              placeholder="Asset name"
            />
            <TextField
              label="Description"
              name="description"
              value={assetForm.description}
              onChange={handleAssetFormChange}
              fullWidth
              size="small"
              multiline
              rows={2}
              InputLabelProps={{ shrink: true }}
              placeholder="Optional description"
            />
            <FormControl size="small" fullWidth>
              <InputLabel shrink>Asset Type</InputLabel>
              <Select
                name="asset_type"
                value={assetForm.asset_type}
                label="Asset Type"
                onChange={handleAssetFormChange}
              >
                {ASSET_TYPES.map((t) => (
                  <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            {assetForm.asset_type === "other" && (
              <TextField
                label="Specify asset type *"
                name="other_type_label"
                placeholder="e.g. Generator, Garden Equipment…"
                value={assetForm.other_type_label}
                onChange={handleAssetFormChange}
                required
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
              />
            )}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="Acquisition Date"
                  name="acquisition_date"
                  type="date"
                  value={assetForm.acquisition_date}
                  onChange={handleAssetFormChange}
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Acquisition Value"
                  name="acquisition_value"
                  type="number"
                  value={assetForm.acquisition_value}
                  onChange={handleAssetFormChange}
                  fullWidth
                  size="small"
                  inputProps={{ min: 0, step: 0.01 }}
                  InputLabelProps={{ shrink: true }}
                  placeholder="0.00"
                />
              </Grid>
            </Grid>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssetFormOpen(false)} disabled={savingAsset}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveAsset} disabled={savingAsset}>
            {savingAsset ? "Saving…" : "Add Asset"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Record Sale dialog */}
      <Dialog open={Boolean(saleTarget)} onClose={() => setSaleTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Record Sale — {saleTarget?.name}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} pt={1}>
            {saleFormError && <Alert severity="error">{saleFormError}</Alert>}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="Sale Date *"
                  name="sale_date"
                  type="date"
                  value={saleForm.sale_date}
                  onChange={handleSaleFormChange}
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Sale Price *"
                  name="sale_price"
                  type="number"
                  value={saleForm.sale_price}
                  onChange={handleSaleFormChange}
                  fullWidth
                  size="small"
                  inputProps={{ min: 0.01, step: 0.01 }}
                  InputLabelProps={{ shrink: true }}
                  placeholder="0.00"
                />
              </Grid>
            </Grid>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="Buyer Name"
                  name="buyer_name"
                  value={saleForm.buyer_name}
                  onChange={handleSaleFormChange}
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                  placeholder="Optional"
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Buyer Contact"
                  name="buyer_contact"
                  value={saleForm.buyer_contact}
                  onChange={handleSaleFormChange}
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                  placeholder="Phone or email"
                />
              </Grid>
            </Grid>
            <TextField
              label="Notes"
              name="notes"
              value={saleForm.notes}
              onChange={handleSaleFormChange}
              fullWidth
              size="small"
              multiline
              rows={2}
              InputLabelProps={{ shrink: true }}
              placeholder="Optional notes"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaleTarget(null)} disabled={recordingSale}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleRecordSale} disabled={recordingSale}>
            {recordingSale ? "Recording…" : "Record Sale"}
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
        <Alert severity={snack.severity} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
          {snack.msg}
        </Alert>
      </Snackbar>
    </Box>
  );
}
