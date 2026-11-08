import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm, Controller } from "react-hook-form";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
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
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  Snackbar,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { CameraAlt, Translate } from "@mui/icons-material";
import { authApi } from "../../api/authApi";
import { useAuth } from "../../hooks/useAuth";
import { useAuthStore } from "../../contexts/authStore";
import { PrivateSEO } from "../../components/seo/SEO";
import NotificationPreferences from "../../components/NotificationPreferences";
import PhoneInput from "../../components/PhoneInput";
import ConfirmDialog from "../../components/ConfirmDialog";
import { formatRelativeTime } from "../../utils/formatters";

export default function ProfilePage() {
  const { t, i18n } = useTranslation("profile");
  const { user, setUser } = useAuth();
  const storeSetUser = useAuthStore((s) => s.setUser);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [uploadingPic, setUploadingPic] = useState(false);
  const [picError, setPicError] = useState(null);
  const [langSaving, setLangSaving] = useState(false);
  const [langSuccess, setLangSuccess] = useState(false);
  const [revokeSuccess, setRevokeSuccess] = useState(false);
  const [revokeError, setRevokeError] = useState(null);
  const [revoking, setRevoking] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [sessionsError, setSessionsError] = useState(null);
  const [revokeSessionTarget, setRevokeSessionTarget] = useState(null);
  const [sessionActionSuccess, setSessionActionSuccess] = useState(false);
  const [sessionActionError, setSessionActionError] = useState(null);
  const fileInputRef = useRef(null);

  const profileForm = useForm({ defaultValues: { first_name: user?.first_name, last_name: user?.last_name, phone: user?.phone } });

  // ── Profile picture upload ───────────────────────────────────────────────────
  const handlePictureChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPicError(null);
    setUploadingPic(true);
    try {
      const res = await authApi.uploadProfilePicture(file);
      setUser(res.data);
    } catch {
      setPicError(t("photo_upload_error", "Could not upload photo."));
    } finally {
      setUploadingPic(false);
      e.target.value = "";
    }
  };

  // ── Update profile ──────────────────────────────────────────────────────────
  const onSaveProfile = async (data) => {
    setSavingProfile(true);
    setProfileError(null);
    setProfileSuccess(false);
    try {
      const res = await authApi.updateProfile({
        ...data,
        first_name: data.first_name?.trim(),
        last_name: data.last_name?.trim(),
        phone: data.phone?.trim(),
      });
      setUser(res.data);
      setProfileSuccess(true);
    } catch {
      setProfileError(t("profile_update_error", "Failed to update profile."));
    } finally {
      setSavingProfile(false);
    }
  };

  // ── Signed-in devices (sessions) ────────────────────────────────────────────
  const fetchSessions = async () => {
    setSessionsLoading(true);
    setSessionsError(null);
    try {
      const res = await authApi.listSessions();
      setSessions(res.data);
    } catch {
      setSessionsError(t("devicesListError", "Could not load your signed-in devices."));
    } finally {
      setSessionsLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleRevokeSession = async () => {
    const target = revokeSessionTarget;
    try {
      await authApi.revokeSession(target.id);
      setRevokeSessionTarget(null);
      setSessionActionSuccess(true);
      setSessionActionError(null);
      await fetchSessions();
    } catch (err) {
      if (err.response?.status === 400) {
        // The session couldn't be revoked as "current" (shouldn't happen since
        // the UI hides the revoke action on that row) — surface and refresh.
        setRevokeSessionTarget(null);
        setSessionActionError(err.response?.data?.detail || t("devicesRevokeError", "Could not sign out that device."));
        await fetchSessions();
        return;
      }
      throw err; // let ConfirmDialog show the error inline for other failures
    }
  };

  // ── Log out of all other devices ────────────────────────────────────────────
  const onRevokeAllDevices = async () => {
    setRevoking(true);
    setRevokeError(null);
    setRevokeSuccess(false);
    try {
      await authApi.revokeAllDevices();
      setRevokeSuccess(true);
      await fetchSessions();
    } catch {
      setRevokeError(t("revokeDevicesError", "Could not log out other devices."));
    } finally {
      setRevoking(false);
    }
  };

  // ── Delete my account ───────────────────────────────────────────────────────
  const navigate = useNavigate();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteCode, setDeleteCode] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  const [balanceOwed, setBalanceOwed] = useState(null); // set when the server asks to confirm an unpaid balance
  const [sendingDeleteCode, setSendingDeleteCode] = useState(false);
  const [deleteCodeSent, setDeleteCodeSent] = useState(false);

  const handleSendDeleteCode = async () => {
    setSendingDeleteCode(true);
    setDeleteError(null);
    try {
      let { data } = await authApi.requestOtp(user?.email);
      if (data.access) {
        // This device is still marked "trusted" (from signing in here),
        // so otp/request/ skipped emailing a code and just re-authenticated
        // us instead — but deleting the account still needs a real code.
        // Clear the trusted-device grant and ask for one again; this time
        // the backend can't bypass it.
        await authApi.revokeAllDevices();
        ({ data } = await authApi.requestOtp(user?.email));
      }
      if (data.access) {
        // Still bypassing somehow — surface rather than loop forever.
        setDeleteError(t("errors:server_error"));
        return;
      }
      setDeleteCodeSent(true);
    } catch {
      setDeleteError(t("errors:server_error"));
    } finally {
      setSendingDeleteCode(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      await authApi.deleteAccount(deleteCode, balanceOwed !== null);
      useAuthStore.getState().logout();
      navigate("/login", { replace: true });
    } catch (err) {
      if (err.response?.data?.requires_confirmation) {
        setBalanceOwed(err.response.data.balance);
      } else {
        setDeleteError(err.response?.data?.detail || t("errors:server_error"));
      }
    } finally {
      setDeleting(false);
    }
  };

  // ── Language preference ─────────────────────────────────────────────────────
  const currentLang = (i18n.language || "en").startsWith("ar") ? "ar" : "en";

  const handleLanguageChange = async (e) => {
    const lang = e.target.value;
    setLangSaving(true);
    i18n.changeLanguage(lang);
    try {
      localStorage.setItem("abem_language", lang);
      const res = await authApi.updateProfile({ preferred_language: lang });
      storeSetUser(res.data);
      setLangSuccess(true);
    } catch {
      // Revert on failure
      i18n.changeLanguage(currentLang);
    } finally {
      setLangSaving(false);
    }
  };

  return (
    <>
      <PrivateSEO title="3maracom – Profile" />
      <Snackbar
        open={langSuccess}
        autoHideDuration={3000}
        onClose={() => setLangSuccess(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="success" onClose={() => setLangSuccess(false)}>
          {t("language_updated")}
        </Alert>
      </Snackbar>
      <Box id="profile-card" maxWidth={640}>
      <Box id="tutorial-profile-form">
      <Typography variant="h5" mb={3}>{t("title")}</Typography>

      {/* Profile picture */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>{t("profilePicture")}</Typography>
          {picError && <Alert severity="error" sx={{ mb: 2 }}>{picError}</Alert>}
          <Stack direction="row" spacing={3} alignItems="center">
            <Box sx={{ position: "relative", display: "inline-flex" }}>
              <Avatar
                src={user?.profile_picture || undefined}
                sx={{ width: 88, height: 88, fontSize: 32 }}
              >
                {!user?.profile_picture && (user?.first_name?.[0] ?? "?")}
              </Avatar>
              <Tooltip title={t("changePhoto")}>
                <IconButton
                  size="small"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingPic}
                  sx={{
                    position: "absolute",
                    bottom: 0,
                    right: 0,
                    bgcolor: "primary.main",
                    color: "white",
                    "&:hover": { bgcolor: "primary.dark" },
                    width: 28,
                    height: 28,
                  }}
                >
                  {uploadingPic
                    ? <CircularProgress size={14} color="inherit" />
                    : <CameraAlt sx={{ fontSize: 16 }} />}
                </IconButton>
              </Tooltip>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                hidden
                onChange={handlePictureChange}
              />
            </Box>
            <Stack spacing={0.5}>
              <Typography variant="body2" fontWeight={500}>
                {user?.first_name} {user?.last_name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {t("clickCameraToUpload")}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {t("acceptedFormats")}
              </Typography>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {/* Profile details */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>{t("personalInformation")}</Typography>
          {profileSuccess && <Alert severity="success" sx={{ mb: 2 }}>{t("profileUpdatedSuccess")}</Alert>}
          {profileError && <Alert severity="error" sx={{ mb: 2 }}>{profileError}</Alert>}
          <Box component="form" onSubmit={profileForm.handleSubmit(onSaveProfile)}>
            <Stack spacing={2.5}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label={t("firstName")}
                  fullWidth
                  error={!!profileForm.formState.errors.first_name}
                  helperText={profileForm.formState.errors.first_name?.message}
                  {...profileForm.register("first_name", { required: "Required." })}
                />
                <TextField
                  label={t("lastName")}
                  fullWidth
                  error={!!profileForm.formState.errors.last_name}
                  helperText={profileForm.formState.errors.last_name?.message}
                  {...profileForm.register("last_name", { required: "Required." })}
                />
              </Stack>
              <Controller
                name="phone"
                control={profileForm.control}
                render={({ field }) => (
                  <PhoneInput
                    label={t("phoneNumber")}
                    value={field.value}
                    onChange={field.onChange}
                    fullWidth
                  />
                )}
              />
              <TextField label={t("email")} fullWidth disabled value={user?.email || ""} />
              <Button type="submit" variant="contained" disabled={savingProfile} sx={{ alignSelf: "flex-start" }}>
                {savingProfile ? <CircularProgress size={20} color="inherit" /> : t("saveChanges")}
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>

      {/* Language & Region */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1} mb={2}>
            <Translate color="action" />
            <Typography variant="h6">{t("language_region")}</Typography>
          </Stack>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>{t("language")}</InputLabel>
            <Select
              value={currentLang}
              label={t("language")}
              onChange={handleLanguageChange}
              disabled={langSaving}
            >
              <MenuItem value="en">🇬🇧 {t("english")}</MenuItem>
              <MenuItem value="ar">🇪🇬 {t("arabic")}</MenuItem>
            </Select>
          </FormControl>
        </CardContent>
      </Card>

      {/* Sign-in & devices */}
      <Card>
        <CardContent>
          <Typography variant="h6" mb={2}>{t("signInSecurity")}</Typography>
          {revokeSuccess && <Alert severity="success" sx={{ mb: 2 }}>{t("revokeDevicesSuccess")}</Alert>}
          {revokeError && <Alert severity="error" sx={{ mb: 2 }}>{revokeError}</Alert>}
          {sessionActionSuccess && (
            <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSessionActionSuccess(false)}>
              {t("devicesRevokeSuccess")}
            </Alert>
          )}
          {sessionActionError && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setSessionActionError(null)}>
              {sessionActionError}
            </Alert>
          )}

          <Typography variant="subtitle2" sx={{ mb: 1 }}>{t("devicesListTitle")}</Typography>

          {sessionsLoading ? (
            <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 2 }}>
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">{t("devicesListLoading")}</Typography>
            </Stack>
          ) : sessionsError ? (
            <Alert severity="error" sx={{ mb: 2 }}>{sessionsError}</Alert>
          ) : (
            <List disablePadding sx={{ mb: 2 }}>
              {sessions.map((session, idx) => (
                <Box key={session.id}>
                  {idx > 0 && <Divider component="li" />}
                  <ListItem
                    disableGutters
                    secondaryAction={
                      !session.is_current && (
                        <Button
                          size="small"
                          color="warning"
                          variant="outlined"
                          onClick={() => setRevokeSessionTarget(session)}
                          sx={{ minHeight: 36 }}
                        >
                          {t("devicesSignOut")}
                        </Button>
                      )
                    }
                  >
                    <ListItemText
                      primary={
                        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                          <Typography variant="body2" fontWeight={500}>
                            {session.device_label || t("devicesUnknownDevice")}
                          </Typography>
                          {session.is_current && (
                            <Chip size="small" color="primary" label={t("devicesThisDevice")} />
                          )}
                        </Stack>
                      }
                      secondary={
                        <>
                          {t("devicesLastActive", { time: formatRelativeTime(session.last_used_at) })}
                          {session.ip_address ? ` · ${session.ip_address}` : ""}
                        </>
                      }
                      sx={{ pr: session.is_current ? 0 : 10 }}
                    />
                  </ListItem>
                </Box>
              ))}
            </List>
          )}

          <Divider sx={{ mb: 2 }} />

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t("revokeDevicesHelp")}
          </Typography>
          <Button variant="outlined" color="warning" disabled={revoking} onClick={onRevokeAllDevices} sx={{ minHeight: 44 }}>
            {revoking ? <CircularProgress size={20} color="inherit" /> : t("revokeDevices")}
          </Button>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={!!revokeSessionTarget}
        title={t("devicesRevokeConfirmTitle")}
        text={t("devicesRevokeConfirmText", { device: revokeSessionTarget?.device_label || t("devicesUnknownDevice") })}
        confirmLabel={t("devicesSignOut")}
        onClose={() => setRevokeSessionTarget(null)}
        onConfirm={handleRevokeSession}
      />

      <NotificationPreferences />

      {/* ── Delete my account ── */}
      <Card sx={{ mt: 3, border: "1px solid", borderColor: "error.light" }}>
        <CardContent>
          <Typography variant="h6" color="error" gutterBottom>{t("delete_account")}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>{t("delete_account_help")}</Typography>
          <Button
            variant="outlined"
            color="error"
            onClick={() => {
              setDeleteOpen(true);
              setDeleteError(null);
              setBalanceOwed(null);
              setDeleteCode("");
              setDeleteCodeSent(false);
            }}
            sx={{ minHeight: 44 }}
          >
            {t("delete_account")}
          </Button>
        </CardContent>
      </Card>
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>{t("delete_account_confirm_title")}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {deleteError && <Alert severity="error">{deleteError}</Alert>}
            {balanceOwed !== null && (
              <Alert severity="warning">{t("delete_account_balance", { amount: balanceOwed })}</Alert>
            )}
            <Typography variant="body2">{t("delete_account_confirm_text")}</Typography>
            {!deleteCodeSent ? (
              <Button variant="outlined" onClick={handleSendDeleteCode} disabled={sendingDeleteCode}>
                {sendingDeleteCode ? <CircularProgress size={20} /> : t("delete_account_send_code")}
              </Button>
            ) : (
              <>
                <Alert severity="success">{t("delete_account_code_sent")}</Alert>
                <TextField
                  label={t("delete_account_code_label")}
                  value={deleteCode}
                  onChange={(e) => setDeleteCode(e.target.value.replace(/\D/g, ""))}
                  inputProps={{ maxLength: 6, inputMode: "numeric" }}
                  autoFocus
                />
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setDeleteOpen(false)} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
          <Button color="error" variant="contained" disabled={deleting || !deleteCode} onClick={handleDeleteAccount} sx={{ minHeight: 44 }}>
            {deleting ? <CircularProgress size={22} color="inherit" /> : t("delete_account_confirm")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
    </Box>
    </>
  );
}
