import { IconButton, Tooltip } from "@mui/material";
import { Brightness4, Brightness7 } from "@mui/icons-material";
import { useAuthStore } from "../contexts/authStore";
import { useTranslation } from "react-i18next";

export default function ThemeSwitcher() {
  const { t } = useTranslation();
  const { theme, setTheme, user, accessToken } = useAuthStore();

  const toggleTheme = async () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);

    // Update in DB if logged in
    if (user && accessToken) {
      try {
        const response = await fetch('/api/auth/profile/', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ theme_preference: newTheme }),
        });
        if (!response.ok) {
          console.error('Failed to update theme preference');
        }
      } catch (error) {
        console.error('Error updating theme:', error);
      }
    }
  };

  return (
    <Tooltip title={t('Switch to {{theme}} mode', { theme: theme === 'light' ? 'dark' : 'light' })}>
      <IconButton onClick={toggleTheme} color="inherit">
        {theme === 'light' ? <Brightness4 /> : <Brightness7 />}
      </IconButton>
    </Tooltip>
  );
}