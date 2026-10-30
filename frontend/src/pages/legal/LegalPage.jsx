import { Link as RouterLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Alert, Box, Button, Container, Stack, Typography } from "@mui/material";
import { PublicSEO } from "../../components/seo/SEO";
import BrandLogo from "../../components/common/BrandLogo";
import { BRAND } from "../../brand";

/** Privacy Policy and Terms of Service. `doc` is "privacy" or "terms"; the text lives in the legal.json locale files. */
export default function LegalPage({ doc }) {
  const { t } = useTranslation("legal");
  const sections = t(`${doc}_sections`, { returnObjects: true });
  const list = Array.isArray(sections) ? sections : [];

  return (
    <>
      <PublicSEO title={`${t(`${doc}_title`)} – 3maracom`} description={t(`${doc}_intro`)} />
      <Container maxWidth="md" sx={{ py: { xs: 3, md: 6 } }}>
        <Stack spacing={3}>
          <Box component={RouterLink} to="/" sx={{ textDecoration: "none" }}>
            <BrandLogo size={40} />
          </Box>
          <Typography variant="h4" fontWeight={800}>{t(`${doc}_title`)}</Typography>
          {BRAND.legalDraft && <Alert severity="warning">{t("draft_notice")}</Alert>}
          <Typography color="text.secondary">{t(`${doc}_intro`)}</Typography>
          {list.map((s) => (
            <Box key={s.h}>
              <Typography variant="h6" fontWeight={700} gutterBottom>{s.h}</Typography>
              <Typography sx={{ whiteSpace: "pre-line" }}>{s.p}</Typography>
            </Box>
          ))}
          {BRAND.supportEmail && (
            <Typography>{t("contact")}: <a href={`mailto:${BRAND.supportEmail}`}>{BRAND.supportEmail}</a></Typography>
          )}
          <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
            <Button component={RouterLink} to={doc === "privacy" ? "/terms" : "/privacy"} variant="outlined">
              {t(doc === "privacy" ? "terms_title" : "privacy_title")}
            </Button>
            <Button component={RouterLink} to="/" variant="text">{t("back_home")}</Button>
          </Stack>
        </Stack>
      </Container>
    </>
  );
}
