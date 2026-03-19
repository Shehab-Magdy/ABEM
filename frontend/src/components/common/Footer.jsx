/**
 * App footer — shown at the bottom of the DashboardLayout content area.
 * Contains navigation links, product info, and copyright.
 */
import { Box, Container, Divider, Grid, Link, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function Footer() {
  const { t } = useTranslation("common");
  const year = new Date().getFullYear();

  return (
    <Box
      component="footer"
      sx={{
        bgcolor: "background.paper",
        borderTop: "1px solid",
        borderColor: "divider",
        mt: "auto",
        py: 4,
        px: 3,
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          {/* Brand */}
          <Grid item xs={12} sm={6} md={3}>
            <Box component="img" src="/abem-logo-light.svg" alt="ABEM" sx={{ height: 32, mb: 1 }} />
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 220 }}>
              {t("footer_tagline", "Apartment & Building Expense Management")}
            </Typography>
          </Grid>

          {/* Product */}
          <Grid item xs={6} sm={3} md={2}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              {t("footer_product", "Product")}
            </Typography>
            <Stack spacing={0.75}>
              <Link component={RouterLink} to="/dashboard" variant="body2" color="text.secondary" underline="hover">
                {t("dashboard")}
              </Link>
              <Link component={RouterLink} to="/buildings" variant="body2" color="text.secondary" underline="hover">
                {t("buildings")}
              </Link>
              <Link component={RouterLink} to="/expenses" variant="body2" color="text.secondary" underline="hover">
                {t("expenses")}
              </Link>
              <Link component={RouterLink} to="/payments" variant="body2" color="text.secondary" underline="hover">
                {t("payments")}
              </Link>
            </Stack>
          </Grid>

          {/* Management */}
          <Grid item xs={6} sm={3} md={2}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              {t("footer_management", "Management")}
            </Typography>
            <Stack spacing={0.75}>
              <Link component={RouterLink} to="/users" variant="body2" color="text.secondary" underline="hover">
                {t("users")}
              </Link>
              <Link component={RouterLink} to="/assets" variant="body2" color="text.secondary" underline="hover">
                {t("assets")}
              </Link>
              <Link component={RouterLink} to="/expense-categories" variant="body2" color="text.secondary" underline="hover">
                {t("categories")}
              </Link>
              <Link component={RouterLink} to="/audit" variant="body2" color="text.secondary" underline="hover">
                {t("footer_audit", "Audit Log")}
              </Link>
            </Stack>
          </Grid>

          {/* Account */}
          <Grid item xs={6} sm={3} md={2}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              {t("account_section")}
            </Typography>
            <Stack spacing={0.75}>
              <Link component={RouterLink} to="/profile" variant="body2" color="text.secondary" underline="hover">
                {t("profile")}
              </Link>
              <Link component={RouterLink} to="/notifications" variant="body2" color="text.secondary" underline="hover">
                {t("notifications")}
              </Link>
            </Stack>
          </Grid>

          {/* Coming Soon */}
          <Grid item xs={6} sm={3} md={3}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              {t("footer_coming_soon", "Coming Soon")}
            </Typography>
            <Stack spacing={0.75}>
              <Typography variant="body2" color="text.disabled">
                {t("footer_mobile_app", "Mobile App (iOS & Android)")}
              </Typography>
              <Typography variant="body2" color="text.disabled">
                {t("footer_reports", "Advanced Reports")}
              </Typography>
              <Typography variant="body2" color="text.disabled">
                {t("footer_integrations", "Payment Gateway Integration")}
              </Typography>
              <Typography variant="body2" color="text.disabled">
                {t("footer_multi_currency", "Multi-Currency Support")}
              </Typography>
            </Stack>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* Copyright */}
        <Stack
          direction={{ xs: "column", sm: "row" }}
          justifyContent="space-between"
          alignItems={{ xs: "center", sm: "flex-start" }}
          spacing={1}
        >
          <Typography variant="caption" color="text.secondary">
            © {year} ABEM — {t("footer_rights", "All rights reserved.")}
          </Typography>
          <Stack direction="row" spacing={2}>
            <Typography variant="caption" color="text.disabled">
              {t("footer_privacy", "Privacy Policy")}
            </Typography>
            <Typography variant="caption" color="text.disabled">
              {t("footer_terms", "Terms of Service")}
            </Typography>
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
}
