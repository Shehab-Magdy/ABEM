import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import {
  Add,
  Block,
  CheckBoxOutlineBlank,
  CheckBox as CheckBoxIcon,
  CheckCircleOutline,
  Edit as EditIcon,
  LockReset,
  SpeakerNotesOff,
} from "@mui/icons-material";
import { useForm, Controller } from "react-hook-form";
import { usersApi } from "../../api/usersApi";
import { buildingsApi } from "../../api/buildingsApi";
import { PrivateSEO } from "../../components/seo/SEO";
import PhoneInput from "../../components/PhoneInput";

const ROLES = ["admin", "owner"];
const checkboxIcon = <CheckBoxOutlineBlank fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

function formatApiError(data) {
  if (!data) return "An error occurred.";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  if (typeof data === "object") {
    return Object.entries(data)
      .map(([field, msgs]) => {
        const label = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, " ");
        const text = Array.isArray(msgs) ? msgs.join(", ") : String(msgs);
        return `${label}: ${text}`;
      })
      .join("\n");
  }
  return "An error occurred.";
}

export default function UsersPage() {
  const { t } = useTranslation("users");
  const [rows, setRows] = useState([]);
  const [rowCount, setRowCount] = useState(0);
  const [paginationModel, setPaginationModel] = useState({ page: 0, pageSize: 20 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Buildings list for admin role assignment
  const [buildingsList, setBuildingsList] = useState([]);

  // Create user dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [createError, setCreateError] = useState(null);
  const [creating, setCreating] = useState(false);
  const createForm = useForm({ defaultValues: { role: "owner", buildings: [] } });
  const watchCreateRole = createForm.watch("role");

  // Edit user dialog
  const [editTarget, setEditTarget] = useState(null);
  const [editError, setEditError] = useState(null);
  const [editing, setEditing] = useState(false);
  const editForm = useForm({ defaultValues: { role: "owner", buildings: [] } });
  const watchEditRole = editForm.watch("role");

  // Reset password dialog
  const [resetTarget, setResetTarget] = useState(null);
  const [resetError, setResetError] = useState(null);
  const [resetting, setResetting] = useState(false);
  const resetForm = useForm();

  // Messaging restrictions dialog
  const [msgTarget, setMsgTarget] = useState(null);
  const [msgBlocked, setMsgBlocked] = useState(false);
  const [msgIndividualBlocked, setMsgIndividualBlocked] = useState(false);
  const [msgSaving, setMsgSaving] = useState(false);
  const [msgError, setMsgError] = useState(null);

  // ── Fetch users ─────────────────────────────────────────────────────────────
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await usersApi.list({
        page: paginationModel.page + 1,
        page_size: paginationModel.pageSize,
      });
      setRows(res.data.results);
      setRowCount(res.data.count);
    } catch {
      setError(t("load_error", "Failed to load users."));
    } finally {
      setLoading(false);
    }
  }, [paginationModel]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  // ── Fetch buildings for admin role multi-select ──────────────────────────────
  const fetchBuildings = useCallback(async () => {
    try {
      const res = await buildingsApi.list({ page_size: 200 });
      setBuildingsList(res.data.results || res.data || []);
    } catch {
      // silently ignore — buildings list is optional context
    }
  }, []);

  useEffect(() => { fetchBuildings(); }, [fetchBuildings]);

  // ── Open edit user dialog ─────────────────────────────────────────────────────
  const openEditDialog = (user) => {
    setEditTarget(user);
    setEditError(null);
    editForm.reset({
      first_name: user.first_name,
      last_name: user.last_name,
      phone: user.phone || "",
      role: user.role,
      buildings: user.buildings || [],
    });
  };

  // ── Edit user submit ──────────────────────────────────────────────────────────
  const onEditUser = async (data) => {
    setEditing(true);
    setEditError(null);
    try {
      const payload = {
        first_name: data.first_name?.trim(),
        last_name: data.last_name?.trim(),
        phone: data.phone?.trim(),
        role: data.role,
      };
      if (data.role === "admin") {
        payload.buildings = data.buildings || [];
      } else {
        payload.buildings = [];
      }
      await usersApi.update(editTarget.id, payload);
      setEditTarget(null);
      editForm.reset();
      fetchUsers();
    } catch (err) {
      setEditError(formatApiError(err.response?.data));
    } finally {
      setEditing(false);
    }
  };

  // ── Activate / Deactivate ───────────────────────────────────────────────────
  const toggleActive = async (user) => {
    try {
      if (user.is_active) {
        await usersApi.deactivate(user.id);
      } else {
        await usersApi.activate(user.id);
      }
      fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || t("action_failed", "Action failed."));
    }
  };

  // ── Create user ─────────────────────────────────────────────────────────────
  const onCreateUser = async (data) => {
    setCreating(true);
    setCreateError(null);
    try {
      const payload = {
        first_name: data.first_name?.trim(),
        last_name: data.last_name?.trim(),
        email: data.email?.trim(),
        phone: data.phone?.trim(),
        role: data.role,
        password: data.password,
      };
      if (data.role === "admin") {
        payload.buildings = data.buildings || [];
      }
      await usersApi.create(payload);
      setCreateOpen(false);
      createForm.reset({ role: "owner", buildings: [] });
      fetchUsers();
    } catch (err) {
      setCreateError(formatApiError(err.response?.data));
    } finally {
      setCreating(false);
    }
  };

  // ── Reset password ──────────────────────────────────────────────────────────
  const onResetPassword = async (data) => {
    setResetting(true);
    setResetError(null);
    try {
      await usersApi.resetPassword(resetTarget.id, data);
      setResetTarget(null);
      resetForm.reset();
    } catch (err) {
      setResetError(err.response?.data?.detail || "Reset failed.");
    } finally {
      setResetting(false);
    }
  };

  // ── Messaging restrictions ──────────────────────────────────────────────────
  const openMsgDialog = (user) => {
    setMsgTarget(user);
    setMsgBlocked(user.messaging_blocked);
    setMsgIndividualBlocked(user.individual_messaging_blocked);
    setMsgError(null);
  };

  const saveMsgRestrictions = async () => {
    setMsgSaving(true);
    setMsgError(null);
    try {
      await usersApi.setMessagingBlock(msgTarget.id, {
        messaging_blocked: msgBlocked,
        individual_messaging_blocked: msgIndividualBlocked,
      });
      setMsgTarget(null);
      fetchUsers();
    } catch (err) {
      setMsgError(err.response?.data?.detail || "Failed to update messaging restrictions.");
    } finally {
      setMsgSaving(false);
    }
  };

  // ── DataGrid columns ────────────────────────────────────────────────────────
  const columns = [
    { field: "email", headerName: t("colEmail"), flex: 1.5, minWidth: 200 },
    {
      field: "full_name",
      headerName: t("colName"),
      flex: 1,
      minWidth: 150,
      valueGetter: (_, row) => `${row.first_name} ${row.last_name}`,
    },
    {
      field: "role",
      headerName: t("colRole"),
      width: 110,
      renderCell: ({ value }) => (
        <Chip
          label={value === "admin" ? t("roleAdmin") : t("roleOwner")}
          size="small"
          color={value === "admin" ? "primary" : "default"}
        />
      ),
    },
    {
      field: "is_active",
      headerName: t("colStatus"),
      width: 110,
      renderCell: ({ value }) => (
        <Chip
          label={value ? t("statusActive") : t("statusInactive")}
          size="small"
          color={value ? "success" : "error"}
        />
      ),
    },
    {
      field: "created_at",
      headerName: t("colCreated"),
      width: 140,
      valueFormatter: (value) => new Date(value).toLocaleDateString(),
    },
    {
      field: "actions",
      headerName: t("colActions"),
      width: 200,
      sortable: false,
      renderCell: ({ row }) => (
        <Stack direction="row" spacing={0.5}>
          <Tooltip title={t("editUser")}>
            <IconButton size="small" onClick={() => openEditDialog(row)}>
              <EditIcon fontSize="small" color="info" />
            </IconButton>
          </Tooltip>
          <Tooltip title={row.is_active ? t("deactivate") : t("activate")}>
            <IconButton size="small" onClick={() => toggleActive(row)}>
              {row.is_active ? (
                <Block fontSize="small" color="error" />
              ) : (
                <CheckCircleOutline fontSize="small" color="success" />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title={t("resetPassword")}>
            <IconButton size="small" onClick={() => { setResetTarget(row); setResetError(null); }}>
              <LockReset fontSize="small" color="warning" />
            </IconButton>
          </Tooltip>
          <Tooltip title={t("messagingRestrictions")}>
            <IconButton
              size="small"
              onClick={() => openMsgDialog(row)}
              color={row.messaging_blocked || row.individual_messaging_blocked ? "error" : "default"}
            >
              <SpeakerNotesOff fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      ),
    },
  ];

  return (
    <>
      <PrivateSEO title="ABEM – Users" />
      <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">{t("title")}</Typography>
        <Button id="add-user-btn" variant="contained" startIcon={<Add />} onClick={() => { setCreateOpen(true); setCreateError(null); }}>
          {t("newUser")}
        </Button>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}

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

      {/* Create User Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t("createNewUser")}</DialogTitle>
        <Box component="form" onSubmit={createForm.handleSubmit(onCreateUser)}>
          <DialogContent>
            {createError && (
              <Alert severity="error" sx={{ mb: 2, whiteSpace: "pre-line" }}>
                {createError}
              </Alert>
            )}
            <Stack spacing={2}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField label={t("firstName")} fullWidth required {...createForm.register("first_name", { required: true })} />
                <TextField label={t("lastName")} fullWidth required {...createForm.register("last_name", { required: true })} />
              </Stack>
              <TextField label={t("colEmail")} type="email" fullWidth required {...createForm.register("email", { required: true })} />
              <Controller
                name="phone"
                control={createForm.control}
                defaultValue=""
                render={({ field }) => (
                  <PhoneInput
                    label={t("phone")}
                    value={field.value}
                    onChange={field.onChange}
                  />
                )}
              />
              <Controller
                name="role"
                control={createForm.control}
                defaultValue="owner"
                rules={{ required: t("roleRequired") }}
                render={({ field, fieldState }) => (
                  <TextField
                    {...field}
                    select
                    label={t("colRole")}
                    fullWidth
                    required
                    error={!!fieldState.error}
                    helperText={fieldState.error?.message}
                  >
                    {ROLES.map((r) => (
                      <MenuItem key={r} value={r}>
                        {r === "admin" ? t("roleAdmin") : t("roleOwner")}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
              {watchCreateRole === "admin" && (
                <Controller
                  name="buildings"
                  control={createForm.control}
                  defaultValue={[]}
                  rules={{
                    validate: (v) =>
                      (Array.isArray(v) && v.length > 0) || t("buildingsRequired"),
                  }}
                  render={({ field, fieldState }) => (
                    <Autocomplete
                      multiple
                      options={buildingsList}
                      disableCloseOnSelect
                      getOptionLabel={(opt) => opt.name || ""}
                      isOptionEqualToValue={(opt, val) => opt.id === val.id || opt.id === val}
                      value={buildingsList.filter((b) => (field.value || []).includes(b.id))}
                      onChange={(_, newVal) => field.onChange(newVal.map((b) => b.id))}
                      renderOption={(props, option, { selected }) => {
                        const { key, ...rest } = props;
                        return (
                          <li key={key} {...rest}>
                            <Checkbox
                              icon={checkboxIcon}
                              checkedIcon={checkedIcon}
                              checked={selected}
                              sx={{ mr: 1 }}
                            />
                            {option.name}
                          </li>
                        );
                      }}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label={t("managesBuildings")}
                          placeholder={t("selectBuildings")}
                          error={!!fieldState.error}
                          helperText={fieldState.error?.message}
                        />
                      )}
                    />
                  )}
                />
              )}
              <TextField label={t("password")} type="password" fullWidth required {...createForm.register("password", { required: true })} />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setCreateOpen(false)}>{t("cancel")}</Button>
            <Button type="submit" variant="contained" disabled={creating}>
              {creating ? t("creating") : t("create")}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={!!editTarget} onClose={() => setEditTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{t("editUser")} — {editTarget?.email}</DialogTitle>
        <Box component="form" onSubmit={editForm.handleSubmit(onEditUser)}>
          <DialogContent>
            {editError && (
              <Alert severity="error" sx={{ mb: 2, whiteSpace: "pre-line" }}>
                {editError}
              </Alert>
            )}
            <Stack spacing={2}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField label={t("firstName")} fullWidth required {...editForm.register("first_name", { required: true })} />
                <TextField label={t("lastName")} fullWidth required {...editForm.register("last_name", { required: true })} />
              </Stack>
              <Controller
                name="phone"
                control={editForm.control}
                defaultValue=""
                render={({ field }) => (
                  <PhoneInput
                    label={t("phone")}
                    value={field.value}
                    onChange={field.onChange}
                  />
                )}
              />
              <Controller
                name="role"
                control={editForm.control}
                defaultValue="owner"
                rules={{ required: t("roleRequired") }}
                render={({ field, fieldState }) => (
                  <TextField
                    {...field}
                    select
                    label={t("colRole")}
                    fullWidth
                    required
                    error={!!fieldState.error}
                    helperText={fieldState.error?.message}
                  >
                    {ROLES.map((r) => (
                      <MenuItem key={r} value={r}>
                        {r === "admin" ? t("roleAdmin") : t("roleOwner")}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
              {watchEditRole === "admin" && (
                <Controller
                  name="buildings"
                  control={editForm.control}
                  defaultValue={[]}
                  rules={{
                    validate: (v) =>
                      (Array.isArray(v) && v.length > 0) || t("buildingsRequired"),
                  }}
                  render={({ field, fieldState }) => (
                    <Autocomplete
                      multiple
                      options={buildingsList}
                      disableCloseOnSelect
                      getOptionLabel={(opt) => opt.name || ""}
                      isOptionEqualToValue={(opt, val) => opt.id === val.id || opt.id === val}
                      value={buildingsList.filter((b) => (field.value || []).includes(b.id))}
                      onChange={(_, newVal) => field.onChange(newVal.map((b) => b.id))}
                      renderOption={(props, option, { selected }) => {
                        const { key, ...rest } = props;
                        return (
                          <li key={key} {...rest}>
                            <Checkbox
                              icon={checkboxIcon}
                              checkedIcon={checkedIcon}
                              checked={selected}
                              sx={{ mr: 1 }}
                            />
                            {option.name}
                          </li>
                        );
                      }}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label={t("managesBuildings")}
                          placeholder={t("selectBuildings")}
                          error={!!fieldState.error}
                          helperText={fieldState.error?.message}
                        />
                      )}
                    />
                  )}
                />
              )}
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setEditTarget(null)}>{t("cancel")}</Button>
            <Button type="submit" variant="contained" disabled={editing}>
              {editing ? t("updating") : t("update")}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={!!resetTarget} onClose={() => setResetTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>{t("resetPassword")} — {resetTarget?.email}</DialogTitle>
        <Box component="form" onSubmit={resetForm.handleSubmit(onResetPassword)}>
          <DialogContent>
            {resetError && <Alert severity="error" sx={{ mb: 2 }}>{resetError}</Alert>}
            <Stack spacing={2}>
              <TextField label={t("newPassword")} type="password" fullWidth required {...resetForm.register("new_password", { required: true })} />
              <TextField label={t("confirmPassword")} type="password" fullWidth required {...resetForm.register("confirm_password", { required: true })} />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setResetTarget(null)}>{t("cancel")}</Button>
            <Button type="submit" variant="contained" color="warning" disabled={resetting}>
              {resetting ? t("resetting") : t("reset")}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Messaging Restrictions Dialog */}
      <Dialog open={!!msgTarget} onClose={() => setMsgTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>{t("messagingRestrictions")} — {msgTarget?.email}</DialogTitle>
        <DialogContent>
          {msgError && <Alert severity="error" sx={{ mb: 2 }}>{msgError}</Alert>}
          <Stack spacing={1} sx={{ mt: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={msgBlocked}
                  onChange={(e) => {
                    setMsgBlocked(e.target.checked);
                    if (e.target.checked) setMsgIndividualBlocked(false);
                  }}
                  color="error"
                />
              }
              label={t("blockAllMessaging")}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={msgIndividualBlocked}
                  onChange={(e) => setMsgIndividualBlocked(e.target.checked)}
                  disabled={msgBlocked}
                  color="warning"
                />
              }
              label={t("blockIndividualMessages")}
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setMsgTarget(null)}>{t("cancel")}</Button>
          <Button variant="contained" color="error" disabled={msgSaving} onClick={saveMsgRestrictions}>
            {msgSaving ? t("saving") : t("save")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
    </>
  );
}
