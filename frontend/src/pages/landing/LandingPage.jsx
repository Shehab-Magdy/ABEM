import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";
import { Box, Button, Container, Grid, Stack, Typography } from "@mui/material";
import {
  AccountBalance,
  BarChart,
  Groups,
  Receipt,
  Repeat,
  Security,
} from "@mui/icons-material";
import { PublicSEO } from "../../components/seo/SEO";

const structuredData = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "ABEM",
  "alternateName": "Apartment & Building Expense Management",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web",
  "description":
    "Multi-tenant platform for managing shared building expenses, payments, and balances for property managers and apartment owners.",
  "url": "https://abem.app",
  "inLanguage": ["ar", "en"],
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "EGP",
    "description": "Free to get started",
  },
  "featureList": [
    "Expense splitting across apartments and stores",
    "Payment tracking with PDF receipts",
    "Role-based access control",
    "Multi-building management",
    "Recurring expense automation",
  ],
};

export default function LandingPage() {
  const { t } = useTranslation("common");

  const features = [
    { icon: <AccountBalance fontSize="large" color="primary" />, title: t("feature_multi_building", "Multi-Building Management"), text: t("feature_multi_building_desc", "Manage multiple buildings, apartments, and stores from a single dashboard.") },
    { icon: <Receipt fontSize="large" color="primary" />, title: t("feature_splitting", "Expense Splitting"), text: t("feature_splitting_desc", "Automatically split shared expenses across apartments and stores with configurable rules.") },
    { icon: <BarChart fontSize="large" color="primary" />, title: t("feature_tracking", "Payment Tracking"), text: t("feature_tracking_desc", "Record payments, generate PDF receipts, and track outstanding balances in real time.") },
    { icon: <Repeat fontSize="large" color="primary" />, title: t("feature_recurring", "Recurring Expenses"), text: t("feature_recurring_desc", "Set up recurring expenses that are automatically generated on schedule.") },
    { icon: <Security fontSize="large" color="primary" />, title: t("feature_rbac", "Role-Based Access"), text: t("feature_rbac_desc", "Admins manage everything. Owners see only their own data. Full audit trail included.") },
    { icon: <Groups fontSize="large" color="primary" />, title: t("feature_egypt", "Built for Egypt"), text: t("feature_egypt_desc", "Designed for Egyptian property managers and apartment owners, with local currency support.") },
  ];

  return (
    <>
      <PublicSEO
        title="ABEM – Apartment & Building Expense Management"
        description="Manage shared building expenses, payments, and balances with ease. Built for property managers and apartment owners in Egypt."
      >
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      </PublicSEO>

      {/* Hero */}
      <Box
        sx={{
          bgcolor: "primary.main",
          color: "white",
          py: { xs: 8, md: 12 },
          textAlign: "center",
        }}
      >
        <Container maxWidth="md">
          <Box
            component="img"
            src="/abem-logo-dark.svg"
            alt="ABEM — Apartment & Building Expense Management"
            width={180}
            height={48}
            loading="eager"
            sx={{ mb: 3 }}
          />
          <Typography variant="h3" fontWeight={700} gutterBottom>
            {t("hero_title", "Building Expense Management Made Simple")}
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9, mb: 4 }}>
            {t("hero_subtitle", "Track shared expenses, split costs fairly, record payments, and keep every apartment owner in the loop — all from one platform.")}
          </Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2} justifyContent="center">
            <Button
              component={RouterLink}
              to="/register"
              variant="contained"
              size="large"
              sx={{ bgcolor: "white", color: "primary.main", "&:hover": { bgcolor: "grey.100" } }}
            >
              {t("get_started_free", "Get Started Free")}
            </Button>
            <Button
              component={RouterLink}
              to="/login"
              variant="outlined"
              size="large"
              sx={{ borderColor: "white", color: "white", "&:hover": { borderColor: "grey.200" } }}
            >
              {t("sign_in", "Sign In")}
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* Features */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 10 } }}>
        <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
          {t("features_title", "Everything You Need")}
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 6, maxWidth: 600, mx: "auto" }}>
          {t("features_desc", "ABEM gives property managers and apartment owners the tools to manage shared building expenses transparently.")}
        </Typography>

        <Grid container spacing={4}>
          {features.map((f) => (
            <Grid item xs={12} sm={6} md={4} key={f.title}>
              <Stack spacing={1.5} sx={{ p: 3, borderRadius: 2, height: "100%" }}>
                {f.icon}
                <Typography variant="h6" fontWeight={600}>{f.title}</Typography>
                <Typography variant="body2" color="text.secondary">{f.text}</Typography>
              </Stack>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA */}
      <Box sx={{ bgcolor: "background.paper", py: 8, textAlign: "center" }}>
        <Container maxWidth="sm">
          <Typography variant="h5" fontWeight={700} gutterBottom>
            {t("cta_title", "Ready to simplify your building's finances?")}
          </Typography>
          <Button component={RouterLink} to="/register" variant="contained" size="large" sx={{ mt: 2 }}>
            {t("create_free_account", "Create Your Free Account")}
          </Button>
        </Container>
      </Box>
    </>
  );
}
