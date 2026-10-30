import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Card, CardContent, Stack, TextField, Typography } from "@mui/material";
import { AttachFile, Email, ExpandMore, WhatsApp } from "@mui/icons-material";
import { BRAND } from "../../brand";
import { supportApi } from "../../api/supportApi";
import { PrivateSEO } from "../../components/seo/SEO";

const QUESTIONS = [1, 2, 3, 4, 5, 6, 7, 8];
const MAX_BYTES = 5 * 1024 * 1024;

/** المساعدة والدعم — FAQ, ways to reach us and a problem report with an optional screenshot. */
export default function HelpPage() {
  const { t } = useTranslation("help");
  const fileInput = useRef(null);
  const [message, setMessage] = useState("");
  const [screenshot, setScreenshot] = useState(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null); // {severity, text}

  const pick = (e) => {
    const file = e.target.files?.[0];
    if (file && file.size > MAX_BYTES) {
      setStatus({ severity: "error", text: t("too_big") });
      e.target.value = "";
      return;
    }
    setScreenshot(file ?? null);
  };

  const send = async () => {
    setBusy(true);
    setStatus(null);
    try {
      await supportApi.report({ message, screenshot });
      setMessage("");
      setScreenshot(null);
      setStatus({ severity: "success", text: t("sent") });
    } catch {
      setStatus({ severity: "error", text: t("send_error") });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PrivateSEO title="3maracom – Help" />
      <Box sx={{ p: { xs: 2, sm: 3 }, maxWidth: 800 }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>{t("title")}</Typography>

        <Typography variant="subtitle1" fontWeight={700} sx={{ mt: 2, mb: 1 }}>{t("faq_title")}</Typography>
        {QUESTIONS.map((n) => (
          <Accordion key={n} disableGutters variant="outlined">
            <AccordionSummary expandIcon={<ExpandMore />}><Typography fontWeight={600}>{t(`q${n}`)}</Typography></AccordionSummary>
            <AccordionDetails><Typography color="text.secondary">{t(`a${n}`)}</Typography></AccordionDetails>
          </Accordion>
        ))}

        <Typography variant="subtitle1" fontWeight={700} sx={{ mt: 3 }}>{t("contact_title")}</Typography>
        <Typography color="text.secondary" sx={{ mb: 1 }}>{t("contact_help")}</Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {BRAND.supportEmail && (
            <Button variant="outlined" startIcon={<Email />} href={`mailto:${BRAND.supportEmail}`} sx={{ minHeight: 44 }}>{t("email")}</Button>
          )}
          {BRAND.supportWhatsapp && (
            <Button variant="outlined" color="success" startIcon={<WhatsApp />} href={`https://wa.me/${BRAND.supportWhatsapp}`} target="_blank" rel="noopener noreferrer" sx={{ minHeight: 44 }}>
              {t("whatsapp")}
            </Button>
          )}
        </Stack>

        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700}>{t("report_title")}</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>{t("report_help")}</Typography>
            <Stack spacing={2}>
              {status && <Alert severity={status.severity}>{status.text}</Alert>}
              <TextField label={t("message")} value={message} onChange={(e) => setMessage(e.target.value)} multiline minRows={3} />
              <input ref={fileInput} type="file" accept="image/*" hidden onChange={pick} data-testid="screenshot-input" />
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                <Button startIcon={<AttachFile />} onClick={() => fileInput.current?.click()} sx={{ minHeight: 44 }}>{t("screenshot")}</Button>
                {screenshot && (
                  <>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 220 }}>{screenshot.name}</Typography>
                    <Button size="small" onClick={() => { setScreenshot(null); if (fileInput.current) fileInput.current.value = ""; }}>{t("remove")}</Button>
                  </>
                )}
              </Stack>
              <Box><Button variant="contained" onClick={send} disabled={busy || message.trim().length < 5} sx={{ minHeight: 44 }}>{t("send")}</Button></Box>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    </>
  );
}
