/**
 * App footer — shown at the bottom of the DashboardLayout content area.
 * Contains navigation links, product info, and copyright.
 */
import { Box, Container, Divider, Grid, Link, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import BrandLogo from "./BrandLogo";
import { BRAND } from "../../brand";
import { useAuth } from "../../hooks/useAuth";

const RESIDENT_LINKS = [["/dashboard", "dashboard"], ["/expenses", "expenses"], ["/payments", "payments"]];
const ADMIN_LINKS = [["/dashboard", "dashboard"], ["/buildings", "buildings"], ["/expenses", "expenses"], ["/payments", "payments"]];
const MANAGEMENT_LINKS = [["/users", "users"], ["/assets", "assets"], ["/expense-categories", "categories"]];

export default function Footer() {
  const { t } = useTranslation("common");
  const { isAdmin } = useAuth();
  const year = new Date().getFullYear();
  const productLinks = isAdmin ? ADMIN_LINKS : RESIDENT_LINKS;
  const managementLinks = MANAGEMENT_LINKS;

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
            <BrandLogo size={32} />
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 220 }}>
              {t("footer_tagline", "Apartment & Building Expense Management")}
            </Typography>
          </Grid>

          {/* Product: residents only see what they can open */}
          <Grid item xs={6} sm={3} md={3}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              {t("footer_product", "Product")}
            </Typography>
            <Stack spacing={0.75}>
              {productLinks.map(([to, key]) => (
                <Link key={to} component={RouterLink} to={to} variant="body2" color="text.secondary" underline="hover">
                  {t(key)}
                </Link>
              ))}
            </Stack>
          </Grid>

          {/* Management: admins only */}
          {isAdmin && (
            <Grid item xs={6} sm={3} md={3}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t("footer_management", "Management")}
              </Typography>
              <Stack spacing={0.75}>
                {managementLinks.map(([to, key]) => (
                  <Link key={to} component={RouterLink} to={to} variant="body2" color="text.secondary" underline="hover">
                    {t(key)}
                  </Link>
                ))}
              </Stack>
            </Grid>
          )}

          {/* Account */}
          <Grid item xs={6} sm={3} md={3}>
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
              {BRAND.supportEmail && (
                <Link href={`mailto:${BRAND.supportEmail}`} variant="body2" color="text.secondary" underline="hover">
                  {t("footer_support", "Support")}
                </Link>
              )}
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
            © {year} عِمارة.كوم | 3maracom — {t("footer_rights", "All rights reserved.")}
          </Typography>
          <Stack direction="row" spacing={2}>
            <Link component={RouterLink} to="/privacy" variant="caption" color="text.secondary" underline="hover">
              {t("footer_privacy", "Privacy Policy")}
            </Link>
            <Link component={RouterLink} to="/terms" variant="caption" color="text.secondary" underline="hover">
              {t("footer_terms", "Terms of Service")}
            </Link>
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
}
