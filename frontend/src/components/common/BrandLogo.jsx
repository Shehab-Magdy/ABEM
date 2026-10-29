import { Box, Typography } from "@mui/material";
import { BRAND } from "../../brand";

/**
 * Text wordmark: app icon + "عِمارة.كوم" with "3maracom" beneath.
 * `light` = white text for dark backgrounds (sidebar).
 */
export default function BrandLogo({ light = false, size = 36 }) {
  const color = light ? "#fff" : "text.primary";
  return (
    <Box
      sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}
      aria-label={BRAND.combined}
    >
      <Box component="img" src="/abem-app-icon.svg" alt="" sx={{ height: size, width: size, borderRadius: 1 }} />
      <Box sx={{ lineHeight: 1.1 }}>
        <Typography component="span" fontWeight={700} sx={{ display: "block", color, fontSize: size * 0.5, fontFamily: "Cairo, Inter, sans-serif" }}>
          {BRAND.nameAr}
        </Typography>
        <Typography component="span" sx={{ display: "block", color, opacity: 0.7, fontSize: size * 0.33, letterSpacing: 0.5 }}>
          {BRAND.nameEn}
        </Typography>
      </Box>
    </Box>
  );
}
