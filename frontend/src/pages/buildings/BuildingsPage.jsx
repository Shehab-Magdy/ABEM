/**
 * Buildings management page – Sprint 2.
 *
 * Features:
 * - List buildings with server-side pagination and search
 * - Create / edit building (admin only)
 * - Soft-delete building (admin only)
 * - Assign owner users to buildings
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  Avatar,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { Add, Apartment, Check, ContentCopy, Delete, Edit, PersonAdd, PhotoCamera, Send, PersonPin, PowerSettingsNew } from "@mui/icons-material";
import { useForm } from "react-hook-form";
import { buildingsApi } from "../../api/buildingsApi";
import { apartmentsApi } from "../../api/apartmentsApi";
import { usersApi } from "../../api/usersApi";
import { useAuth } from "../../hooks/useAuth";
import { useTranslation } from "react-i18next";
import { PrivateSEO } from "../../components/seo/SEO";

export default function BuildingsPage() {
  const { t } = useTranslation("buildings");
  const { isAdmin } = useAuth();

  const [rows, setRows] = useState([]);
  const [rowCount, setRowCount] = useState(0);
  const [paginationModel, setPaginationModel] = useState({ page: 0, pageSize: 20 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Create / Edit dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [dialogError, setDialogError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const form = useForm();

  // Delete dialog
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Units dialog
  const [unitsTarget, setUnitsTarget] = useState(null);
  const [units, setUnits] = useState([]);
  const [unitsLoading, setUnitsLoading] = useState(false);
  const [floorEdits, setFloorEdits] = useState({});
  const [sizeEdits, setSizeEdits] = useState({});
  const [savingFloors, setSavingFloors] = useState(false);
  const [unitsError, setUnitsError] = useState(null);
  const [inviteEmails, setInviteEmails] = useState({});
  const [inviteLinks, setInviteLinks] = useState({});
  const [inviteCodes, setInviteCodes] = useState({});
  const [invitingUnit, setInvitingUnit] = useState(null);
  const [copiedUnit, setCopiedUnit] = useState(null);
  const [claimingUnit, setClaimingUnit] = useState(null);
  const [buildingMembers, setBuildingMembers] = useState([]);

  // Admin selector for create/edit dialog
  const [adminUsers, setAdminUsers] = useState([]);
  const [coAdminIds, setCoAdminIds] = useState([]);

  // Photo upload
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const photoInputRef = useRef(null);

  // Assign user dialog
  const [assignTarget, setAssignTarget] = useState(null);
  const [owners, setOwners] = useState([]);
  const [selectedOwner, setSelectedOwner] = useState("");
  const [assignError, setAssignError] = useState(null);
  const [assigning, setAssigning] = useState(false);

  // ── Fetch buildings ──────────────────────────────────────────────────────────
  const fetchBuildings = useCallback(async (options) => {
    setLoading(true);
    setError(null);
    try {
      const res = await buildingsApi.list({
        page: paginationModel.page + 1,
        page_size: paginationModel.pageSize,
      }, options);
      const data = res.data;
      setRows(data.results ?? data);
      setRowCount(data.count ?? (data.results ?? data).length);
    } catch (err) {
      if (err?.code === "ERR_CANCELED") return; // request was aborted on unmount
      setError(t("load_error", "Failed to load buildings."));
    } finally {
      setLoading(false);
    }
  }, [paginationModel]);

  useEffect(() => {
    const controller = new AbortController();
    fetchBuildings({ signal: controller.signal });
    return () => controller.abort();
  }, [fetchBuildings]);

  // ── Create ──────────────────────────────────────────────────────────────────
  const loadAdminUsers = async () => {
    try {
      const res = await usersApi.list({ role: "admin", page_size: 100 });
      setAdminUsers(res.data.results ?? res.data);
    } catch {
      setAdminUsers([]);
    }
  };

  const openCreate = () => {
    setEditTarget(null);
    form.reset({ name: "", address: "", city: "", country: "", num_floors: 1, num_apartments: 0, num_stores: 0, admin_id: "" });
    setCoAdminIds([]);
    setPhotoFile(null);
    setPhotoPreview(null);
    setDialogError(null);
    loadAdminUsers();
    setDialogOpen(true);
  };

  // ── Edit ────────────────────────────────────────────────────────────────────
  const openEdit = (building) => {
    setEditTarget(building);
    form.reset({
      name: building.name,
      address: building.address,
      city: building.city,
      country: building.country || "",
      num_floors: building.num_floors,
      num_apartments: building.num_apartments ?? 0,
      num_stores: building.num_stores ?? 0,
      admin_id: building.admin_id || "",
    });
    setCoAdminIds(building.co_admin_ids ?? []);
    setPhotoFile(null);
    setPhotoPreview(building.photo || null);
    setDialogError(null);
    loadAdminUsers();
    setDialogOpen(true);
  };

  const onSubmit = async (data) => {
    setSubmitting(true);
    setDialogError(null);
    try {
      const fields = {
        name: data.name?.trim(),
        address: data.address?.trim(),
        city: data.city?.trim(),
        country: data.country?.trim(),
        num_floors: parseInt(data.num_floors, 10),
        num_apartments: parseInt(data.num_apartments, 10) || 0,
        num_stores: parseInt(data.num_stores, 10) || 0,
      };
      if (data.admin_id) fields.admin_id = data.admin_id;
      if (coAdminIds.length) fields.co_admin_ids = coAdminIds;

      let payload;
      if (photoFile) {
        payload = new FormData();
        Object.entries(fields).forEach(([key, value]) => {
          if (Array.isArray(value)) {
            value.forEach((v) => payload.append(key, v));
          } else {
            payload.append(key, value);
          }
        });
        payload.append("photo", photoFile);
      } else {
        payload = fields;
      }

      if (editTarget) {
        await buildingsApi.update(editTarget.id, payload);
      } else {
        await buildingsApi.create(payload);
      }
      setDialogOpen(false);
      fetchBuildings();
    } catch (err) {
      const detail = err.response?.data;
      setDialogError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setSubmitting(false);
    }
  };

  // ── Delete ──────────────────────────────────────────────────────────────────
  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await buildingsApi.remove(deleteTarget.id);
      setDeleteTarget(null);
      fetchBuildings();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete building.");
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  // ── Deactivate / Activate ────────────────────────────────────────────────────
  const handleToggleActive = async (building) => {
    try {
      if (building.is_active) {
        await buildingsApi.deactivate(building.id);
      } else {
        await buildingsApi.activate(building.id);
      }
      fetchBuildings();
    } catch (err) {
      setError(err.response?.data?.detail || t("status_update_error", "Failed to update building status."));
    }
  };

  // ── Units ────────────────────────────────────────────────────────────────────
  const generateInvite = async (unit) => {
    const email = inviteEmails[unit.id]?.trim();
    if (!email) return;
    setInvitingUnit(unit.id);
    setUnitsError(null);
    try {
      const res = await apartmentsApi.inviteUnit(unit.id, email);
      const link = `${window.location.origin}/register?invite=${res.data.token}`;
      setInviteLinks((prev) => ({ ...prev, [unit.id]: link }));
      setInviteCodes((prev) => ({ ...prev, [unit.id]: res.data.registration_code }));
    } catch (err) {
      setUnitsError(err.response?.data?.detail || t("invite_error", "Failed to generate invite link."));
    } finally {
      setInvitingUnit(null);
    }
  };

  const claimUnit = async (unit) => {
    setClaimingUnit(unit.id);
    setUnitsError(null);
    try {
      await apartmentsApi.claim(unit.id);
      const res = await buildingsApi.apartments(unitsTarget.id, { page_size: 100 });
      setUnits(res.data?.results ?? res.data);
    } catch (err) {
      setUnitsError(err.response?.data?.detail || t("claim_error", "Failed to claim unit."));
    } finally {
      setClaimingUnit(null);
    }
  };

  const copyLink = (unitId) => {
    navigator.clipboard.writeText(inviteLinks[unitId]);
    setCopiedUnit(unitId);
    setTimeout(() => setCopiedUnit(null), 2000);
  };

  const openUnits = async (building) => {
    setUnitsTarget(building);
    setFloorEdits({});
    setSizeEdits({});
    setInviteEmails({});
    setInviteLinks({});
    setInviteCodes({});
    setUnitsError(null);
    setBuildingMembers([]);
    setUnitsLoading(true);
    try {
      const [unitsRes, membersRes] = await Promise.all([
        buildingsApi.apartments(building.id, { page_size: 100 }),
        usersApi.list({ building_id: building.id, page_size: 100 }),
      ]);
      setUnits(unitsRes.data?.results ?? unitsRes.data);
      setBuildingMembers(membersRes.data?.results ?? membersRes.data ?? []);
    } catch {
      setUnitsError(t("units_load_error", "Failed to load units."));
    } finally {
      setUnitsLoading(false);
    }
  };

  const saveUnitEdits = async () => {
    // Merge floor and size edits per unit into a single patch per unit
    const unitIds = new Set([...Object.keys(floorEdits), ...Object.keys(sizeEdits)]);
    if (!unitIds.size) return;
    setSavingFloors(true);
    setUnitsError(null);
    try {
      await Promise.all(
        [...unitIds].map((id) => {
          const patch = {};
          if (id in floorEdits) patch.floor = parseInt(floorEdits[id], 10);
          if (id in sizeEdits) patch.size_sqm = sizeEdits[id] === "" ? null : parseFloat(sizeEdits[id]);
          return apartmentsApi.update(id, patch);
        })
      );
      setFloorEdits({});
      setSizeEdits({});
      const res = await buildingsApi.apartments(unitsTarget.id, { page_size: 100 });
      setUnits(res.data?.results ?? res.data);
    } catch (err) {
      setUnitsError(err.response?.data?.detail || t("unit_save_error", "Failed to save unit changes."));
    } finally {
      setSavingFloors(false);
    }
  };

  // ── Assign user ─────────────────────────────────────────────────────────────
  const openAssign = async (building) => {
    setAssignTarget(building);
    setAssignError(null);
    setSelectedOwner("");
    try {
      const res = await usersApi.list({ role: "owner", page_size: 100 });
      setOwners(res.data.results ?? res.data);
    } catch {
      setOwners([]);
    }
  };

  const handleAssign = async () => {
    if (!selectedOwner || !assignTarget) return;
    setAssigning(true);
    setAssignError(null);
    try {
      await buildingsApi.assignUser(assignTarget.id, selectedOwner);
      setAssignTarget(null);
      fetchBuildings();
    } catch (err) {
      setAssignError(err.response?.data?.detail || t("assign_error", "Assignment failed."));
    } finally {
      setAssigning(false);
    }
  };

  // ── Columns ─────────────────────────────────────────────────────────────────
  const columns = [
    { field: "name", headerName: t("name"), flex: 1.2, minWidth: 160 },
    { field: "address", headerName: t("address"), flex: 1.5, minWidth: 180 },
    { field: "city", headerName: t("city"), width: 130 },
    { field: "country", headerName: t("country"), width: 120 },
    { field: "num_floors", headerName: t("floors"), width: 80, type: "number" },
    {
      field: "is_active",
      headerName: t("status"),
      width: 100,
      renderCell: ({ value }) => (
        <Chip
          label={value ? t("active") : t("inactive")}
          size="small"
          color={value ? "success" : "error"}
        />
      ),
    },
    {
      field: "created_at",
      headerName: t("created"),
      width: 130,
      valueFormatter: (value) => new Date(value).toLocaleDateString(),
    },
    ...(isAdmin
      ? [
          {
            field: "actions",
            headerName: t("actions"),
            width: 170,
            sortable: false,
            renderCell: ({ row }) => (
              <Stack id="building-actions-row" direction="row" spacing={0.5}>
                <Tooltip title={t("edit")}>
                  <IconButton size="small" onClick={() => openEdit(row)}>
                    <Edit fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={t("manage_units")}>
                  <IconButton size="small" onClick={() => openUnits(row)}>
                    <Apartment fontSize="small" color="secondary" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={t("assign_owner")}>
                  <IconButton size="small" onClick={() => openAssign(row)}>
                    <PersonAdd fontSize="small" color="primary" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={row.is_active ? t("deactivate_building") : t("activate_building")}>
                  <IconButton
                    size="small"
                    color={row.is_active ? "warning" : "success"}
                    onClick={() => handleToggleActive(row)}
                  >
                    <PowerSettingsNew fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={t("delete")}>
                  <IconButton size="small" color="error" onClick={() => setDeleteTarget(row)}>
                    <Delete fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Stack>
            ),
          },
        ]
      : []),
  ];

  return (
    <>
      <PrivateSEO title="ABEM – Buildings" />
      <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          {t("page_title")}
        </Typography>
        {isAdmin && (
          <Button id="add-building-btn" variant="contained" startIcon={<Add />} onClick={openCreate}>
            {t("new_building")}
          </Button>
        )}
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <DataGrid
        rows={rows}
        columns={columns}
        rowCount={rowCount}
        loading={loading}
        paginationMode="server"
        paginationModel={paginationModel}
        onPaginationModelChange={setPaginationModel}
        pageSizeOptions={[10, 20, 50]}
        autoHeight
        disableRowSelectionOnClick
        sx={{ bgcolor: "background.paper" }}
      />

      {/* ── Create / Edit Dialog ──────────────────────────────────────────── */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editTarget ? t("edit_building") : t("new_building")}</DialogTitle>
        <Box component="form" onSubmit={form.handleSubmit(onSubmit)}>
          <DialogContent>
            {dialogError && <Alert severity="error" sx={{ mb: 2 }}>{dialogError}</Alert>}
            <Stack spacing={2}>
              {/* Photo upload */}
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar
                  src={photoPreview || undefined}
                  variant="rounded"
                  sx={{ width: 80, height: 80, bgcolor: "grey.200" }}
                >
                  {!photoPreview && <PhotoCamera sx={{ color: "grey.500" }} />}
                </Avatar>
                <Box>
                  <input
                    ref={photoInputRef}
                    type="file"
                    accept="image/jpeg,image/png"
                    hidden
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setPhotoFile(file);
                        setPhotoPreview(URL.createObjectURL(file));
                      }
                    }}
                  />
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<PhotoCamera />}
                    onClick={() => photoInputRef.current?.click()}
                  >
                    {t("upload_photo")}
                  </Button>
                  {photoPreview && (
                    <Button
                      size="small"
                      color="error"
                      sx={{ ml: 1 }}
                      onClick={() => { setPhotoFile(null); setPhotoPreview(null); }}
                    >
                      {t("remove")}
                    </Button>
                  )}
                </Box>
              </Stack>
              <TextField
                label={`${t("name")} *`}
                fullWidth
                error={!!form.formState.errors.name}
                helperText={form.formState.errors.name?.message}
                {...form.register("name", { required: t("name_required") })}
              />
              <TextField
                label={`${t("address")} *`}
                fullWidth
                error={!!form.formState.errors.address}
                helperText={form.formState.errors.address?.message}
                {...form.register("address", { required: t("address_required") })}
              />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label={`${t("city")} *`}
                  fullWidth
                  error={!!form.formState.errors.city}
                  helperText={form.formState.errors.city?.message}
                  {...form.register("city", { required: t("city_required") })}
                />
                <TextField
                  label={t("country")}
                  fullWidth
                  {...form.register("country")}
                />
              </Stack>
              <TextField
                label={`${t("num_floors")} *`}
                type="number"
                inputProps={{ min: 1 }}
                fullWidth
                error={!!form.formState.errors.num_floors}
                helperText={form.formState.errors.num_floors?.message}
                {...form.register("num_floors", {
                  required: t("floors_required"),
                  min: { value: 1, message: t("floors_min") },
                })}
              />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label={t("num_apartments")}
                  type="number"
                  inputProps={{ min: 0 }}
                  fullWidth
                  {...form.register("num_apartments", { min: 0 })}
                />
                <TextField
                  label={t("num_stores")}
                  type="number"
                  inputProps={{ min: 0 }}
                  fullWidth
                  {...form.register("num_stores", { min: 0 })}
                />
              </Stack>
              <FormControl fullWidth size="small">
                <InputLabel>{t("building_admin")}</InputLabel>
                <Select
                  label={t("building_admin")}
                  defaultValue=""
                  {...form.register("admin_id")}
                >
                  <MenuItem value="">{t("assign_to_me")}</MenuItem>
                  {adminUsers.map((u) => (
                    <MenuItem key={u.id} value={u.id}>
                      {u.first_name} {u.last_name} ({u.email})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth size="small">
                <InputLabel>{t("additional_admins")}</InputLabel>
                <Select
                  label={t("additional_admins")}
                  multiple
                  value={coAdminIds}
                  onChange={(e) => setCoAdminIds(e.target.value)}
                  input={<OutlinedInput label={t("additional_admins")} />}
                  renderValue={(selected) =>
                    selected.map((id) => {
                      const u = adminUsers.find((a) => a.id === id);
                      return u ? (
                        <Chip key={id} label={`${u.first_name} ${u.last_name}`} size="small" sx={{ mr: 0.5 }} />
                      ) : null;
                    })
                  }
                >
                  {adminUsers.map((u) => (
                    <MenuItem key={u.id} value={u.id}>
                      <Checkbox checked={coAdminIds.includes(u.id)} />
                      <ListItemText primary={`${u.first_name} ${u.last_name}`} secondary={u.email} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setDialogOpen(false)}>{t("cancel")}</Button>
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? t("saving") : editTarget ? t("save_changes") : t("create")}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* ── Delete Dialog ─────────────────────────────────────────────────── */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>{t("delete_building")}</DialogTitle>
        <DialogContent>
          <Typography>
            {t("confirm_delete")}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>{t("cancel")}</Button>
          <Button variant="contained" color="error" disabled={deleting} onClick={handleDelete}>
            {deleting ? t("deleting") : t("delete")}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Units Dialog ──────────────────────────────────────────────────── */}
      <Dialog open={Boolean(unitsTarget)} onClose={() => setUnitsTarget(null)} maxWidth="md" fullWidth>
        <DialogTitle>{t("units_title", { name: unitsTarget?.name })}</DialogTitle>
        <DialogContent>
          {unitsError && <Alert severity="error" sx={{ mb: 2 }}>{unitsError}</Alert>}
          {unitsLoading ? (
            <Box display="flex" justifyContent="center" p={3}><CircularProgress /></Box>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t("unit")}</TableCell>
                  <TableCell>{t("type")}</TableCell>
                  <TableCell>{t("status")}</TableCell>
                  <TableCell width={110}>{t("floor")}</TableCell>
                  <TableCell width={110}>{t("size_sqm")}</TableCell>
                  <TableCell>{t("invite_owner")}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {units.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>{u.unit_number}</TableCell>
                    <TableCell>
                      <Chip
                        label={u.type === "store" ? t("store") : t("apt")}
                        size="small"
                        color={u.type === "store" ? "warning" : "primary"}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      {{
                        'Occupied': t('status_occupied'),
                        'Vacant': t('status_vacant'),
                        'Under Maintenance': t('status_under_maintenance'),
                        'occupied': t('status_occupied'),
                        'vacant': t('status_vacant'),
                        'under_maintenance': t('status_under_maintenance'),
                      }[u.status] || u.status}
                    </TableCell>
                    <TableCell>
                      <TextField
                        type="number"
                        size="small"
                        inputProps={{ min: 0, max: unitsTarget?.num_floors ?? 99 }}
                        value={floorEdits[u.id] ?? u.floor}
                        onChange={(e) =>
                          setFloorEdits((prev) => ({ ...prev, [u.id]: e.target.value }))
                        }
                        sx={{ width: 80 }}
                      />
                    </TableCell>
                    <TableCell>
                      <TextField
                        type="number"
                        size="small"
                        inputProps={{ min: 0, step: "0.01" }}
                        value={sizeEdits[u.id] ?? u.size_sqm ?? ""}
                        onChange={(e) =>
                          setSizeEdits((prev) => ({ ...prev, [u.id]: e.target.value }))
                        }
                        sx={{ width: 90 }}
                      />
                    </TableCell>
                    <TableCell>
                      <Stack spacing={0.5}>
                        {/* Current owners */}
                        {u.owner_names?.length > 0 && (
                          <Typography variant="caption" color="text.secondary">
                            {u.owner_names.join(", ")}
                          </Typography>
                        )}
                        {/* Invite form */}
                        {claimingUnit === u.id ? (
                          <CircularProgress size={16} />
                        ) : inviteLinks[u.id] ? (
                          <Stack spacing={0.5}>
                            <Stack direction="row" spacing={0.5} alignItems="center">
                              <Typography variant="caption" sx={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                {inviteLinks[u.id]}
                              </Typography>
                              <Tooltip title={copiedUnit === u.id ? t("copied") : t("copy_link")}>
                                <IconButton size="small" onClick={() => copyLink(u.id)}>
                                  {copiedUnit === u.id ? <Check fontSize="small" color="success" /> : <ContentCopy fontSize="small" />}
                                </IconButton>
                              </Tooltip>
                            </Stack>
                            {inviteCodes[u.id] && (
                              <Stack direction="row" spacing={0.5} alignItems="center">
                                <Typography variant="caption" color="text.secondary">{t("code_label", "Code:")}</Typography>
                                <Chip label={inviteCodes[u.id]} size="small" variant="outlined" color="secondary" />
                              </Stack>
                            )}
                            <Button
                              size="small"
                              onClick={() => setInviteLinks((prev) => ({ ...prev, [u.id]: null }))}
                              sx={{ alignSelf: "flex-start", textTransform: "none", p: 0, minWidth: 0 }}
                            >
                              {t("invite_another")}
                            </Button>
                          </Stack>
                        ) : (
                          <Stack spacing={0.5}>
                            <Stack direction="row" spacing={0.5} alignItems="center">
                              <Autocomplete
                                freeSolo
                                size="small"
                                options={buildingMembers.map((m) => m.email)}
                                inputValue={inviteEmails[u.id] ?? ""}
                                onInputChange={(_, val) => setInviteEmails((prev) => ({ ...prev, [u.id]: val }))}
                                sx={{ width: 200 }}
                                renderInput={(params) => (
                                  <TextField
                                    {...params}
                                    placeholder="owner@email.com"
                                    type="email"
                                  />
                                )}
                              />
                              <Tooltip title={t("generate_invite_link")}>
                                <span>
                                  <IconButton
                                    size="small"
                                    color="primary"
                                    disabled={!inviteEmails[u.id]?.trim() || invitingUnit === u.id}
                                    onClick={() => generateInvite(u)}
                                  >
                                    {invitingUnit === u.id ? <CircularProgress size={16} /> : <Send fontSize="small" />}
                                  </IconButton>
                                </span>
                              </Tooltip>
                            </Stack>
                            {!(u.owner_ids?.length > 0 || u.owner_id) && (
                              <Tooltip title={t("claim_for_self")}>
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<PersonPin fontSize="small" />}
                                  onClick={() => claimUnit(u)}
                                  sx={{ alignSelf: "flex-start" }}
                                >
                                  {t("claim_for_self")}
                                </Button>
                              </Tooltip>
                            )}
                          </Stack>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setUnitsTarget(null)}>{t("close")}</Button>
          <Button
            variant="contained"
            disabled={(!Object.keys(floorEdits).length && !Object.keys(sizeEdits).length) || savingFloors}
            onClick={saveUnitEdits}
          >
            {savingFloors ? t("saving") : t("save_unit_changes")}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Assign User Dialog ────────────────────────────────────────────── */}
      <Dialog open={Boolean(assignTarget)} onClose={() => setAssignTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>{t("assign_owner_title", { name: assignTarget?.name })}</DialogTitle>
        <DialogContent>
          {assignError && <Alert severity="error" sx={{ mb: 2 }}>{assignError}</Alert>}
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel>{t("select_owner")}</InputLabel>
            <Select
              label={t("select_owner")}
              value={selectedOwner}
              onChange={(e) => setSelectedOwner(e.target.value)}
            >
              {owners.map((u) => (
                <MenuItem key={u.id} value={u.id}>
                  {u.email} — {u.first_name} {u.last_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setAssignTarget(null)}>{t("cancel")}</Button>
          <Button
            variant="contained"
            disabled={!selectedOwner || assigning}
            onClick={handleAssign}
          >
            {assigning ? t("assigning") : t("assign")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
    </>
  );
}
