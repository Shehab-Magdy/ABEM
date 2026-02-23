import { useState } from "react";
import { useForm } from "react-hook-form";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { authApi } from "../../api/authApi";
import { useAuth } from "../../hooks/useAuth";

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [pwSuccess, setPwSuccess] = useState(false);
  const [pwError, setPwError] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPw, setSavingPw] = useState(false);

  const profileForm = useForm({ defaultValues: { first_name: user?.first_name, last_name: user?.last_name, phone: user?.phone } });
  const pwForm = useForm();

  // ── Update profile ──────────────────────────────────────────────────────────
  const onSaveProfile = async (data) => {
    setSavingProfile(true);
    setProfileError(null);
    setProfileSuccess(false);
    try {
      const res = await authApi.updateProfile(data);
      setUser(res.data);
      setProfileSuccess(true);
    } catch {
      setProfileError("Failed to update profile. Please try again.");
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

  return (
    <Box maxWidth={640}>
      <Typography variant="h5" mb={3}>My Profile</Typography>

      {/* Profile details */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Personal Information</Typography>
          {profileSuccess && <Alert severity="success" sx={{ mb: 2 }}>Profile updated successfully.</Alert>}
          {profileError && <Alert severity="error" sx={{ mb: 2 }}>{profileError}</Alert>}
          <Box component="form" onSubmit={profileForm.handleSubmit(onSaveProfile)}>
            <Stack spacing={2.5}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label="First name"
                  fullWidth
                  error={!!profileForm.formState.errors.first_name}
                  helperText={profileForm.formState.errors.first_name?.message}
                  {...profileForm.register("first_name", { required: "Required." })}
                />
                <TextField
                  label="Last name"
                  fullWidth
                  error={!!profileForm.formState.errors.last_name}
                  helperText={profileForm.formState.errors.last_name?.message}
                  {...profileForm.register("last_name", { required: "Required." })}
                />
              </Stack>
              <TextField label="Phone number" fullWidth {...profileForm.register("phone")} />
              <TextField label="Email" fullWidth disabled value={user?.email || ""} />
              <Button type="submit" variant="contained" disabled={savingProfile} sx={{ alignSelf: "flex-start" }}>
                {savingProfile ? <CircularProgress size={20} color="inherit" /> : "Save Changes"}
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>

      {/* Change password */}
      <Card>
        <CardContent>
          <Typography variant="h6" mb={2}>Change Password</Typography>
          {pwSuccess && <Alert severity="success" sx={{ mb: 2 }}>Password changed successfully.</Alert>}
          {pwError && <Alert severity="error" sx={{ mb: 2 }}>{pwError}</Alert>}
          <Box component="form" onSubmit={pwForm.handleSubmit(onChangePassword)}>
            <Stack spacing={2.5}>
              <TextField
                label="Current password"
                type="password"
                fullWidth
                error={!!pwForm.formState.errors.current_password}
                helperText={pwForm.formState.errors.current_password?.message}
                {...pwForm.register("current_password", { required: "Required." })}
              />
              <TextField
                label="New password"
                type="password"
                fullWidth
                error={!!pwForm.formState.errors.new_password}
                helperText={pwForm.formState.errors.new_password?.message}
                {...pwForm.register("new_password", { required: "Required.", minLength: { value: 8, message: "Min 8 characters." } })}
              />
              <TextField
                label="Confirm new password"
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
                {savingPw ? <CircularProgress size={20} color="inherit" /> : "Change Password"}
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
