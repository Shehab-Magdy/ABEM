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
import { useTranslation } from "react-i18next";
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
import { PrivateSEO } from "../../components/seo/SEO";

const ASSET_TYPE_VALUES = ["vehicle", "equipment", "furniture", "electronics", "property", "other"];

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
  const { t } = useTranslation("common");

  const ASSET_TYPES = ASSET_TYPE_VALUES.map((v) => ({
    value: v,
    label: t(`assets.type.${v}`, {
      defaultValue: v.charAt(0).toUpperCase() + v.slice(1),
    }),
  }));

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
      setSnack({ open: true, msg: t("assets.failedToLoadAssets", "Failed to load assets"), severity: "error" });
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
      setAssetFormError(t("assets.nameRequired", "Name is required."));
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
      setSnack({ open: true, msg: t("assets.assetAdded", "Asset added."), severity: "success" });
      loadAssets();
    } catch (err) {
      setAssetFormError(err.response?.data?.detail || t("assets.failedToAddAsset", "Failed to add asset."));
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
      setSaleFormError(t("assets.salePriceRequired", "Sale price must be greater than 0."));
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
      setSnack({ open: true, msg: t("assets.saleRecorded", "Sale recorded."), severity: "success" });
      loadAssets();
    } catch (err) {
      setSaleFormError(err.response?.data?.detail || t("assets.failedToRecordSale", "Failed to record sale."));
    } finally {
      setRecordingSale(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <>
      <PrivateSEO title={`ABEM – ${t("assets.pageTitle", "Assets")}`} />
      <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          {t("assets.buildingAssets", "Building Assets")}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => { setAssetForm(EMPTY_ASSET_FORM); setAssetFormError(""); setAssetFormOpen(true); }}
          disabled={!selectedBuilding}
        >
          {t("assets.addAsset", "Add Asset")}
        </Button>
      </Stack>

      {/* Building selector */}
      <FormControl size="small" sx={{ minWidth: 260, mb: 3 }}>
        <InputLabel>{t("building", "Building")}</InputLabel>
        <Select
          value={selectedBuilding}
          label={t("building", "Building")}
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
              <Typography variant="caption" color="text.secondary">{t("assets.totalSaleProceeds", "Total Sale Proceeds")}</Typography>
              <Typography variant="h6" fontWeight={600} color="success.main">
                {totalSaleProceeds.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="caption" color="text.secondary">{t("assets.totalAssets", "Total Assets")}</Typography>
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
                <TableCell><strong>{t("name", "Name")}</strong></TableCell>
                <TableCell><strong>{t("type", "Type")}</strong></TableCell>
                <TableCell><strong>{t("assets.acquired", "Acquired")}</strong></TableCell>
                <TableCell><strong>{t("assets.acquisitionValue", "Acquisition Value")}</strong></TableCell>
                <TableCell><strong>{t("status", "Status")}</strong></TableCell>
                <TableCell><strong>{t("assets.salePrice", "Sale Price")}</strong></TableCell>
                <TableCell align="right"><strong>{t("actions", "Actions")}</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {assets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4, color: "text.secondary" }}>
                    {t("assets.emptyState", "No assets found. Click \"Add Asset\" to create one.")}
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
                        label={ASSET_TYPES.find((at) => at.value === asset.asset_type)?.label ?? asset.asset_type}
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
                        label={asset.is_sold ? t("assets.sold", "Sold") : t("assets.active", "Active")}
                        size="small"
                        color={asset.is_sold ? "default" : "success"}
                      />
                    </TableCell>
                    <TableCell>
                      {asset.sale?.sale_price != null
                        ? parseFloat(asset.sale.sale_price).toLocaleString("en-US", { minimumFractionDigits: 2 })
                        : "—"}
                    </TableCell>
                    <TableCell align="right">
                      {!asset.is_sold && (
                        <Tooltip title={t("assets.recordSale", "Record Sale")}>
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
        <DialogTitle>{t("assets.addBuildingAsset", "Add Building Asset")}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} pt={1}>
            {assetFormError && <Alert severity="error">{assetFormError}</Alert>}
            <TextField
              label={`${t("name", "Name")} *`}
              name="name"
              value={assetForm.name}
              onChange={handleAssetFormChange}
              fullWidth
              size="small"
              autoFocus
              InputLabelProps={{ shrink: true }}
              placeholder={t("assets.assetNamePlaceholder", "Asset name")}
            />
            <TextField
              label={t("description", "Description")}
              name="description"
              value={assetForm.description}
              onChange={handleAssetFormChange}
              fullWidth
              size="small"
              multiline
              rows={2}
              InputLabelProps={{ shrink: true }}
              placeholder={t("assets.optionalDescription", "Optional description")}
            />
            <FormControl size="small" fullWidth>
              <InputLabel shrink>{t("assets.assetType", "Asset Type")}</InputLabel>
              <Select
                name="asset_type"
                value={assetForm.asset_type}
                label={t("assets.assetType", "Asset Type")}
                onChange={handleAssetFormChange}
              >
                {ASSET_TYPES.map((at) => (
                  <MenuItem key={at.value} value={at.value}>{at.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            {assetForm.asset_type === "other" && (
              <TextField
                label={`${t("assets.specifyAssetType", "Specify asset type")} *`}
                name="other_type_label"
                placeholder={t("assets.specifyAssetTypePlaceholder", "e.g. Generator, Garden Equipment…")}
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
                  label={t("assets.acquisitionDate", "Acquisition Date")}
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
                  label={t("assets.acquisitionValue", "Acquisition Value")}
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
          <Button onClick={() => setAssetFormOpen(false)} disabled={savingAsset}>{t("cancel", "Cancel")}</Button>
          <Button variant="contained" onClick={handleSaveAsset} disabled={savingAsset}>
            {savingAsset ? t("saving", "Saving…") : t("assets.addAsset", "Add Asset")}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Record Sale dialog */}
      <Dialog open={Boolean(saleTarget)} onClose={() => setSaleTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{t("assets.recordSale", "Record Sale")} — {saleTarget?.name}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} pt={1}>
            {saleFormError && <Alert severity="error">{saleFormError}</Alert>}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label={`${t("assets.saleDate", "Sale Date")} *`}
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
                  label={`${t("assets.salePrice", "Sale Price")} *`}
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
                  label={t("assets.buyerName", "Buyer Name")}
                  name="buyer_name"
                  value={saleForm.buyer_name}
                  onChange={handleSaleFormChange}
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                  placeholder={t("optional", "Optional")}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label={t("assets.buyerContact", "Buyer Contact")}
                  name="buyer_contact"
                  value={saleForm.buyer_contact}
                  onChange={handleSaleFormChange}
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                  placeholder={t("assets.phoneOrEmail", "Phone or email")}
                />
              </Grid>
            </Grid>
            <TextField
              label={t("notes", "Notes")}
              name="notes"
              value={saleForm.notes}
              onChange={handleSaleFormChange}
              fullWidth
              size="small"
              multiline
              rows={2}
              InputLabelProps={{ shrink: true }}
              placeholder={t("assets.optionalNotes", "Optional notes")}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaleTarget(null)} disabled={recordingSale}>{t("cancel", "Cancel")}</Button>
          <Button variant="contained" color="success" onClick={handleRecordSale} disabled={recordingSale}>
            {recordingSale ? t("assets.recording", "Recording…") : t("assets.recordSale", "Record Sale")}
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
    </>
  );
}
