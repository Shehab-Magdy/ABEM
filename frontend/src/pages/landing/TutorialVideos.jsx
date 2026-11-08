import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Container, Tab, Tabs, Typography } from "@mui/material";
import { AdminPanelSettings, Home } from "@mui/icons-material";

// Languages a tutorial video exists for. Add "en" here once
// public/videos/tutorial-<role>-en.mp4 is built (see tools/tutorial-video).
const VIDEO_LANGS = ["ar"];

const ROLES = [
  { key: "admin", icon: <AdminPanelSettings /> },
  { key: "owner", icon: <Home /> },
];

/** Two short walkthroughs (building admin / unit owner), shown before login. */
export default function TutorialVideos() {
  const { t, i18n } = useTranslation("common");
  const [role, setRole] = useState("admin");
  const lang = VIDEO_LANGS.includes((i18n.language || "").slice(0, 2)) ? i18n.language.slice(0, 2) : VIDEO_LANGS[0];
  const base = `/videos/tutorial-${role}-${lang}`;

  return (
    <Box id="tutorial-videos" sx={{ bgcolor: "background.paper", py: { xs: 6, md: 8 } }}>
      <Container maxWidth="md">
        <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
          {t("tutorial_videos_title", "See how it works")}
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 3, maxWidth: 600, mx: "auto" }}>
          {t("tutorial_videos_desc", "Two short videos: sign in with a one-time email code, then a quick tour of what you can do.")}
        </Typography>

        <Tabs
          value={role}
          onChange={(_, v) => setRole(v)}
          centered
          sx={{ mb: 3 }}
          aria-label={t("tutorial_videos_title", "See how it works")}
        >
          {ROLES.map((r) => (
            <Tab
              key={r.key}
              value={r.key}
              icon={r.icon}
              iconPosition="start"
              label={t(`tutorial_tab_${r.key}`, r.key)}
              data-testid={`tutorial-tab-${r.key}`}
            />
          ))}
        </Tabs>

        <Box sx={{ borderRadius: 3, overflow: "hidden", boxShadow: 4, bgcolor: "#000", aspectRatio: "16 / 9" }}>
          <video
            key={base}
            controls
            playsInline
            preload="metadata"
            poster={`${base}.jpg`}
            style={{ width: "100%", height: "100%", display: "block" }}
            data-testid="tutorial-video"
          >
            <source src={`${base}.mp4`} type="video/mp4" />
            <track kind="captions" src={`${base}.vtt`} srcLang={lang} label={lang === "ar" ? "العربية" : "English"} />
          </video>
        </Box>
        <Typography variant="body2" align="center" color="text.secondary" sx={{ mt: 2 }}>
          {t(`tutorial_${role}_desc`, "")}
        </Typography>
        {!(i18n.language || "").startsWith("ar") && (
          <Typography variant="caption" align="center" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
            {t("tutorial_lang_note", "The videos are in Arabic with Arabic captions. An English version is coming soon.")}
          </Typography>
        )}
      </Container>
    </Box>
  );
}
