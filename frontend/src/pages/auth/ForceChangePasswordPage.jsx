import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../contexts/authStore";
import { PrivateSEO } from "../../components/seo/SEO";

export default function ForceChangePasswordPage() {
  const navigate = useNavigate();
  const { setUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm();

  const onSubmit = async (data) => {
    setError(null);
    setIsLoading(true);
    try {
      const res = await authApi.forceChangePassword({
        new_password: data.new_password,
        confirm_password: data.confirm_password,
      });
      setUser(res.data.user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const resData = err.response?.data;
      const detail =
        resData?.detail ||
        resData?.new_password?.[0] ||
        resData?.confirm_password?.[0] ||
        "Failed to change password. Please try again.";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <PrivateSEO title="ABEM – Change Password" />
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        bgcolor="background.default"
        px={2}
      >
        <Card sx={{ width: "100%", maxWidth: 420 }}>
          <CardContent sx={{ p: 4 }}>
            <Stack alignItems="center" spacing={1} mb={3}>
              <Box component="img" src="/abem-logo-light.svg" alt="ABEM" sx={{ height: 48 }} />
              <Typography variant="h6" fontWeight={600}>
                Password Change Required
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                Your password was reset by an administrator. Please create a new password to continue.
              </Typography>
            </Stack>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
              <Stack spacing={2.5}>
                <TextField
                  label="New password"
                  type={showPassword ? "text" : "password"}
                  fullWidth
                  autoFocus
                  autoComplete="new-password"
                  error={!!errors.new_password}
                  helperText={
                    errors.new_password?.message ||
                    "Min 8 chars, 1 uppercase, 1 digit, 1 special char."
                  }
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword((prev) => !prev)}
                          edge="end"
                          tabIndex={-1}
                          aria-label={showPassword ? "Hide password" : "Show password"}
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  {...register("new_password", {
                    required: "New password is required.",
                    minLength: { value: 8, message: "Min 8 characters." },
                  })}
                />

                <TextField
                  label="Confirm new password"
                  type={showPassword ? "text" : "password"}
                  fullWidth
                  autoComplete="new-password"
                  error={!!errors.confirm_password}
                  helperText={errors.confirm_password?.message}
                  {...register("confirm_password", {
                    required: "Please confirm your new password.",
                    validate: (val) =>
                      val === watch("new_password") || "Passwords do not match.",
                  })}
                />

                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    "Set New Password"
                  )}
                </Button>
              </Stack>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </>
  );
}
