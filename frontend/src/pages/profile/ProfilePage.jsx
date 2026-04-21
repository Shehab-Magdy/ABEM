import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useForm, Controller } from "react-hook-form";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  FormControl,
  IconButton,
  InputLabel,
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
import PhoneInput from "../../components/PhoneInput";
import ThemeSwitcher from "../../components/ThemeSwitcher";

export default function ProfilePage() {
  const { t, i18n } = useTranslation("profile");
  const { user, setUser } = useAuth();
  const storeSetUser = useAuthStore((s) => s.setUser);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [pwSuccess, setPwSuccess] = useState(false);
  const [pwError, setPwError] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPw, setSavingPw] = useState(false);
  const [uploadingPic, setUploadingPic] = useState(false);
  const [picError, setPicError] = useState(null);
  const [langSaving, setLangSaving] = useState(false);
  const [langSuccess, setLangSuccess] = useState(false);
  const [themeSaving, setThemeSaving] = useState(false);
  const [themeSuccess, setThemeSuccess] = useState(false);
  const fileInputRef = useRef(null);

  const profileForm = useForm({ defaultValues: { first_name: user?.first_name, last_name: user?.last_name, phone: user?.phone } });
  const pwForm = useForm();

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

  // ── Change password ─────────────────────────────────────────────────────────
  const onChangePassword = async (data) => {
    setSavingPw(true);
    setPwError(null);
    setPwSuccess(false);
    try {
      await authApi.changePassword(data);
      setPwSuccess(true);
      pwForm.reset();
    } catch (err) {
      const detail = err.response?.data?.detail || err.response?.data;
      setPwError(typeof detail === "string" ? detail : "Failed to change password.");
    } finally {
      setSavingPw(false);
    }
  };

  // ── Theme preference ─────────────────────────────────────────────────────

  const handleThemeChange = async (e) => {
    const newTheme = e.target.value;
    setThemeSaving(true);
    try {
      const res = await authApi.updateProfile({ theme_preference: newTheme });
      storeSetUser(res.data);
      setThemeSuccess(true);
    } catch {
      // Revert on failure
    } finally {
      setThemeSaving(false);
    }
  };

  return (
    <>
      <PrivateSEO title="ABEM – Profile" />
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
      <Snackbar
        open={themeSuccess}
        autoHideDuration={3000}
        onClose={() => setThemeSuccess(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="success" onClose={() => setThemeSuccess(false)}>
          {t("theme_updated", "Theme updated")}
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

      {/* Theme Preference */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1} mb={2}>
            <ThemeSwitcher />
            <Typography variant="h6">{t("theme_preference", "Theme Preference")}</Typography>
          </Stack>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>{t("theme")}</InputLabel>
            <Select
              value={user?.theme_preference || 'light'}
              label={t("theme")}
              onChange={handleThemeChange}
              disabled={themeSaving}
            >
              <MenuItem value="light">☀️ {t("light")}</MenuItem>
              <MenuItem value="dark">🌙 {t("dark")}</MenuItem>
            </Select>
          </FormControl>
        </CardContent>
      </Card>

      {/* Change password */}
      <Card>
        <CardContent>
          <Typography variant="h6" mb={2}>{t("changePassword")}</Typography>
          {pwSuccess && <Alert severity="success" sx={{ mb: 2 }}>{t("passwordChangedSuccess")}</Alert>}
          {pwError && <Alert severity="error" sx={{ mb: 2 }}>{pwError}</Alert>}
          <Box component="form" onSubmit={pwForm.handleSubmit(onChangePassword)}>
            <Stack spacing={2.5}>
              <TextField
                label={t("currentPassword")}
                type="password"
                fullWidth
                error={!!pwForm.formState.errors.current_password}
                helperText={pwForm.formState.errors.current_password?.message}
                {...pwForm.register("current_password", { required: "Required." })}
              />
              <TextField
                label={t("newPassword")}
                type="password"
                fullWidth
                error={!!pwForm.formState.errors.new_password}
                helperText={pwForm.formState.errors.new_password?.message}
                {...pwForm.register("new_password", { required: "Required.", minLength: { value: 8, message: t("min_8_chars", "Min 8 characters.") } })}
              />
              <TextField
                label={t("confirmNewPassword")}
                type="password"
                fullWidth
                error={!!pwForm.formState.errors.confirm_password}
                helperText={pwForm.formState.errors.confirm_password?.message}
                {...pwForm.register("confirm_password", {
                  required: "Required.",
                  validate: (val) => val === pwForm.watch("new_password") || "Passwords do not match.",
                })}
              />
              <Button type="submit" variant="contained" color="warning" disabled={savingPw} sx={{ alignSelf: "flex-start" }}>
                {savingPw ? <CircularProgress size={20} color="inherit" /> : t("changePassword")}
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
    </Box>
    </>
  );
}
