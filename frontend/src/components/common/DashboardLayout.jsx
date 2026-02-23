/**
 * Main app shell: top app bar + sidebar navigation + content outlet.
 * Full implementation in Sprint 2.
 */
import { Outlet } from "react-router-dom";
import { Box, Typography } from "@mui/material";

export default function DashboardLayout() {
  // TODO Sprint 2: implement sidebar navigation, app bar, breadcrumbs
  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      {/* Sidebar placeholder */}
      <Box sx={{ width: 240, bgcolor: "primary.main", color: "white", p: 2 }}>
        <Typography variant="h6">ABEM</Typography>
        {/* TODO Sprint 2: NavMenu component */}
      </Box>

      {/* Main content */}
      <Box component="main" sx={{ flex: 1, overflow: "auto", p: 3, bgcolor: "background.default" }}>
        <Outlet />
      </Box>
    </Box>
  );
}
