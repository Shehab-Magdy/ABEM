import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
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
import LanguageSwitcher from "../../components/LanguageSwitcher";

export default function ForgotPasswordPage() {
  const { t } = useTranslation("auth");
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
        position="relative"
      >
        <Box sx={{ position: "absolute", top: 16, right: 16 }}>
          <LanguageSwitcher />
        </Box>
        <Card sx={{ width: "100%", maxWidth: 420 }}>
          <CardContent sx={{ p: 4 }}>
            <Stack alignItems="center" spacing={1} mb={4}>
              <Box component="img" src="/abem-logo-light.svg" alt="ABEM" sx={{ height: 48 }} />
              <Typography variant="h6" fontWeight={600}>
                {t("reset_password_title")}
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                {t("reset_password_desc")}
              </Typography>
            </Stack>

            {submitted ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                {t("reset_link_sent")}
              </Alert>
            ) : (
              <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
                <Stack spacing={2.5}>
                  <TextField
                    label={t("email_address")}
                    type="email"
                    fullWidth
                    autoComplete="email"
                    autoFocus
                    error={!!errors.email}
                    helperText={errors.email?.message}
                    {...register("email", {
                      required: t("email_required"),
                      pattern: {
                        value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                        message: t("errors:invalid_email"),
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
                    {isLoading ? <CircularProgress size={24} color="inherit" /> : t("send_reset_link")}
                  </Button>
                </Stack>
              </Box>
            )}

            <Typography variant="body2" align="center" color="text.secondary" sx={{ mt: 3 }}>
              {t("remember_password")}{" "}
              <Link component={RouterLink} to="/login" underline="hover">
                {t("sign_in_link")}
              </Link>
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </>
  );
}
