/**
 * Notification Centre — Sprint 6 + Feature 4.
 * Lists user notifications with read/unread filter and mark-as-read.
 * Admin users also see a Broadcast form.
 * All authenticated users can send messages to building members.
 */
import { useEffect, useState, useCallback } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import axiosClient from "../../api/axiosClient";
import { useAuth } from "../../hooks/useAuth";

const TYPE_LABELS = {
  payment_due: "Payment Due",
  payment_overdue: "Payment Overdue",
  payment_confirmed: "Payment Confirmed",
  expense_added: "Expense Added",
  expense_updated: "Expense Updated",
  user_registered: "User Registered",
  announcement: "Announcement",
};

const TYPE_COLORS = {
  payment_due: "warning",
  payment_overdue: "error",
  payment_confirmed: "success",
  expense_added: "info",
  expense_updated: "info",
  user_registered: "default",
  announcement: "primary",
};

export default function NotificationCenterPage() {
  const { isAdmin } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState("all"); // "all" | "unread"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Broadcast form state (admin only)
  const [buildings, setBuildings] = useState([]);
  const [broadcastBuilding, setBroadcastBuilding] = useState("");
  const [broadcastSubject, setBroadcastSubject] = useState("");
  const [broadcastMessage, setBroadcastMessage] = useState("");
  const [broadcastStatus, setBroadcastStatus] = useState("");
  const [broadcastOpen, setBroadcastOpen] = useState(false);

  // Send message form (all users)
  const [sendOpen, setSendOpen] = useState(false);
  const [sendBuilding, setSendBuilding] = useState("");
  const [sendTitle, setSendTitle] = useState("");
  const [sendMessage, setSendMessage] = useState("");
  const [sendRecipientType, setSendRecipientType] = useState("all");
  const [sendRecipientIds, setSendRecipientIds] = useState("");
  const [sendingMsg, setSendingMsg] = useState(false);
  const [sendStatus, setSendStatus] = useState("");
  // Building members for individual send
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
      .catch(() => setError("Failed to load notifications."))
      .finally(() => setLoading(false));
  }, [filter]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // Fetch building list for all users (broadcast + send)
  useEffect(() => {
    axiosClient
      .get("/buildings/")
      .then((r) => setBuildings(r.data.results ?? r.data))
      .catch(() => {});
  }, []);

  // Load building members when sendBuilding changes and recipient type is "individual"
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
      .catch(() => setBroadcastStatus("Broadcast failed."));
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
        setSendStatus("Failed to send message.");
      }
    } finally {
      setSendingMsg(false);
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Notifications
        </Typography>
        {unreadCount > 0 && (
          <Chip
            label={`${unreadCount} unread`}
            color="error"
            size="small"
            data-testid="unread-count-chip"
          />
        )}
      </Box>

      {/* Filter chips */}
      <Stack direction="row" spacing={1} sx={{ mb: 3 }}>
        <Chip
          label="All"
          onClick={() => setFilter("all")}
          color={filter === "all" ? "primary" : "default"}
          variant={filter === "all" ? "filled" : "outlined"}
          clickable
          data-testid="filter-all"
        />
        <Chip
          label="Unread"
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
        <Box sx={{ display: "flex", justifyContent: "center", mt: 6 }}>
          <CircularProgress />
        </Box>
      ) : notifications.length === 0 ? (
        <Alert severity="info" data-testid="empty-notifications">
          No notifications yet.
        </Alert>
      ) : (
        <Stack spacing={1.5} data-testid="notification-list">
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
              <CardContent sx={{ display: "flex", alignItems: "flex-start", gap: 2, py: 1.5, "&:last-child": { pb: 1.5 } }}>
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                    <Chip
                      label={TYPE_LABELS[n.notification_type] ?? n.notification_type}
                      color={TYPE_COLORS[n.notification_type] ?? "default"}
                      size="small"
                      data-testid="notification-type-chip"
                    />
                    {!n.is_read && (
                      <Chip label="New" size="small" color="primary" variant="outlined" />
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
                    Mark as Read
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      {/* ── Send Message (all users) ── */}
      <Box sx={{ mt: 4 }}>
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
          <Typography variant="h6">Send Message</Typography>
          <Button
            size="small"
            variant="outlined"
            onClick={() => setSendOpen((p) => !p)}
          >
            {sendOpen ? "Hide" : "Show"}
          </Button>
        </Box>

        {sendOpen && (
          <Card variant="outlined">
            <CardContent>
              <Stack spacing={2}>
                <FormControl size="small" fullWidth>
                  <InputLabel>Building</InputLabel>
                  <Select
                    value={sendBuilding}
                    label="Building"
                    onChange={(e) => { setSendBuilding(e.target.value); setSelectedMembers([]); }}
                  >
                    {buildings.map((b) => (
                      <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl size="small" fullWidth>
                  <InputLabel>Recipients</InputLabel>
                  <Select
                    value={sendRecipientType}
                    label="Recipients"
                    onChange={(e) => { setSendRecipientType(e.target.value); setSelectedMembers([]); }}
                  >
                    <MenuItem value="all">All members</MenuItem>
                    <MenuItem value="admins">Admins only</MenuItem>
                    <MenuItem value="owners">Owners only</MenuItem>
                    <MenuItem value="individual">Specific person</MenuItem>
                  </Select>
                </FormControl>

                {sendRecipientType === "individual" && buildingMembers.length > 0 && (
                  <FormControl size="small" fullWidth>
                    <InputLabel>Select recipient(s)</InputLabel>
                    <Select
                      multiple
                      value={selectedMembers}
                      label="Select recipient(s)"
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
                  label="Subject"
                  value={sendTitle}
                  onChange={(e) => setSendTitle(e.target.value)}
                  fullWidth
                />
                <TextField
                  size="small"
                  label="Message"
                  value={sendMessage}
                  onChange={(e) => setSendMessage(e.target.value)}
                  multiline
                  rows={3}
                  fullWidth
                />
                <Button
                  variant="contained"
                  onClick={handleSendMessage}
                  disabled={sendingMsg || !sendBuilding || !sendTitle || !sendMessage || (sendRecipientType === "individual" && selectedMembers.length === 0)}
                >
                  {sendingMsg ? <CircularProgress size={20} color="inherit" /> : "Send Message"}
                </Button>
                {sendStatus && (
                  <Alert severity={sendStatus.startsWith("Message sent") ? "success" : "error"}>
                    {sendStatus}
                  </Alert>
                )}
              </Stack>
            </CardContent>
          </Card>
        )}
      </Box>

      {/* ── Admin broadcast ── */}
      {isAdmin && (
        <Box sx={{ mt: 4 }}>
          <Divider sx={{ mb: 2 }} />
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
            <Typography variant="h6">Broadcast Announcement</Typography>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setBroadcastOpen((p) => !p)}
              data-testid="broadcast-toggle"
            >
              {broadcastOpen ? "Hide" : "Show"}
            </Button>
          </Box>

          {broadcastOpen && (
            <Card variant="outlined" data-testid="broadcast-form">
              <CardContent>
                <Stack spacing={2}>
                  <FormControl size="small" fullWidth>
                    <InputLabel>Building</InputLabel>
                    <Select
                      value={broadcastBuilding}
                      label="Building"
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
                    label="Subject"
                    value={broadcastSubject}
                    onChange={(e) => setBroadcastSubject(e.target.value)}
                    inputProps={{ "data-testid": "broadcast-subject" }}
                    fullWidth
                  />
                  <TextField
                    size="small"
                    label="Message"
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
                  >
                    Send Broadcast
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
            </Card>
          )}
        </Box>
      )}
    </Box>
  );
}
