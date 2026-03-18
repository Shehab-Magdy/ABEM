import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import { useForm } from "react-hook-form";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Link,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { PublicSEO } from "../../components/seo/SEO";

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const onSubmit = async () => {
    setIsLoading(true);
    // TODO: Wire to backend forgot-password endpoint when available
    await new Promise((r) => setTimeout(r, 1000));
    setIsLoading(false);
    setSubmitted(true);
  };

  return (
    <>
      <PublicSEO
        title="Reset Password – ABEM"
        description="Reset your ABEM account password securely."
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
            <Stack alignItems="center" spacing={1} mb={4}>
              <Box component="img" src="/abem-logo-light.svg" alt="ABEM" sx={{ height: 48 }} />
              <Typography variant="h6" fontWeight={600}>
                Reset your password
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                Enter your email and we&apos;ll send you a link to reset your password.
              </Typography>
            </Stack>

            {submitted ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                If an account with that email exists, you&apos;ll receive a password reset link shortly.
              </Alert>
            ) : (
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
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={isLoading}
                  >
                    {isLoading ? <CircularProgress size={24} color="inherit" /> : "Send Reset Link"}
                  </Button>
                </Stack>
              </Box>
            )}

            <Typography variant="body2" align="center" color="text.secondary" sx={{ mt: 3 }}>
              Remember your password?{" "}
              <Link component={RouterLink} to="/login" underline="hover">
                Sign in
              </Link>
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </>
  );
}
