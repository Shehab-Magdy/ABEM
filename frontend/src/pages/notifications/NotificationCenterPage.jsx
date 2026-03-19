/**
 * Notification Centre — Sprint 6 + Feature 4.
 * Layout: compose panels (Send Message + Broadcast) at the top, side by side.
 *         Notifications list below. All three sections are independently collapsible.
 * Admin users also see a Broadcast form.
 * All authenticated users can send messages to building members.
 */
import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import {
  Send,
  Campaign,
  Notifications as NotificationsIcon,
  ExpandMore,
  ExpandLess,
} from "@mui/icons-material";
import axiosClient from "../../api/axiosClient";
import { useAuth } from "../../hooks/useAuth";
import { PrivateSEO } from "../../components/seo/SEO";

const TYPE_COLORS = {
  payment_due: "warning",
  payment_overdue: "error",
  payment_confirmed: "success",
  expense_added: "info",
  expense_updated: "info",
  user_registered: "default",
  announcement: "primary",
};

// ── Collapsible section header ─────────────────────────────────────────────

function SectionHeader({ icon, title, badge, open, onToggle, accent }) {
  return (
    <Box
      onClick={onToggle}
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.5,
        px: 2,
        py: 1.5,
        cursor: "pointer",
        borderRadius: open ? "10px 10px 0 0" : "10px",
        bgcolor: open ? `${accent}14` : "transparent",
        transition: "background-color 0.2s",
        "&:hover": { bgcolor: `${accent}1a` },
        userSelect: "none",
      }}
    >
      <Box
        sx={{
          width: 34,
          height: 34,
          borderRadius: "8px",
          bgcolor: `${accent}1a`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: accent,
          flexShrink: 0,
        }}
      >
        {icon}
      </Box>
      <Typography variant="subtitle1" fontWeight={700} sx={{ flex: 1, color: "#1F2937" }}>
        {title}
      </Typography>
      {badge !== undefined && badge > 0 && (
        <Chip label={badge} size="small" color="error" sx={{ height: 20, fontSize: 11 }} />
      )}
      <Box sx={{ color: "#6B7280" }}>
        {open ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
      </Box>
    </Box>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export default function NotificationCenterPage() {
  const { t } = useTranslation("notifications");
  const TYPE_LABELS = {
    payment_due: t("type_payment_due", "Payment Due"),
    payment_overdue: t("type_payment_overdue", "Payment Overdue"),
    payment_confirmed: t("type_payment_confirmed", "Payment Confirmed"),
    expense_added: t("type_expense_added", "Expense Added"),
    expense_updated: t("type_expense_updated", "Expense Updated"),
    user_registered: t("type_user_registered", "User Registered"),
    announcement: t("type_announcement", "Announcement"),
  };
  const { isAdmin } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Section open/closed state
  const [sendOpen, setSendOpen] = useState(false);
  const [broadcastOpen, setBroadcastOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(true);

  // Broadcast form state (admin only)
  const [buildings, setBuildings] = useState([]);
  const [broadcastBuilding, setBroadcastBuilding] = useState("");
  const [broadcastSubject, setBroadcastSubject] = useState("");
  const [broadcastMessage, setBroadcastMessage] = useState("");
  const [broadcastStatus, setBroadcastStatus] = useState("");

  // Send message form (all users)
  const [sendBuilding, setSendBuilding] = useState("");
  const [sendTitle, setSendTitle] = useState("");
  const [sendMessage, setSendMessage] = useState("");
  const [sendRecipientType, setSendRecipientType] = useState("all");
  const [sendingMsg, setSendingMsg] = useState(false);
  const [sendStatus, setSendStatus] = useState("");
  const [buildingMembers, setBuildingMembers] = useState([]);
  const [selectedMembers, setSelectedMembers] = useState([]);

  const fetchNotifications = useCallback(() => {
    setLoading(true);
    setError("");
    const params = filter === "unread" ? { is_read: "false" } : undefined;
    axiosClient
      .get("/notifications/", { params })
      .then((r) => {
        const data = r.data;
        setNotifications(Array.isArray(data) ? data : (data.results ?? []));
      })
      .catch(() => setError(t("load_error", "Failed to load notifications.")))
      .finally(() => setLoading(false));
  }, [filter]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  useEffect(() => {
    axiosClient
      .get("/buildings/")
      .then((r) => setBuildings(r.data.results ?? r.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!sendBuilding || sendRecipientType !== "individual") {
      setBuildingMembers([]);
      setSelectedMembers([]);
      return;
    }
    axiosClient
      .get("/users/", { params: { building_id: sendBuilding, page_size: 200 } })
      .then((r) => setBuildingMembers(r.data.results ?? r.data))
      .catch(() => setBuildingMembers([]));
  }, [sendBuilding, sendRecipientType]);

  const handleMarkRead = (id) => {
    axiosClient
      .post(`/notifications/${id}/read/`)
      .then(() => fetchNotifications())
      .catch(() => {});
  };

  const handleBroadcast = () => {
    if (!broadcastBuilding || !broadcastSubject || !broadcastMessage) return;
    axiosClient
      .post("/notifications/broadcast/", {
        subject: broadcastSubject,
        message: broadcastMessage,
        building_id: broadcastBuilding,
      })
      .then((r) => {
        setBroadcastStatus(`Sent to ${r.data.created} owner(s).`);
        setBroadcastSubject("");
        setBroadcastMessage("");
        setBroadcastBuilding("");
      })
      .catch(() => setBroadcastStatus(t("broadcast_failed", "Broadcast failed.")));
  };

  const handleSendMessage = async () => {
    if (!sendBuilding || !sendTitle || !sendMessage) return;
    setSendingMsg(true);
    setSendStatus("");
    try {
      const payload = {
        building_id: sendBuilding,
        title: sendTitle,
        message: sendMessage,
        recipient_type: sendRecipientType,
      };
      if (sendRecipientType === "individual") {
        payload.recipient_ids = selectedMembers;
      }
      const r = await axiosClient.post("/notifications/send/", payload);
      setSendStatus(`Message sent to ${r.data.created} recipient(s).`);
      setSendTitle("");
      setSendMessage("");
      setSendBuilding("");
      setSendRecipientType("all");
      setSelectedMembers([]);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 403 && detail) {
        setSendStatus(`${detail} Please contact your building admin.`);
      } else {
        setSendStatus(t("send_failed", "Failed to send message."));
      }
    } finally {
      setSendingMsg(false);
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <>
      <PrivateSEO title="ABEM – Notifications" />
      <Box sx={{ p: 3, maxWidth: 1200 }}>
      <Typography variant="h4" fontWeight={700} sx={{ mb: 3 }}>
        {t("title")}
      </Typography>

      {/* ── Top compose row ── */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: isAdmin ? "1fr 1fr" : "1fr",
          gap: 2,
          mb: 3,
        }}
      >
        {/* Send Message panel */}
        <Card
          variant="outlined"
          sx={{
            borderRadius: "12px",
            borderColor: sendOpen ? "#6366F1" : "#E5E7EB",
            transition: "border-color 0.2s",
          }}
        >
          <SectionHeader
            icon={<Send fontSize="small" />}
            title={t("sendMessage")}
            open={sendOpen}
            onToggle={() => setSendOpen((p) => !p)}
            accent="#6366F1"
          />

          <Collapse in={sendOpen}>
            <Divider />
            <CardContent sx={{ pt: 2 }}>
              <Stack spacing={2}>
                <FormControl size="small" fullWidth>
                  <InputLabel>{t("building")}</InputLabel>
                  <Select
                    value={sendBuilding}
                    label={t("building")}
                    onChange={(e) => {
                      setSendBuilding(e.target.value);
                      setSelectedMembers([]);
                    }}
                  >
                    {buildings.map((b) => (
                      <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl size="small" fullWidth>
                  <InputLabel>{t("recipients")}</InputLabel>
                  <Select
                    value={sendRecipientType}
                    label={t("recipients")}
                    onChange={(e) => {
                      setSendRecipientType(e.target.value);
                      setSelectedMembers([]);
                    }}
                  >
                    <MenuItem value="all">{t("allMembers")}</MenuItem>
                    <MenuItem value="admins">{t("adminsOnly")}</MenuItem>
                    <MenuItem value="owners">{t("ownersOnly")}</MenuItem>
                    <MenuItem value="individual">{t("specificPerson")}</MenuItem>
                  </Select>
                </FormControl>

                {sendRecipientType === "individual" && buildingMembers.length > 0 && (
                  <FormControl size="small" fullWidth>
                    <InputLabel>{t("selectRecipients")}</InputLabel>
                    <Select
                      multiple
                      value={selectedMembers}
                      label={t("selectRecipients")}
                      onChange={(e) => setSelectedMembers(e.target.value)}
                      renderValue={(selected) =>
                        buildingMembers
                          .filter((m) => selected.includes(m.id))
                          .map((m) => `${m.first_name} ${m.last_name}`.trim() || m.email)
                          .join(", ")
                      }
                    >
                      {buildingMembers.map((m) => (
                        <MenuItem key={m.id} value={m.id}>
                          {m.first_name} {m.last_name} — {m.email}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}

                <TextField
                  size="small"
                  label={t("subject")}
                  value={sendTitle}
                  onChange={(e) => setSendTitle(e.target.value)}
                  fullWidth
                />
                <TextField
                  size="small"
                  label={t("message")}
                  value={sendMessage}
                  onChange={(e) => setSendMessage(e.target.value)}
                  multiline
                  rows={3}
                  fullWidth
                />
                <Button
                  variant="contained"
                  onClick={handleSendMessage}
                  disabled={
                    sendingMsg ||
                    !sendBuilding ||
                    !sendTitle ||
                    !sendMessage ||
                    (sendRecipientType === "individual" && selectedMembers.length === 0)
                  }
                  sx={{
                    bgcolor: "#6366F1",
                    "&:hover": { bgcolor: "#4F46E5" },
                    textTransform: "none",
                    fontWeight: 600,
                  }}
                >
                  {sendingMsg ? <CircularProgress size={20} color="inherit" /> : t("sendMessage")}
                </Button>
                {sendStatus && (
                  <Alert severity={sendStatus.startsWith("Message sent") ? "success" : "error"}>
                    {sendStatus}
                  </Alert>
                )}
              </Stack>
            </CardContent>
          </Collapse>
        </Card>

        {/* Broadcast panel (admin only) */}
        {isAdmin && (
          <Card
            variant="outlined"
            sx={{
              borderRadius: "12px",
              borderColor: broadcastOpen ? "#F59E0B" : "#E5E7EB",
              transition: "border-color 0.2s",
            }}
          >
            <SectionHeader
              icon={<Campaign fontSize="small" />}
              title={t("broadcastAnnouncement")}
              open={broadcastOpen}
              onToggle={() => setBroadcastOpen((p) => !p)}
              accent="#F59E0B"
              data-testid="broadcast-toggle"
            />

            <Collapse in={broadcastOpen}>
              <Divider />
              <CardContent sx={{ pt: 2 }} data-testid="broadcast-form">
                <Stack spacing={2}>
                  <FormControl size="small" fullWidth>
                    <InputLabel>{t("building")}</InputLabel>
                    <Select
                      value={broadcastBuilding}
                      label={t("building")}
                      onChange={(e) => setBroadcastBuilding(e.target.value)}
                      inputProps={{ "data-testid": "broadcast-building" }}
                    >
                      {buildings.map((b) => (
                        <MenuItem key={b.id} value={b.id}>
                          {b.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <TextField
                    size="small"
                    label={t("subject")}
                    value={broadcastSubject}
                    onChange={(e) => setBroadcastSubject(e.target.value)}
                    inputProps={{ "data-testid": "broadcast-subject" }}
                    fullWidth
                  />
                  <TextField
                    size="small"
                    label={t("message")}
                    value={broadcastMessage}
                    onChange={(e) => setBroadcastMessage(e.target.value)}
                    inputProps={{ "data-testid": "broadcast-message" }}
                    multiline
                    rows={3}
                    fullWidth
                  />
                  <Button
                    variant="contained"
                    onClick={handleBroadcast}
                    data-testid="broadcast-send"
                    disabled={!broadcastBuilding || !broadcastSubject || !broadcastMessage}
                    sx={{
                      bgcolor: "#F59E0B",
                      color: "white",
                      "&:hover": { bgcolor: "#D97706" },
                      textTransform: "none",
                      fontWeight: 600,
                    }}
                  >
                    {t("sendBroadcast")}
                  </Button>
                  {broadcastStatus && (
                    <Alert
                      severity={broadcastStatus.includes("failed") ? "error" : "success"}
                      data-testid="broadcast-status"
                    >
                      {broadcastStatus}
                    </Alert>
                  )}
                </Stack>
              </CardContent>
            </Collapse>
          </Card>
        )}
      </Box>

      {/* ── Notifications list ── */}
      <Card
        variant="outlined"
        sx={{
          borderRadius: "12px",
          borderColor: notifOpen ? "#10B981" : "#E5E7EB",
          transition: "border-color 0.2s",
        }}
      >
        <SectionHeader
          icon={<NotificationsIcon fontSize="small" />}
          title={t("yourNotifications")}
          badge={unreadCount}
          open={notifOpen}
          onToggle={() => setNotifOpen((p) => !p)}
          accent="#10B981"
        />

        <Collapse in={notifOpen}>
          <Divider />
          <CardContent sx={{ pt: 2 }}>
            {/* Filter chips */}
            <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
              <Chip
                label={t("all")}
                onClick={() => setFilter("all")}
                color={filter === "all" ? "primary" : "default"}
                variant={filter === "all" ? "filled" : "outlined"}
                clickable
                data-testid="filter-all"
              />
              <Chip
                label={t("unread")}
                onClick={() => setFilter("unread")}
                color={filter === "unread" ? "primary" : "default"}
                variant={filter === "unread" ? "filled" : "outlined"}
                clickable
                data-testid="filter-unread"
              />
            </Stack>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {loading ? (
              <Box sx={{ display: "flex", justifyContent: "center", mt: 4, mb: 2 }}>
                <CircularProgress />
              </Box>
            ) : notifications.length === 0 ? (
              <Alert severity="info" data-testid="empty-notifications">
                {t("noNotificationsYet")}
              </Alert>
            ) : (
              <Stack id="notifications-list" spacing={1.5} data-testid="notification-list">
                {notifications.map((n) => (
                  <Card
                    key={n.id}
                    variant="outlined"
                    data-testid="notification-item"
                    sx={{
                      opacity: n.is_read ? 0.7 : 1,
                      borderLeft: n.is_read ? undefined : "4px solid",
                      borderLeftColor: n.is_read ? undefined : "primary.main",
                    }}
                  >
                    <CardContent
                      sx={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 2,
                        py: 1.5,
                        "&:last-child": { pb: 1.5 },
                      }}
                    >
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                          <Chip
                            label={TYPE_LABELS[n.notification_type] ?? n.notification_type}
                            color={TYPE_COLORS[n.notification_type] ?? "default"}
                            size="small"
                            data-testid="notification-type-chip"
                          />
                          {!n.is_read && (
                            <Chip label={t("new")} size="small" color="primary" variant="outlined" />
                          )}
                        </Box>
                        <Typography variant="subtitle2" fontWeight={600}>
                          {n.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {n.body}
                        </Typography>
                        <Stack direction="row" spacing={1} alignItems="center" mt={0.5}>
                          <Typography variant="caption" color="text.disabled">
                            {new Date(n.created_at).toLocaleString()}
                          </Typography>
                          {n.sender_name && (
                            <Typography variant="caption" color="text.disabled">
                              · From: {n.sender_name}
                            </Typography>
                          )}
                        </Stack>
                      </Box>
                      {!n.is_read && (
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleMarkRead(n.id)}
                          data-testid="mark-read-btn"
                        >
                          {t("markAsRead")}
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </CardContent>
        </Collapse>
      </Card>
    </Box>
    </>
  );
}
