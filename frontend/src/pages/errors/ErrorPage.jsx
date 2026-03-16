/**
 * Generic full-page error display.
 * Used directly by 404 / 401 / 403 / 500 pages.
 */
import { Box, Button, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function ErrorPage({
  code,
  title,
  description,
  icon,
  primaryAction,       // { label, to?, onClick? }
  secondaryAction,     // optional { label, to?, onClick? }
  accentColor = "#2563EB",
}) {
  const navigate = useNavigate();

  function handleClick(action) {
    if (action.onClick) return action.onClick();
    navigate(action.to ?? "/");
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "#F9FAFB",
        px: 3,
      }}
    >
      <Stack alignItems="center" spacing={3} sx={{ maxWidth: 480, textAlign: "center" }}>
        {/* Big code */}
        <Typography
          component="div"
          sx={{
            fontSize: { xs: 80, sm: 120 },
            fontWeight: 900,
            lineHeight: 1,
            color: accentColor,
            opacity: 0.15,
            letterSpacing: -4,
            userSelect: "none",
          }}
        >
          {code}
        </Typography>

        {/* Icon */}
        <Box
          sx={{
            width: 72,
            height: 72,
            borderRadius: "50%",
            bgcolor: accentColor + "18",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            mt: -8,       // overlap the faded number
            position: "relative",
            zIndex: 1,
          }}
        >
          <Box sx={{ color: accentColor, fontSize: 36, lineHeight: 1 }}>{icon}</Box>
        </Box>

        {/* Text */}
        <Box>
          <Typography variant="h5" fontWeight={700} gutterBottom>
            {title}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {description}
          </Typography>
        </Box>

        {/* Actions */}
        <Stack direction="row" spacing={2} justifyContent="center">
          <Button
            variant="contained"
            size="large"
            sx={{ bgcolor: accentColor, "&:hover": { bgcolor: accentColor } }}
            onClick={() => handleClick(primaryAction)}
          >
            {primaryAction.label}
          </Button>
          {secondaryAction && (
            <Button
              variant="outlined"
              size="large"
              sx={{ borderColor: accentColor, color: accentColor }}
              onClick={() => handleClick(secondaryAction)}
            >
              {secondaryAction.label}
            </Button>
          )}
        </Stack>

        {/* Subtle branding */}
        <Typography variant="caption" color="text.disabled">
          ABEM — Apartment &amp; Building Expense Management
        </Typography>
      </Stack>
    </Box>
  );
}
