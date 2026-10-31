/**
 * Header notification bell + popover panel (GitHub/Facebook style).
 * - Badge uses the shared notification store (optimistic on mark-read / mark-all, reconciled with
 *   GET /notifications/unread-count/ on open, on tab focus and on route change).
 * - List is paged 10 at a time; an IntersectionObserver on a sentinel loads the next page.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Badge,
  Box,
  Button,
  CircularProgress,
  IconButton,
  Popover,
  Skeleton,
  Tab,
  Tabs,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  Campaign,
  CheckCircle,
  ChatBubbleOutline,
  ErrorOutline,
  Notifications,
  NotificationsNone,
  PersonAdd,
  Receipt,
  Payment,
} from "@mui/icons-material";
import axiosClient from "../api/axiosClient";
import { useNotificationStore } from "../contexts/notificationStore";
import { useAuth } from "../hooks/useAuth";

const PAGE_SIZE = 10;

const TYPE_ICONS = {
  payment_due: <Payment fontSize="small" color="warning" />,
  payment_overdue: <ErrorOutline fontSize="small" color="error" />,
  payment_confirmed: <CheckCircle fontSize="small" color="success" />,
  expense_added: <Receipt fontSize="small" color="info" />,
  expense_updated: <Receipt fontSize="small" color="info" />,
  user_registered: <PersonAdd fontSize="small" color="action" />,
  announcement: <Campaign fontSize="small" color="primary" />,
  message: <ChatBubbleOutline fontSize="small" color="secondary" />,
};

/** Where a notification leads, or null when it has no specific target (opens the centre). */
function targetFor(n, isAdmin) {
  const m = n.metadata || {};
  if (m.poll_id) return "/polls";
  if (m.report_id) return "/maintenance";
  if (m.kind === "plan") return isAdmin ? "/plan" : null;
  if (m.expense_id || n.notification_type?.startsWith("expense_")) return "/expenses";
  if (n.notification_type?.startsWith("payment_")) return "/payments";
  return null;
}

function relativeTime(iso, lang) {
  const diff = (new Date(iso).getTime() - Date.now()) / 1000;
  const rtf = new Intl.RelativeTimeFormat(`${lang}-u-nu-latn`, { numeric: "auto" });
  const abs = Math.abs(diff);
  if (abs < 60) return rtf.format(0, "second");
  if (abs < 3600) return rtf.format(Math.round(diff / 60), "minute");
  if (abs < 86400) return rtf.format(Math.round(diff / 3600), "hour");
  if (abs < 86400 * 30) return rtf.format(Math.round(diff / 86400), "day");
  if (abs < 86400 * 365) return rtf.format(Math.round(diff / (86400 * 30)), "month");
  return rtf.format(Math.round(diff / (86400 * 365)), "year");
}

function mergeById(prev, next) {
  const seen = new Set(prev.map((n) => n.id));
  return [...prev, ...next.filter((n) => !seen.has(n.id))];
}

function Row({ n, lang, onClick }) {
  return (
    <Box
      component="button"
      type="button"
      role="listitem"
      data-nitem
      data-testid="notification-menu-item"
      onClick={() => onClick(n)}
      sx={{
        display: "flex",
        gap: 1.5,
        alignItems: "flex-start",
        width: "100%",
        textAlign: "start",
        font: "inherit",
        color: "text.primary",
        bgcolor: n.is_read ? "transparent" : "action.hover",
        border: 0,
        borderBottom: "1px solid",
        borderColor: "divider",
        px: 2,
        py: 1.25,
        cursor: "pointer",
        "&:hover, &:focus-visible": { bgcolor: "action.selected" },
        "&:focus-visible": { outline: "2px solid", outlineColor: "primary.main", outlineOffset: -2 },
      }}
    >
      <Box sx={{ mt: 0.25, flexShrink: 0 }}>{TYPE_ICONS[n.notification_type] || <Notifications fontSize="small" />}</Box>
      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Typography variant="subtitle2" fontWeight={n.is_read ? 500 : 700} noWrap>
          {n.title}
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}
        >
          {n.body}
        </Typography>
        <Typography variant="caption" color={n.is_read ? "text.disabled" : "primary.main"}>
          {relativeTime(n.created_at, lang)}
        </Typography>
      </Box>
      {!n.is_read && (
        <Box
          component="span"
          data-testid="notification-unread-dot"
          aria-hidden="true"
          sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: "primary.main", flexShrink: 0, mt: 0.75 }}
        />
      )}
    </Box>
  );
}

