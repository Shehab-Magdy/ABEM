/**
 * Main app shell: sidebar navigation + top bar + content outlet.
 * Navigation items are role-aware (admin vs owner), split into sections.
 */
import { useState, useEffect } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  AppBar,
  Avatar,
  Badge,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  AccountBalance,
  AccountCircle,
  Apartment,
  Assessment,
  Business,
  Category,
  ExitToApp,
  Menu as MenuIcon,
  Notifications,
  Payment,
  People,
} from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../hooks/useAuth";
import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../contexts/authStore";
import { usePreferredLanguage } from "../../hooks/usePreferredLanguage";
import { useDirection } from "../../hooks/useDirection";
import axiosClient from "../../api/axiosClient";
import { TutorialButton } from "../../tutorial/TutorialOverlay";
import LanguageSwitcher from "../LanguageSwitcher";

const DRAWER_WIDTH = 240;

function NavItem({ to, icon, label, currentPath }) {
  const isActive = currentPath.startsWith(to);
  return (
    <ListItem disablePadding>
      <ListItemButton
        component={Link}
        to={to}
        selected={isActive}
        sx={{
          borderRadius: 1,
          mx: 1,
          "&.Mui-selected": { bgcolor: "rgba(255,255,255,0.15)", color: "white" },
          "&:hover": { bgcolor: "rgba(255,255,255,0.1)" },
          color: "rgba(255,255,255,0.85)",
        }}
      >
        <ListItemIcon sx={{ color: "inherit", minWidth: 36 }}>{icon}</ListItemIcon>
        <ListItemText primary={label} primaryTypographyProps={{ fontSize: 14 }} />
      </ListItemButton>
    </ListItem>
  );
}

function NavSection({ title, items, currentPath }) {
  if (items.length === 0) return null;
  return (
    <>
      <Box sx={{ px: 2, pt: 1.5, pb: 0.25 }}>
        <Typography
          variant="overline"
          sx={{ color: "rgba(255,255,255,0.38)", fontSize: 10, letterSpacing: 1.5, lineHeight: 1 }}
        >
          {title}
        </Typography>
      </Box>
      <List sx={{ pt: 0, pb: 0.5 }}>
        {items.map((item) => (
          <NavItem key={item.to} {...item} currentPath={currentPath} />
        ))}
      </List>
    </>
  );
}

export default function DashboardLayout() {
  const { user, isAdmin } = useAuth();
  const { logout, refreshToken } = useAuthStore();
  const { t } = useTranslation(["common"]);
  const dir = useDirection();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);

  // Sync language from user preference on mount
  usePreferredLanguage();

  useEffect(() => {
    axiosClient
      .get("/notifications/", { params: { is_read: "false" } })
      .then((r) => {
        const data = r.data;
        const count = Array.isArray(data)
          ? data.length
          : (data.count ?? (data.results ?? []).length);
        setUnreadCount(count);
      })
      .catch(() => {});
  }, [location.pathname]);

  const handleLogout = async () => {
    try {
      await authApi.logout(refreshToken);
    } catch { /* best-effort */ }
    logout();
    navigate("/login", { replace: true });
  };

  const mainItems = [
    { to: "/dashboard", icon: <Assessment />, label: "Dashboard", show: true },
    { to: "/buildings", icon: <Business />, label: "Buildings", show: isAdmin },
    { to: "/expenses", icon: <Apartment />, label: "Expenses", show: true },
    { to: "/payments", icon: <Payment />, label: "Payments", show: true },
    { to: "/notifications", icon: <Notifications />, label: "Notifications", show: true },
  ].filter((i) => i.show);

  const adminItems = [
    { to: "/users", icon: <People />, label: "Users", show: isAdmin },
    { to: "/expense-categories", icon: <Category />, label: "Categories", show: isAdmin },
    { to: "/assets", icon: <AccountBalance />, label: "Assets", show: isAdmin },
  ].filter((i) => i.show);

  const accountItems = [
    { to: "/profile", icon: <AccountCircle />, label: "Profile", show: true },
  ];

  const drawer = (
    <Box sx={{ height: "100%", bgcolor: "primary.dark", display: "flex", flexDirection: "column" }}>
      <Box sx={{ p: 2.5, pb: 2 }}>
        <Box component="img" src="/abem-logo-dark.svg" alt="ABEM" sx={{ height: 36, mb: 0.5 }} />
        <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.6)", display: "block" }}>
          Building Expense Manager
        </Typography>
      </Box>
      <Divider sx={{ borderColor: "rgba(255,255,255,0.12)" }} />

      <Box sx={{ flex: 1, overflowY: "auto", pt: 0.5 }}>
        <NavSection title="Main" items={mainItems} currentPath={location.pathname} />

        {adminItems.length > 0 && (
          <>
            <Divider sx={{ borderColor: "rgba(255,255,255,0.08)", mx: 2, my: 0.5 }} />
            <NavSection title="Admin" items={adminItems} currentPath={location.pathname} />
          </>
        )}

        <Divider sx={{ borderColor: "rgba(255,255,255,0.08)", mx: 2, my: 0.5 }} />
        <NavSection title="Account" items={accountItems} currentPath={location.pathname} />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      {/* Sidebar – permanent on desktop */}
      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: 0 }}>
        <Drawer
          variant="temporary"
          anchor={dir === "rtl" ? "right" : "left"}
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ display: { xs: "block", md: "none" }, "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" } }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          anchor={dir === "rtl" ? "right" : "left"}
          sx={{ display: { xs: "none", md: "block" }, "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box", border: "none" } }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main area */}
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Top AppBar */}
        <AppBar position="static" color="inherit" elevation={0} sx={{ borderBottom: "1px solid", borderColor: "divider" }}>
          <Toolbar>
            <IconButton edge="start" sx={{ mr: 2, display: { md: "none" } }} onClick={() => setMobileOpen(true)}>
              <MenuIcon />
            </IconButton>
            <Box flex={1} />
            <TutorialButton />
            <LanguageSwitcher />
            <Tooltip title={t("common:filter") === "تصفية" ? "الإشعارات" : "Notifications"}>
              <IconButton
                color="inherit"
                onClick={() => navigate("/notifications")}
                aria-label="notifications"
                data-testid="notification-bell"
                sx={{ mr: 1 }}
              >
                <Badge badgeContent={unreadCount || null} color="error" data-testid="notification-badge">
                  <Notifications />
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title="Account">
              <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} size="small">
                <Avatar
                  src={user?.profile_picture || undefined}
                  sx={{ width: 32, height: 32, bgcolor: "primary.main", fontSize: 14 }}
                >
                  {user?.first_name?.[0]}{user?.last_name?.[0]}
                </Avatar>
              </IconButton>
            </Tooltip>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={() => setAnchorEl(null)}
              transformOrigin={{ horizontal: "right", vertical: "top" }}
              anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
            >
              <MenuItem sx={{ pointerEvents: "none", opacity: 0.7 }}>
                <Typography variant="body2">{user?.email}</Typography>
              </MenuItem>
              <Divider />
              <MenuItem component={Link} to="/profile" onClick={() => setAnchorEl(null)}>
                <AccountCircle fontSize="small" sx={{ mr: 1 }} />
                My Profile
              </MenuItem>
              <MenuItem onClick={handleLogout} sx={{ color: "error.main" }}>
                <ExitToApp fontSize="small" sx={{ mr: 1 }} />
                Sign Out
              </MenuItem>
            </Menu>
          </Toolbar>
        </AppBar>

        {/* Page content */}
        <Box component="main" sx={{ flex: 1, overflow: "auto", p: 3, bgcolor: "background.default" }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
