import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
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
  CheckCircleOutline,
  LockReset,
  SpeakerNotesOff,
} from "@mui/icons-material";
import { useForm } from "react-hook-form";
import { usersApi } from "../../api/usersApi";

const ROLES = ["admin", "owner"];

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
  const [rows, setRows] = useState([]);
  const [rowCount, setRowCount] = useState(0);
  const [paginationModel, setPaginationModel] = useState({ page: 0, pageSize: 20 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Create user dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [createError, setCreateError] = useState(null);
  const [creating, setCreating] = useState(false);
  const createForm = useForm();

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
      setError("Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, [paginationModel]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

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
      setError(err.response?.data?.detail || "Action failed.");
    }
  };

  // ── Create user ─────────────────────────────────────────────────────────────
  const onCreateUser = async (data) => {
    setCreating(true);
    setCreateError(null);
    try {
      await usersApi.create(data);
      setCreateOpen(false);
      createForm.reset();
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
    { field: "email", headerName: "Email", flex: 1.5, minWidth: 200 },
    {
      field: "full_name",
      headerName: "Name",
      flex: 1,
      minWidth: 150,
      valueGetter: (_, row) => `${row.first_name} ${row.last_name}`,
    },
    {
      field: "role",
      headerName: "Role",
      width: 110,
      renderCell: ({ value }) => (
        <Chip
          label={value}
          size="small"
          color={value === "admin" ? "primary" : "default"}
        />
      ),
    },
    {
      field: "is_active",
      headerName: "Status",
      width: 110,
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
      width: 140,
      valueFormatter: (value) => new Date(value).toLocaleDateString(),
    },
    {
      field: "actions",
      headerName: "Actions",
      width: 160,
      sortable: false,
      renderCell: ({ row }) => (
        <Stack direction="row" spacing={0.5}>
          <Tooltip title={row.is_active ? "Deactivate" : "Activate"}>
            <IconButton size="small" onClick={() => toggleActive(row)}>
              {row.is_active ? (
                <Block fontSize="small" color="error" />
              ) : (
                <CheckCircleOutline fontSize="small" color="success" />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title="Reset password">
            <IconButton size="small" onClick={() => { setResetTarget(row); setResetError(null); }}>
              <LockReset fontSize="small" color="warning" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Messaging restrictions">
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
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">User Management</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => { setCreateOpen(true); setCreateError(null); }}>
          New User
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
        <DialogTitle>Create New User</DialogTitle>
        <Box component="form" onSubmit={createForm.handleSubmit(onCreateUser)}>
          <DialogContent>
            {createError && (
              <Alert severity="error" sx={{ mb: 2, whiteSpace: "pre-line" }}>
                {createError}
              </Alert>
            )}
            <Stack spacing={2}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField label="First name" fullWidth required {...createForm.register("first_name", { required: true })} />
                <TextField label="Last name" fullWidth required {...createForm.register("last_name", { required: true })} />
              </Stack>
              <TextField label="Email" type="email" fullWidth required {...createForm.register("email", { required: true })} />
              <TextField label="Phone" fullWidth {...createForm.register("phone")} />
              <TextField label="Role" select fullWidth defaultValue="owner" {...createForm.register("role")}>
                {ROLES.map((r) => <MenuItem key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</MenuItem>)}
              </TextField>
              <TextField label="Password" type="password" fullWidth required {...createForm.register("password", { required: true })} />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>
              {creating ? "Creating…" : "Create"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={!!resetTarget} onClose={() => setResetTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Reset Password — {resetTarget?.email}</DialogTitle>
        <Box component="form" onSubmit={resetForm.handleSubmit(onResetPassword)}>
          <DialogContent>
            {resetError && <Alert severity="error" sx={{ mb: 2 }}>{resetError}</Alert>}
            <Stack spacing={2}>
              <TextField label="New password" type="password" fullWidth required {...resetForm.register("new_password", { required: true })} />
              <TextField label="Confirm password" type="password" fullWidth required {...resetForm.register("confirm_password", { required: true })} />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setResetTarget(null)}>Cancel</Button>
            <Button type="submit" variant="contained" color="warning" disabled={resetting}>
              {resetting ? "Resetting…" : "Reset"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Messaging Restrictions Dialog */}
      <Dialog open={!!msgTarget} onClose={() => setMsgTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Messaging Restrictions — {msgTarget?.email}</DialogTitle>
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
              label="Block all messaging"
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
              label="Block individual (direct) messages only"
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setMsgTarget(null)}>Cancel</Button>
          <Button variant="contained" color="error" disabled={msgSaving} onClick={saveMsgRestrictions}>
            {msgSaving ? "Saving…" : "Save"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
