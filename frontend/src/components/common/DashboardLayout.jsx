/**
 * Main app shell: collapsible sidebar + top bar + content outlet.
 * Sidebar position follows document dir (left in LTR, right in RTL).
 * Burger menu always visible to toggle sidebar open/closed.
 */
import { useState, useEffect } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  AppBar,
  Avatar,
  Badge,
  Box,
  BottomNavigation,
  BottomNavigationAction,
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
  useMediaQuery,
} from "@mui/material";
import {
  AccountBalance,
  AccountCircle,
  Apartment,
  Assessment,
  Business,
  Category,
  ChevronLeft,
  ChevronRight,
  ExitToApp,
  Menu as MenuIcon,
  Notifications,
  Payment,
  People,
} from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useTheme } from "@mui/material/styles";
import { useAuth } from "../../hooks/useAuth";
import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../contexts/authStore";
import { usePreferredLanguage } from "../../hooks/usePreferredLanguage";
import axiosClient from "../../api/axiosClient";
import { useNotificationStore } from "../../contexts/notificationStore";
import { TutorialButton } from "../../tutorial/TutorialOverlay";
import ThemeSwitcher from "../ThemeSwitcher";
import Footer from "./Footer";

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
  const { t, i18n } = useTranslation(["common", "auth"]);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  const [anchorEl, setAnchorEl] = useState(null);
  const { unreadCount, setUnreadCount } = useNotificationStore();
  const { theme: userTheme } = useAuthStore();

  usePreferredLanguage();

  const isRtl = (i18n.language || "en").startsWith("ar");

  // Close sidebar on mobile when navigating
  useEffect(() => {
    if (isMobile) setSidebarOpen(false);
  }, [location.pathname, isMobile]);

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

  const toggleSidebar = () => setSidebarOpen((prev) => !prev);

  const mainItems = [
    { to: "/dashboard", icon: <Assessment />, label: t("common:dashboard", "Dashboard"), show: true },
    { to: "/buildings", icon: <Business />, label: t("common:buildings", "Buildings"), show: isAdmin },
    { to: "/expenses", icon: <Apartment />, label: t("common:expenses", "Expenses"), show: true },
    { to: "/payments", icon: <Payment />, label: t("common:payments", "Payments"), show: true },
    { to: "/notifications", icon: <Notifications />, label: t("common:notifications", "Notifications"), show: true },
  ].filter((i) => i.show);

  const adminItems = [
    { to: "/users", icon: <People />, label: t("common:users", "Users"), show: isAdmin },
    { to: "/expense-categories", icon: <Category />, label: t("common:categories", "Categories"), show: isAdmin },
    { to: "/assets", icon: <AccountBalance />, label: t("common:assets", "Assets"), show: isAdmin },
  ].filter((i) => i.show);

  const accountItems = [
    { to: "/profile", icon: <AccountCircle />, label: t("common:profile", "Profile"), show: true },
  ];

  const bottomNavItems = [...mainItems, ...adminItems, ...accountItems]; // Include all nav items for mobile

  const drawerContent = (mode) => (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Header with close button */}
      <Box sx={{ p: 2.5, pb: 2, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Box>
          <Box component="img" src="/abem-logo-dark.svg" alt="ABEM" sx={{ height: 36, mb: 0.5 }} />
          <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.6)", display: "block" }}>
            {t("auth:apartment_building_expense")}
          </Typography>
        </Box>
        <IconButton onClick={toggleSidebar} sx={{ color: "rgba(255,255,255,0.6)" }} size="small">
          {isRtl ? <ChevronRight /> : <ChevronLeft />}
        </IconButton>
      </Box>
      <Divider sx={{ borderColor: "rgba(255,255,255,0.12)" }} />

      <Box sx={{ flex: 1, overflowY: "auto", pt: 0.5 }}>
        <NavSection title={t("common:main_section", "Main")} items={mainItems} currentPath={location.pathname} />

        {adminItems.length > 0 && (
          <>
            <Divider sx={{ borderColor: "rgba(255,255,255,0.08)", mx: 2, my: 0.5 }} />
            <NavSection title={t("common:admin_section", "Admin")} items={adminItems} currentPath={location.pathname} />
          </>
        )}

        <Divider sx={{ borderColor: "rgba(255,255,255,0.08)", mx: 2, my: 0.5 }} />
        <NavSection title={t("common:account_section", "Account")} items={accountItems} currentPath={location.pathname} />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", height: "100vh", flexDirection: "column" }}>
      {/* Sidebar */}
      {sidebarOpen && (
        isMobile ? (
          <Drawer
            anchor={isRtl ? "right" : "left"}
            open={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
            sx={{
              '& .MuiDrawer-paper': {
                width: DRAWER_WIDTH,
                bgcolor: userTheme === 'dark' ? "#2a0b3b" : "#0c5c41",
              },
            }}
          >
            {drawerContent(userTheme)}
          </Drawer>
        ) : (
          <Box
            component="nav"
            sx={{
              width: DRAWER_WIDTH,
              flexShrink: 0,
              height: "100vh",
              overflow: "hidden",
              bgcolor: userTheme === 'dark' ? "#2a0b3b" : "#0c5c41",
            }}
          >
            {drawerContent(userTheme)}
          </Box>
        )
      )}

      {/* Main area */}
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
        {/* Top AppBar */}
        <AppBar position="static" color="inherit" elevation={0} sx={{ borderBottom: "1px solid", borderColor: "divider" }}>
          <Toolbar>
            {/* Burger icon */}
            <IconButton
              edge="start"
              onClick={toggleSidebar}
              sx={{ mr: 1 }}
              aria-label={sidebarOpen ? t("common:close") : t("common:dashboard")}
            >
              <MenuIcon />
            </IconButton>
            <Box flex={1} />
            <ThemeSwitcher />
            <TutorialButton />
            <Tooltip title={t("common:notifications")}>
              <IconButton
                color="inherit"
                onClick={() => navigate("/notifications")}
                aria-label={t("common:notifications")}
                data-testid="notification-bell"
                sx={{ mr: 1 }}
              >
                <Badge badgeContent={unreadCount || null} color="error" data-testid="notification-badge">
                  <Notifications />
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title={t("common:account_section")}>
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
                {t("common:profile")}
              </MenuItem>
              <MenuItem onClick={handleLogout} sx={{ color: "error.main" }}>
                <ExitToApp fontSize="small" sx={{ mr: 1 }} />
                {t("auth:sign_out")}
              </MenuItem>
            </Menu>
          </Toolbar>
        </AppBar>

        {/* Page content */}
        <Box component="main" sx={{ flex: 1, overflow: "auto", bgcolor: "background.default", display: "flex", flexDirection: "column" }}>
          <Box sx={{ flex: 1, p: isMobile ? 2 : 3 }}>
            <Outlet />
          </Box>
          <Footer />
        </Box>

        {/* Bottom Navigation on mobile */}
        {isMobile && (
          <BottomNavigation
            value={bottomNavItems.findIndex(item => location.pathname.startsWith(item.to))}
            onChange={(event, newValue) => {
              navigate(bottomNavItems[newValue].to);
            }}
            showLabels
            sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1400 }}
          >
            {bottomNavItems.map((item, index) => (
              <BottomNavigationAction key={item.to} label={item.label} icon={item.icon} />
            ))}
          </BottomNavigation>
        )}
      </Box>

      {/* Drawer for mobile hamburger menu */}
      {isMobile && (
        <Drawer
          variant="temporary"
          anchor={isRtl ? "right" : "left"}
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" }, zIndex: 1300 }}
        >
          {drawerContent(userTheme)}
        </Drawer>
      )}
    </Box>
  );
}
