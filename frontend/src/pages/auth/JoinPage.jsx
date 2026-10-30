import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Alert, Box, Button, Card, CardContent, CircularProgress, Stack, Typography } from "@mui/material";
import { apartmentsApi } from "../../api/apartmentsApi";
import { useAuthStore } from "../../contexts/authStore";
import BrandLogo from "../../components/common/BrandLogo";
import { PrivateSEO } from "../../components/seo/SEO";

/**
 * Landing page for a shareable invite link: /join/:token
 * Shows which building/unit the link is for, then either claims it right away
 * (already signed in) or sends the resident to sign up / sign in and back here.
 */
export default function JoinPage() {
  const { t } = useTranslation("auth");
  const { token } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);

  useEffect(() => {
    apartmentsApi
      .validateInvite(token)
      .then((res) => setInfo(res.data))
      .catch((err) => setError(err.response?.data?.detail || t("join_invalid")))
      .finally(() => setLoading(false));
  }, [token, t]);

  const claim = async () => {
    setClaiming(true);
    setError(null);
    try {
      await apartmentsApi.useInvite(token);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || t("errors:server_error"));
    } finally {
      setClaiming(false);
    }
  };

  const next = encodeURIComponent(`/join/${token}`);

  return (
    <>
      <PrivateSEO title="3maracom" />
      <Box display="flex" alignItems="center" justifyContent="center" minHeight="100vh" px={2} py={4}>
        <Card sx={{ width: "100%", maxWidth: 480 }}>
          <CardContent sx={{ p: 4 }}>
            <Stack alignItems="center" spacing={3}>
              <BrandLogo size={48} />
              {loading ? (
                <CircularProgress />
              ) : error && !info ? (
                <Alert severity="error" sx={{ width: "100%" }}>{error}</Alert>
              ) : (
                <>
                  <Stack alignItems="center" spacing={0.5} textAlign="center">
                    <Typography variant="h6" fontWeight={700}>{t(info.role === "renter" ? "join_title_renter" : "join_title")}</Typography>
                    <Typography>
                      {t("join_unit_in_building", { unit: info.unit_number, building: info.building_name })}
                    </Typography>
                    {info.building_city && (
                      <Typography variant="body2" color="text.secondary">{info.building_city}</Typography>
                    )}
                  </Stack>
                  {error && <Alert severity="error" sx={{ width: "100%" }}>{error}</Alert>}
                  {user ? (
                    <Button variant="contained" size="large" fullWidth disabled={claiming} onClick={claim} sx={{ minHeight: 52 }}>
                      {claiming ? <CircularProgress size={22} color="inherit" /> : t("join_claim")}
                    </Button>
                  ) : (
                    <Stack spacing={1.5} sx={{ width: "100%" }}>
                      <Button component={RouterLink} to={`/register?invite=${token}`} variant="contained" size="large" fullWidth sx={{ minHeight: 52 }}>
                        {t("join_create_account")}
                      </Button>
                      <Button component={RouterLink} to={`/login?next=${next}`} variant="outlined" size="large" fullWidth sx={{ minHeight: 52 }}>
                        {t("join_have_account")}
                      </Button>
                    </Stack>
                  )}
                </>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Box>
    </>
  );
}
