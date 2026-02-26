import { useState } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
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
  Link,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../contexts/authStore";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm();

  const passwordValue = watch("password", "");

  const onSubmit = async (data) => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await authApi.selfRegister({
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        phone: data.phone || "",
        password: data.password,
        confirm_password: data.confirm_password,
      });
      const { access, refresh, user } = response.data;
      login(user, access, refresh);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const detail = err.response?.data;
      if (typeof detail === "object" && detail !== null) {
        const messages = Object.values(detail).flat().join(" ");
        setError(messages || "Registration failed.");
      } else {
        setError(detail || "An unexpected error occurred.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      bgcolor="background.default"
      px={2}
    >
      <Card sx={{ width: "100%", maxWidth: 480 }}>
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Stack alignItems="center" spacing={1} mb={4}>
            <Typography variant="h4" color="primary" fontWeight={700}>
              ABEM
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create your owner account
            </Typography>
          </Stack>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
            <Stack spacing={2.5}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label="First name"
                  fullWidth
                  autoFocus
                  error={!!errors.first_name}
                  helperText={errors.first_name?.message}
                  {...register("first_name", { required: "First name is required." })}
                />
                <TextField
                  label="Last name"
                  fullWidth
                  error={!!errors.last_name}
                  helperText={errors.last_name?.message}
                  {...register("last_name", { required: "Last name is required." })}
                />
              </Stack>

              <TextField
                label="Email address"
                type="email"
                fullWidth
                autoComplete="email"
                error={!!errors.email}
                helperText={errors.email?.message}
                {...register("email", {
                  required: "Email is required.",
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: "Enter a valid email address.",
                  },
                })}
              />

              <TextField
                label="Phone (optional)"
                type="tel"
                fullWidth
                {...register("phone")}
              />

              <TextField
                label="Password"
                type={showPassword ? "text" : "password"}
                fullWidth
                autoComplete="new-password"
                error={!!errors.password}
                helperText={
                  errors.password?.message ||
                  "Min 8 chars, 1 uppercase, 1 digit, 1 special character."
                }
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword((prev) => !prev)}
                        edge="end"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                {...register("password", { required: "Password is required." })}
              />

              <TextField
                label="Confirm password"
                type={showPassword ? "text" : "password"}
                fullWidth
                autoComplete="new-password"
                error={!!errors.confirm_password}
                helperText={errors.confirm_password?.message}
                {...register("confirm_password", {
                  required: "Please confirm your password.",
                  validate: (value) =>
                    value === passwordValue || "Passwords do not match.",
                })}
              />

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={isLoading}
                sx={{ mt: 1 }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  "Create account"
                )}
              </Button>

              <Typography variant="body2" align="center" color="text.secondary">
                Already have an account?{" "}
                <Link component={RouterLink} to="/login" underline="hover">
                  Sign in
                </Link>
              </Typography>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
