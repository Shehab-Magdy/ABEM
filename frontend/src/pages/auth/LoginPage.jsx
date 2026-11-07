import { useNavigate, useSearchParams, Link as RouterLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Card, CardContent, Link, Stack, Typography } from "@mui/material";
import { useAuthStore } from "../../contexts/authStore";
import { PublicSEO } from "../../components/seo/SEO";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import BrandLogo from "../../components/common/BrandLogo";
import OtpLoginForm from "../../components/auth/OtpLoginForm";

export default function LoginPage() {
  const { t, i18n } = useTranslation("auth");
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [searchParams] = useSearchParams();

  const handleSuccess = (user, accessToken) => {
    login(user, accessToken);
    if (user.preferred_language) {
      i18n.changeLanguage(user.preferred_language);
    }
    const next = searchParams.get("next");
    // only follow same-site relative paths (blocks open redirects like //evil.com)
    const safeNext = next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";
    navigate(safeNext, { replace: true });
  };

  return (
    <>
    <PublicSEO
      title="Login – 3maracom"
      description="Sign in to your 3maracom account to manage your building's shared expenses and payments."
    />
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      px={2}
      position="relative"
      sx={{
        backgroundImage: 'url(/abem-hero-banner.svg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        bgcolor: 'background.default',
      }}
    >
      {/* Language switcher — top-right corner */}
      <Box sx={{ position: "absolute", top: 16, right: 16 }}>
        <LanguageSwitcher />
      </Box>

      <Card sx={{ width: "100%", maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Stack alignItems="center" spacing={1} mb={4}>
            <BrandLogo size={44} />
            <Typography variant="body2" color="text.secondary">
              {t("apartment_building_expense")}
            </Typography>
          </Stack>

          <OtpLoginForm initialEmail={searchParams.get("email") || undefined} onSuccess={handleSuccess} />

          <Typography variant="body2" align="center" color="text.secondary" sx={{ mt: 2.5 }}>
            {t("dont_have_account")}{" "}
            <Link component={RouterLink} to="/register" underline="hover">
              {t("create_account")}
            </Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
    </>
  );
}
