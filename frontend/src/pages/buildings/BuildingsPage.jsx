/**
 * Buildings management page – Sprint 2.
 *
 * Features:
 * - List buildings with server-side pagination and search
 * - Create / edit building (admin only)
 * - Soft-delete building (admin only)
 * - Assign owner users to buildings
 */
import { useCallback, useEffect, useState } from "react";
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
import { Add, Apartment, Check, ContentCopy, Delete, Edit, PersonAdd, Send, PersonPin, PowerSettingsNew } from "@mui/icons-material";
import { useForm } from "react-hook-form";
import { buildingsApi } from "../../api/buildingsApi";
import { apartmentsApi } from "../../api/apartmentsApi";
import { usersApi } from "../../api/usersApi";
import { useAuth } from "../../hooks/useAuth";

export default function BuildingsPage() {
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
  const [savingFloors, setSavingFloors] = useState(false);
  const [unitsError, setUnitsError] = useState(null);
  const [inviteEmails, setInviteEmails] = useState({});
  const [inviteLinks, setInviteLinks] = useState({});
  const [inviteCodes, setInviteCodes] = useState({});
  const [invitingUnit, setInvitingUnit] = useState(null);
  const [copiedUnit, setCopiedUnit] = useState(null);
  const [claimingUnit, setClaimingUnit] = useState(null);

  // Admin selector for create/edit dialog
  const [adminUsers, setAdminUsers] = useState([]);
  const [coAdminIds, setCoAdminIds] = useState([]);

  // Assign user dialog
  const [assignTarget, setAssignTarget] = useState(null);
  const [owners, setOwners] = useState([]);
  const [selectedOwner, setSelectedOwner] = useState("");
  const [assignError, setAssignError] = useState(null);
  const [assigning, setAssigning] = useState(false);

  // ── Fetch buildings ──────────────────────────────────────────────────────────
  const fetchBuildings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await buildingsApi.list({
        page: paginationModel.page + 1,
        page_size: paginationModel.pageSize,
      });
      const data = res.data;
      setRows(data.results ?? data);
      setRowCount(data.count ?? (data.results ?? data).length);
    } catch {
      setError("Failed to load buildings.");
    } finally {
      setLoading(false);
    }
  }, [paginationModel]);

  useEffect(() => { fetchBuildings(); }, [fetchBuildings]);

  // ── Create ──────────────────────────────────────────────────────────────────
  const loadAdminUsers = async () => {
    try {
      const res = await usersApi.list({ role: "admin", page_size: 200 });
      setAdminUsers(res.data.results ?? res.data);
    } catch {
      setAdminUsers([]);
    }
  };

  const openCreate = () => {
    setEditTarget(null);
    form.reset({ name: "", address: "", city: "", country: "", num_floors: 1, num_apartments: 0, num_stores: 0, admin_id: "" });
    setCoAdminIds([]);
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
    setDialogError(null);
    loadAdminUsers();
    setDialogOpen(true);
  };

  const onSubmit = async (data) => {
    setSubmitting(true);
    setDialogError(null);
    try {
      const payload = {
        name: data.name,
        address: data.address,
        city: data.city,
        country: data.country,
        num_floors: parseInt(data.num_floors, 10),
        num_apartments: parseInt(data.num_apartments, 10) || 0,
        num_stores: parseInt(data.num_stores, 10) || 0,
      };
      if (data.admin_id) payload.admin_id = data.admin_id;
      if (coAdminIds.length) payload.co_admin_ids = coAdminIds;
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
      setError(err.response?.data?.detail || "Failed to update building status.");
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
      setUnitsError(err.response?.data?.detail || "Failed to generate invite link.");
    } finally {
      setInvitingUnit(null);
    }
  };

  const claimUnit = async (unit) => {
    setClaimingUnit(unit.id);
    setUnitsError(null);
    try {
      await apartmentsApi.claim(unit.id);
      const res = await buildingsApi.apartments(unitsTarget.id);
      setUnits(res.data?.results ?? res.data);
    } catch (err) {
      setUnitsError(err.response?.data?.detail || "Failed to claim unit.");
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
    setInviteEmails({});
    setInviteLinks({});
    setInviteCodes({});
    setUnitsError(null);
    setUnitsLoading(true);
    try {
      const res = await buildingsApi.apartments(building.id);
      setUnits(res.data?.results ?? res.data);
    } catch {
      setUnitsError("Failed to load units.");
    } finally {
      setUnitsLoading(false);
    }
  };

  const saveFloors = async () => {
    const changed = Object.entries(floorEdits);
    if (!changed.length) return;
    setSavingFloors(true);
    setUnitsError(null);
    try {
      await Promise.all(
        changed.map(([id, floor]) =>
          apartmentsApi.update(id, { floor: parseInt(floor, 10) })
        )
      );
      setFloorEdits({});
      const res = await buildingsApi.apartments(unitsTarget.id);
      setUnits(res.data?.results ?? res.data);
    } catch (err) {
      setUnitsError(err.response?.data?.detail || "Failed to save floor changes.");
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
      const res = await usersApi.list({ role: "owner", page_size: 200 });
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
    } catch (err) {
      setAssignError(err.response?.data?.detail || "Assignment failed.");
    } finally {
      setAssigning(false);
    }
  };

  // ── Columns ─────────────────────────────────────────────────────────────────
  const columns = [
    { field: "name", headerName: "Name", flex: 1.2, minWidth: 160 },
    { field: "address", headerName: "Address", flex: 1.5, minWidth: 180 },
    { field: "city", headerName: "City", width: 130 },
    { field: "country", headerName: "Country", width: 120 },
    { field: "num_floors", headerName: "Floors", width: 80, type: "number" },
    {
      field: "is_active",
      headerName: "Status",
      width: 100,
      renderCell: ({ value }) => (
        <Chip
          label={value ? "Active" : "Inactive"}
          size="small"
          color={value ? "success" : "error"}
        />
      ),
    },
    {
      field: "created_at",
      headerName: "Created",
      width: 130,
      valueFormatter: (value) => new Date(value).toLocaleDateString(),
    },
    ...(isAdmin
      ? [
          {
            field: "actions",
            headerName: "Actions",
            width: 170,
            sortable: false,
            renderCell: ({ row }) => (
              <Stack direction="row" spacing={0.5}>
                <Tooltip title="Edit">
                  <IconButton size="small" onClick={() => openEdit(row)}>
                    <Edit fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Manage units">
                  <IconButton size="small" onClick={() => openUnits(row)}>
                    <Apartment fontSize="small" color="secondary" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Assign owner">
                  <IconButton size="small" onClick={() => openAssign(row)}>
                    <PersonAdd fontSize="small" color="primary" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={row.is_active ? "Deactivate" : "Activate"}>
                  <IconButton
                    size="small"
                    color={row.is_active ? "warning" : "success"}
                    onClick={() => handleToggleActive(row)}
                  >
                    <PowerSettingsNew fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
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
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          Buildings
        </Typography>
        {isAdmin && (
          <Button variant="contained" startIcon={<Add />} onClick={openCreate}>
            New Building
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
        <DialogTitle>{editTarget ? "Edit Building" : "New Building"}</DialogTitle>
        <Box component="form" onSubmit={form.handleSubmit(onSubmit)}>
          <DialogContent>
            {dialogError && <Alert severity="error" sx={{ mb: 2 }}>{dialogError}</Alert>}
            <Stack spacing={2}>
              <TextField
                label="Name *"
                fullWidth
                error={!!form.formState.errors.name}
                helperText={form.formState.errors.name?.message}
                {...form.register("name", { required: "Name is required." })}
              />
              <TextField
                label="Address *"
                fullWidth
                error={!!form.formState.errors.address}
                helperText={form.formState.errors.address?.message}
                {...form.register("address", { required: "Address is required." })}
              />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label="City *"
                  fullWidth
                  error={!!form.formState.errors.city}
                  helperText={form.formState.errors.city?.message}
                  {...form.register("city", { required: "City is required." })}
                />
                <TextField
                  label="Country"
                  fullWidth
                  {...form.register("country")}
                />
              </Stack>
              <TextField
                label="Number of Floors *"
                type="number"
                inputProps={{ min: 1 }}
                fullWidth
                error={!!form.formState.errors.num_floors}
                helperText={form.formState.errors.num_floors?.message}
                {...form.register("num_floors", {
                  required: "Number of floors is required.",
                  min: { value: 1, message: "Must be at least 1." },
                })}
              />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label="Apartments"
                  type="number"
                  inputProps={{ min: 0 }}
                  fullWidth
                  helperText="Number of apartment units (auto-creates vacant units)"
                  {...form.register("num_apartments", { min: 0 })}
                />
                <TextField
                  label="Stores"
                  type="number"
                  inputProps={{ min: 0 }}
                  fullWidth
                  helperText="Number of commercial/store units"
                  {...form.register("num_stores", { min: 0 })}
                />
              </Stack>
              <FormControl fullWidth size="small">
                <InputLabel>Building Admin</InputLabel>
                <Select
                  label="Building Admin"
                  defaultValue=""
                  {...form.register("admin_id")}
                >
                  <MenuItem value="">— Assign to me (default) —</MenuItem>
                  {adminUsers.map((u) => (
                    <MenuItem key={u.id} value={u.id}>
                      {u.first_name} {u.last_name} ({u.email})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth size="small">
                <InputLabel>Additional Admins</InputLabel>
                <Select
                  label="Additional Admins"
                  multiple
                  value={coAdminIds}
                  onChange={(e) => setCoAdminIds(e.target.value)}
                  input={<OutlinedInput label="Additional Admins" />}
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
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? "Saving…" : editTarget ? "Save Changes" : "Create"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* ── Delete Dialog ─────────────────────────────────────────────────── */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete Building</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete <strong>{deleteTarget?.name}</strong>?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="contained" color="error" disabled={deleting} onClick={handleDelete}>
            {deleting ? "Deleting…" : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Units Dialog ──────────────────────────────────────────────────── */}
      <Dialog open={Boolean(unitsTarget)} onClose={() => setUnitsTarget(null)} maxWidth="md" fullWidth>
        <DialogTitle>Units — {unitsTarget?.name}</DialogTitle>
        <DialogContent>
          {unitsError && <Alert severity="error" sx={{ mb: 2 }}>{unitsError}</Alert>}
          {unitsLoading ? (
            <Box display="flex" justifyContent="center" p={3}><CircularProgress /></Box>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Unit</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell width={110}>Floor</TableCell>
                  <TableCell>Invite Owner</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {units.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>{u.unit_number}</TableCell>
                    <TableCell>
                      <Chip
                        label={u.type === "store" ? "Store" : "Apt"}
                        size="small"
                        color={u.type === "store" ? "warning" : "primary"}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{u.status}</TableCell>
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
                      {(u.owner_ids?.length > 0 || u.owner_id) ? (
                        <Typography variant="caption" color="text.disabled">
                          Claimed ({u.owner_ids?.length ?? 1} owner{(u.owner_ids?.length ?? 1) !== 1 ? "s" : ""})
                        </Typography>
                      ) : claimingUnit === u.id ? (
                        <CircularProgress size={16} />
                      ) : inviteLinks[u.id] ? (
                        <Stack spacing={0.5}>
                          <Stack direction="row" spacing={0.5} alignItems="center">
                            <Typography variant="caption" sx={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {inviteLinks[u.id]}
                            </Typography>
                            <Tooltip title={copiedUnit === u.id ? "Copied!" : "Copy link"}>
                              <IconButton size="small" onClick={() => copyLink(u.id)}>
                                {copiedUnit === u.id ? <Check fontSize="small" color="success" /> : <ContentCopy fontSize="small" />}
                              </IconButton>
                            </Tooltip>
                          </Stack>
                          {inviteCodes[u.id] && (
                            <Stack direction="row" spacing={0.5} alignItems="center">
                              <Typography variant="caption" color="text.secondary">Code:</Typography>
                              <Chip label={inviteCodes[u.id]} size="small" variant="outlined" color="secondary" />
                            </Stack>
                          )}
                        </Stack>
                      ) : (
                        <Stack spacing={0.5}>
                          <Stack direction="row" spacing={0.5} alignItems="center">
                            <TextField
                              size="small"
                              placeholder="owner@email.com"
                              type="email"
                              value={inviteEmails[u.id] ?? ""}
                              onChange={(e) => setInviteEmails((prev) => ({ ...prev, [u.id]: e.target.value }))}
                              sx={{ width: 160 }}
                            />
                            <Tooltip title="Generate invite link">
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
                          <Tooltip title="Claim this unit for yourself">
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<PersonPin fontSize="small" />}
                              onClick={() => claimUnit(u)}
                              sx={{ alignSelf: "flex-start" }}
                            >
                              Claim for self
                            </Button>
                          </Tooltip>
                        </Stack>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setUnitsTarget(null)}>Close</Button>
          <Button
            variant="contained"
            disabled={!Object.keys(floorEdits).length || savingFloors}
            onClick={saveFloors}
          >
            {savingFloors ? "Saving…" : "Save Floor Changes"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Assign User Dialog ────────────────────────────────────────────── */}
      <Dialog open={Boolean(assignTarget)} onClose={() => setAssignTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Assign Owner — {assignTarget?.name}</DialogTitle>
        <DialogContent>
          {assignError && <Alert severity="error" sx={{ mb: 2 }}>{assignError}</Alert>}
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel>Select Owner</InputLabel>
            <Select
              label="Select Owner"
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
          <Button onClick={() => setAssignTarget(null)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={!selectedOwner || assigning}
            onClick={handleAssign}
          >
            {assigning ? "Assigning…" : "Assign"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