export default function NotificationMenu() {
  const { t, i18n } = useTranslation("notifications");
  const lang = (i18n.language || "en").startsWith("ar") ? "ar" : "en";
  const isRtl = lang === "ar";
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const refreshUnread = useNotificationStore((s) => s.refreshUnread);

  const [anchorEl, setAnchorEl] = useState(null);
  const [tab, setTab] = useState("all");
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(0); // last loaded page (0 = none yet)
  const [hasMore, setHasMore] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [listEl, setListEl] = useState(null);
  const [sentinelEl, setSentinelEl] = useState(null);
  const abortRef = useRef(null);
  const inFlightRef = useRef(false);
  const genRef = useRef(0); // bumped on every reset so stale responses are ignored
  const open = Boolean(anchorEl);

  const loadPage = useCallback(
    (nextPage, filter) => {
      if (inFlightRef.current) return;
      inFlightRef.current = true;
      const gen = genRef.current;
      const controller = new AbortController();
      abortRef.current = controller;
      setStatus("loading");
      axiosClient
        .get("/notifications/", {
          params: { page: nextPage, page_size: PAGE_SIZE, ...(filter === "unread" ? { unread: "true" } : {}) },
          signal: controller.signal,
        })
        .then((r) => {
          if (gen !== genRef.current) return;
          const results = Array.isArray(r.data) ? r.data : (r.data.results ?? []);
          setItems((prev) => mergeById(nextPage === 1 ? [] : prev, results));
          setPage(nextPage);
          setHasMore(Boolean(r.data?.next));
          setStatus("idle");
        })
        .catch((err) => {
          if (gen !== genRef.current || err?.code === "ERR_CANCELED") return;
          setStatus("error");
        })
        .finally(() => {
          if (gen === genRef.current) inFlightRef.current = false;
        });
    },
    [],
  );

  const reset = useCallback(
    (filter) => {
      abortRef.current?.abort();
      genRef.current += 1;
      inFlightRef.current = false;
      setItems([]);
      setPage(0);
      setHasMore(false);
      setStatus("loading");
      loadPage(1, filter);
    },
    [loadPage],
  );

  const handleOpen = (e) => {
    setAnchorEl(e.currentTarget);
    setTab("all");
    reset("all");
    refreshUnread();
  };

  const handleClose = () => {
    abortRef.current?.abort();
    genRef.current += 1;
    inFlightRef.current = false;
    setAnchorEl(null);
  };

  const handleTab = (_e, value) => {
    setTab(value);
    reset(value);
  };

  // Infinite scroll: observe the sentinel inside the scroll container.
  useEffect(() => {
    if (!open || !listEl || !sentinelEl || !hasMore || status !== "idle") return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) loadPage(page + 1, tab);
      },
      { root: listEl, rootMargin: "0px 0px 80px 0px" },
    );
    observer.observe(sentinelEl);
    return () => observer.disconnect();
  }, [open, listEl, sentinelEl, hasMore, status, page, tab, loadPage]);

  // Keep the badge fresh when the tab regains focus (no extra polling).
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") refreshUnread();
    };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onVisible);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onVisible);
      abortRef.current?.abort();
    };
  }, [refreshUnread]);

  const markOneRead = (n) => {
    if (n.is_read) return;
    setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
    useNotificationStore.getState().decrementUnread();
    axiosClient
      .post(`/notifications/${n.id}/read/`)
      .catch(() => {
        setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: false } : x)));
      })
      .finally(() => refreshUnread());
  };

  const handleItem = (n) => {
    markOneRead(n);
    const target = targetFor(n, isAdmin);
    handleClose();
    navigate(target || "/notifications");
  };

  const [markingAll, setMarkingAll] = useState(false);
  const [markAllError, setMarkAllError] = useState(false);
  const handleMarkAll = () => {
    if (markingAll) return;
    setMarkingAll(true);
    setMarkAllError(false);
    const snapshot = items;
    setItems((prev) => prev.map((x) => ({ ...x, is_read: true })));
    useNotificationStore.getState().clearUnread();
    axiosClient
      .post("/notifications/mark-all-read/")
      .catch(() => {
        setItems(snapshot);
        setMarkAllError(true);
      })
      .finally(() => {
        setMarkingAll(false);
        refreshUnread();
      });
  };

  // Arrow-key navigation between rows.
  const handleListKeyDown = (e) => {
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key)) return;
    const rows = Array.from(listEl?.querySelectorAll("[data-nitem]") || []);
    if (!rows.length) return;
    const idx = rows.indexOf(document.activeElement);
    let next = idx;
    if (e.key === "ArrowDown") next = Math.min(rows.length - 1, idx + 1);
    if (e.key === "ArrowUp") next = Math.max(0, idx - 1);
    if (e.key === "Home") next = 0;
    if (e.key === "End") next = rows.length - 1;
    e.preventDefault();
    rows[next]?.focus();
  };

  const bellLabel = unreadCount > 0 ? t("bell_label_unread", { count: unreadCount }) : t("title");
  const horizontal = isRtl ? "left" : "right";
  const initialLoading = status === "loading" && items.length === 0;
  const unreadInList = useMemo(() => items.some((n) => !n.is_read), [items]);

  return (
    <>
      <Tooltip title={t("title")}>
        <IconButton
          color="inherit"
          onClick={handleOpen}
          aria-label={bellLabel}
          aria-haspopup="true"
          aria-expanded={open ? "true" : "false"}
          aria-controls={open ? "notification-menu-panel" : undefined}
          data-testid="notification-bell"
          id="notification-bell"
          sx={{ mr: 1 }}
        >
          <Badge badgeContent={unreadCount || null} max={99} color="error" data-testid="notification-badge">
            <Notifications />
          </Badge>
        </IconButton>
      </Tooltip>
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal }}
        transformOrigin={{ vertical: "top", horizontal }}
        slotProps={{
          paper: {
            id: "notification-menu-panel",
            role: "dialog",
            "aria-label": t("title"),
            sx: {
              width: { xs: "calc(100vw - 16px)", sm: 400 },
              maxWidth: "calc(100vw - 16px)",
              maxHeight: "min(600px, calc(100dvh - 80px))",
              display: "flex",
              flexDirection: "column",
              mt: 0.5,
            },
          },
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1, px: 2, pt: 1.5 }}>
          <Typography variant="h6" component="h2" fontWeight={700}>
            {t("title")}
          </Typography>
          <Button size="small" onClick={handleMarkAll} disabled={markingAll || (unreadCount === 0 && !unreadInList)}>
            {t("mark_all_read")}
          </Button>
        </Box>
        <Tabs value={tab} onChange={handleTab} variant="fullWidth" aria-label={t("title")} sx={{ minHeight: 40 }}>
          <Tab value="all" label={t("all")} data-testid="menu-tab-all" sx={{ minHeight: 40 }} />
          <Tab value="unread" label={t("unread")} data-testid="menu-tab-unread" sx={{ minHeight: 40 }} />
        </Tabs>
        {markAllError && (
          <Alert severity="error" sx={{ borderRadius: 0 }} onClose={() => setMarkAllError(false)}>
            {t("mark_all_failed")}
          </Alert>
        )}
        <Box
          ref={setListEl}
          role="list"
          aria-busy={status === "loading"}
          aria-label={tab === "unread" ? t("unread") : t("all")}
          onKeyDown={handleListKeyDown}
          data-testid="notification-menu-list"
          sx={{ flex: 1, overflowY: "auto", minHeight: 120, borderTop: "1px solid", borderColor: "divider" }}
        >
          {initialLoading &&
            [0, 1, 2, 3].map((i) => (
              <Box key={i} sx={{ display: "flex", gap: 1.5, px: 2, py: 1.5 }} data-testid="notification-menu-skeleton">
                <Skeleton variant="circular" width={24} height={24} />
                <Box sx={{ flex: 1 }}>
                  <Skeleton width="60%" />
                  <Skeleton />
                  <Skeleton width="30%" />
                </Box>
              </Box>
            ))}
          {status === "error" && items.length === 0 && (
            <Box sx={{ p: 2 }} data-testid="notification-menu-error">
              <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => reset(tab)}>{t("retry")}</Button>}>
                {t("load_error")}
              </Alert>
            </Box>
          )}
          {status === "idle" && items.length === 0 && (
            <Box sx={{ textAlign: "center", p: 4, color: "text.secondary" }} data-testid="notification-menu-empty">
              <NotificationsNone sx={{ fontSize: 40, opacity: 0.6 }} />
              <Typography variant="body2">{tab === "unread" ? t("empty_unread") : t("no_notifications")}</Typography>
              {tab === "unread" && <Typography variant="caption">{t("all_caught_up")}</Typography>}
            </Box>
          )}
          {items.map((n) => (
            <Row key={n.id} n={n} lang={lang} onClick={handleItem} />
          ))}
          {items.length > 0 && status === "error" && (
            <Box sx={{ p: 1.5 }}>
              <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => loadPage(page + 1, tab)}>{t("retry")}</Button>}>
                {t("load_error")}
              </Alert>
            </Box>
          )}
          {items.length > 0 && status === "loading" && (
            <Box sx={{ display: "flex", justifyContent: "center", py: 1.5 }} role="status" aria-label={t("loading_more")}>
              <CircularProgress size={20} />
            </Box>
          )}
          {hasMore && <Box ref={setSentinelEl} data-testid="notification-menu-sentinel" sx={{ height: 1 }} />}
        </Box>
        <Box sx={{ borderTop: "1px solid", borderColor: "divider", p: 0.5, textAlign: "center" }}>
          <Button
            fullWidth
            size="small"
            onClick={() => {
              handleClose();
              navigate("/notifications");
            }}
            data-testid="notification-menu-open-center"
          >
            {t("menu_open_center")}
          </Button>
        </Box>
      </Popover>
    </>
  );
}
