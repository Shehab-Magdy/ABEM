import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Card, CardContent, FormControlLabel, Stack, Switch, Typography } from "@mui/material";
import { authApi } from "../api/authApi";
import { useAuthStore } from "../contexts/authStore";

const KEYS = ["payment_reminders", "expense_updates", "announcements", "email"];

/** Which notifications a person wants. Everything is on until they switch it off; each switch saves at once. */
export default function NotificationPreferences() {
  const { t } = useTranslation("profile");
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [error, setError] = useState(null);
  const prefs = user?.notification_preferences ?? {};

  const toggle = async (key, on) => {
    setError(null);
    const next = { ...prefs, [key]: on };
    try {
      const res = await authApi.updateProfile({ notification_preferences: next });
      setUser(res.data);
    } catch {
      setError(t("prefs_error"));
    }
  };

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>{t("prefs_title")}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{t("prefs_help")}</Typography>
        {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}
        <Stack>
          {KEYS.map((key) => (
            <FormControlLabel
              key={key}
              control={<Switch checked={prefs[key] !== false} onChange={(e) => toggle(key, e.target.checked)} />}
              label={<><Typography component="span" fontWeight={600}>{t(`pref_${key}`)}</Typography><Typography variant="caption" color="text.secondary" display="block">{t(`pref_${key}_help`)}</Typography></>}
              sx={{ py: 0.5 }}
            />
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
