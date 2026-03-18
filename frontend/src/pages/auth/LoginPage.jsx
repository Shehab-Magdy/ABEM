import { useState } from "react";
import { useNavigate, Link as RouterLink, useSearchParams } from "react-router-dom";
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
import { PublicSEO } from "../../components/seo/SEO";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [searchParams] = useSearchParams();

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [errorCode, setErrorCode] = useState(null);
  const [lockoutUntil, setLockoutUntil] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm({ defaultValues: { email: searchParams.get("email") || "" } });

  const onSubmit = async (data) => {
    setError(null);
    setErrorCode(null);
    setLockoutUntil(null);
    setIsLoading(true);
    try {
      const response = await authApi.login(data);
      const { access, refresh, user } = response.data;
      login(user, access, refresh);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const httpStatus = err.response?.status;
      const resData = err.response?.data;
      const code = resData?.code || null;
      const detail =
        resData?.detail ||
        resData?.non_field_errors?.[0] ||
        resData?.email?.[0] ||
        resData?.password?.[0] ||
        (httpStatus === 401 ? "Invalid email or password." : "An unexpected error occurred.");

      if (httpStatus === 423) {
        setLockoutUntil(err.response.data.locked_until);
      } else {
        setErrorCode(code);
        setError(detail);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
    <PublicSEO
      title="Login – ABEM"
      description="Sign in to your ABEM account to manage your building's shared expenses and payments."
    />
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
          {/* Header */}
          <Stack alignItems="center" spacing={1} mb={4}>
            <Box component="img" src="/abem-logo-light.svg" alt="ABEM" sx={{ height: 48 }} />
            <Typography variant="body2" color="text.secondary">
              Apartment & Building Expense Management
            </Typography>
          </Stack>

          {/* Lockout alert */}
          {lockoutUntil && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Account locked. Too many failed attempts.
              <br />
              Try again after{" "}
              <strong>{new Date(lockoutUntil).toLocaleTimeString()}</strong>.
            </Alert>
          )}

          {/* Generic error */}
          {error && !lockoutUntil && (
            <Alert
              severity="error"
              sx={{ mb: 2 }}
              action={
                errorCode === "email_not_found" ? (
                  <Button
                    color="inherit"
                    size="small"
                    component={RouterLink}
                    to={`/register?email=${encodeURIComponent(getValues("email"))}`}
                  >
                    Create account
                  </Button>
                ) : undefined
              }
            >
              {error}
            </Alert>
          )}

          {/* Form */}
          <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
            <Stack spacing={2.5}>
              <TextField
                label="Email address"
                type="email"
                fullWidth
                autoComplete="email"
                autoFocus
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
                label="Password"
                type={showPassword ? "text" : "password"}
                fullWidth
                autoComplete="current-password"
                error={!!errors.password}
                helperText={errors.password?.message}
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
                {...register("password", { required: "Password is required." })}
              />

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={isLoading}
                sx={{ mt: 1 }}
              >
                {isLoading ? <CircularProgress size={24} color="inherit" /> : "Sign in"}
              </Button>

              <Typography variant="body2" align="center" color="text.secondary">
                Don&apos;t have an account?{" "}
                <Link component={RouterLink} to="/register" underline="hover">
                  Create account
                </Link>
              </Typography>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
    </>
  );
}
