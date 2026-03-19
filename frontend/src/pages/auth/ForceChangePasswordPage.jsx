import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
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
import LanguageSwitcher from "../../components/LanguageSwitcher";

export default function ForceChangePasswordPage() {
  const { t } = useTranslation("auth");
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
        t("errors:server_error", "Failed to change password.");
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
        position="relative"
      >
        <Box sx={{ position: "absolute", top: 16, right: 16 }}>
          <LanguageSwitcher />
        </Box>
        <Card sx={{ width: "100%", maxWidth: 420 }}>
          <CardContent sx={{ p: 4 }}>
            <Stack alignItems="center" spacing={1} mb={3}>
              <Box component="img" src="/abem-logo-light.svg" alt="ABEM" sx={{ height: 48 }} />
              <Typography variant="h6" fontWeight={600}>
                {t("password_change_required")}
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                {t("password_change_required_desc")}
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
                  label={t("new_password")}
                  type={showPassword ? "text" : "password"}
                  fullWidth
                  autoFocus
                  autoComplete="new-password"
                  error={!!errors.new_password}
                  helperText={
                    errors.new_password?.message ||
                    t("password_min_length")
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
                    required: t("password_required"),
                    minLength: { value: 8, message: t("password_min_length") },
                  })}
                />

                <TextField
                  label={t("confirm_new_password")}
                  type={showPassword ? "text" : "password"}
                  fullWidth
                  autoComplete="new-password"
                  error={!!errors.confirm_password}
                  helperText={errors.confirm_password?.message}
                  {...register("confirm_password", {
                    required: t("password_required"),
                    validate: (val) =>
                      val === watch("new_password") || t("passwords_dont_match"),
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
                    t("set_new_password")
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
