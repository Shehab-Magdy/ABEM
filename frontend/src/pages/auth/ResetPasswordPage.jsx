import { useState } from "react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Alert, Box, Button, Card, CardContent, CircularProgress, Link, Stack, TextField, Typography } from "@mui/material";
import { authApi } from "../../api/authApi";
import { PublicSEO } from "../../components/seo/SEO";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import BrandLogo from "../../components/common/BrandLogo";

/** Landing page for the emailed reset link: /reset-password?uid=...&token=... */
export default function ResetPasswordPage() {
  const { t } = useTranslation("auth");
  const [params] = useSearchParams();
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm();

  const onSubmit = async (data) => {
    setLoading(true);
    setError(null);
    try {
      await authApi.resetPassword({
        uid: params.get("uid"),
        token: params.get("token"),
        password: data.password,
        confirm_password: data.confirm_password,
      });
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.detail || t("errors:server_error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PublicSEO title="Reset Password – 3maracom" description="Choose a new password for your 3maracom account." />
      <Box display="flex" alignItems="center" justifyContent="center" minHeight="100vh" bgcolor="background.default" px={2} position="relative">
        <Box sx={{ position: "absolute", top: 16, right: 16 }}>
          <LanguageSwitcher />
        </Box>
        <Card sx={{ width: "100%", maxWidth: 420 }}>
          <CardContent sx={{ p: 4 }}>
            <Stack alignItems="center" spacing={1} mb={3}>
              <BrandLogo size={44} />
              <Typography variant="h6" fontWeight={600}>{t("new_password_title")}</Typography>
            </Stack>
            {done ? (
              <Stack spacing={2}>
                <Alert severity="success">{t("password_reset_done")}</Alert>
                <Button component={RouterLink} to="/login" variant="contained" size="large" fullWidth>{t("sign_in")}</Button>
              </Stack>
            ) : (
              <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
                <Stack spacing={2.5}>
                  {error && <Alert severity="error">{error}</Alert>}
                  <TextField
                    label={t("new_password")}
                    type="password"
                    fullWidth
                    autoComplete="new-password"
                    error={!!errors.password}
                    helperText={errors.password?.message}
                    {...register("password", { required: t("password_required") })}
                  />
                  <TextField
                    label={t("confirm_password")}
                    type="password"
                    fullWidth
                    autoComplete="new-password"
                    error={!!errors.confirm_password}
                    helperText={errors.confirm_password?.message}
                    {...register("confirm_password", {
                      validate: (v) => v === watch("password") || t("passwords_do_not_match"),
                    })}
                  />
                  <Button type="submit" variant="contained" size="large" fullWidth disabled={loading}>
                    {loading ? <CircularProgress size={24} color="inherit" /> : t("save_new_password")}
                  </Button>
                </Stack>
              </Box>
            )}
            <Typography variant="body2" align="center" color="text.secondary" sx={{ mt: 3 }}>
              <Link component={RouterLink} to="/forgot-password" underline="hover">{t("request_new_link")}</Link>
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </>
  );
}
