/**
 * ABEM Interactive Tutorial System
 *
 * Integration checklist:
 *   1. Wrap your router outlet with <TutorialOverlay /> anywhere inside
 *      the component that already has access to React Router context
 *      (i.e. inside <BrowserRouter> or equivalent):
 *        <BrowserRouter>
 *          <TutorialOverlay />
 *          <App />
 *        </BrowserRouter>
 *
 *   2. In DashboardLayout (or any header component), render <TutorialButton />.
 *
 *   3. Every DOM element used as an anchor MUST carry the id listed in
 *      docs/TUTORIAL_ANCHORS.md.  Search the codebase for those ids before removing
 *      or renaming elements.
 *
 *   4. The tour role is auto-detected from the logged-in user's role.
 *      Admin users get the Admin tour; all other users get the Owner tour.
 */

import { useTheme, alpha } from "@mui/material/styles";
import { useEffect, useRef, useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import {
  Box,
  Button,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { Close, NavigateBefore, NavigateNext, School } from "@mui/icons-material";
import { useAuth } from "../hooks/useAuth";

// ─────────────────────────────────────────────────────────────────────────────
// Step definitions
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Step shape: { page, anchor, titleKey, descKey, openBell? }.
 * Texts live only in public/locales/{en,ar}/tutorial.json.
 * openBell: open the header notification popover for this step (>= 600px wide; on phones the
 * popover would cover the card, so only the bell is highlighted). It is closed again on leaving the step.
 * @type {Record<'admin'|'owner', Array<{page:string, anchor:string|null, titleKey:string, descKey:string, openBell?:boolean}>>}
 */
export const TUTORIAL_STEPS = {
  admin: [
    { page: "/dashboard", anchor: null, titleKey: "step_1_title", descKey: "step_1_desc" },
    { page: "/dashboard", anchor: "language-switch", titleKey: "step_lang_title", descKey: "step_lang_desc" },
    { page: "/dashboard", anchor: "notification-bell", openBell: true, titleKey: "step_bell_title", descKey: "step_bell_desc" },
    { page: "/buildings", anchor: "add-building-btn", titleKey: "step_2_title", descKey: "step_2_desc" },
    { page: "/buildings", anchor: "building-actions-row", titleKey: "step_3_title", descKey: "step_3_desc" },
    { page: "/expenses", anchor: "add-expense-btn", titleKey: "step_4_title", descKey: "step_4_desc" },
    { page: "/expenses", anchor: "expenses-table", titleKey: "step_5_title", descKey: "step_5_desc" },
    { page: "/payments", anchor: "payments-table", titleKey: "step_pay_title", descKey: "step_pay_desc" },
    { page: "/records", anchor: "export-building-btn", titleKey: "step_rec_title", descKey: "step_rec_desc" },
    { page: "/users", anchor: "add-user-btn", titleKey: "step_6_title", descKey: "step_6_desc" },
    { page: "/expense-categories", anchor: "categories-table", titleKey: "step_7_title", descKey: "step_7_desc" },
    { page: "/assets", anchor: "assets-table", titleKey: "step_8a_title", descKey: "step_8a_desc" },
    { page: "/audit", anchor: "audit-table", titleKey: "step_8_title", descKey: "step_8_desc" },
    { page: "/plan", anchor: "plan-period-toggle", titleKey: "step_plan_title", descKey: "step_plan_desc" },
    { page: "/help", anchor: null, titleKey: "step_more_title", descKey: "step_more_desc" },
    { page: "/profile", anchor: "tutorial-profile-form", titleKey: "step_9_title", descKey: "step_9_desc" },
  ],
  owner: [
    { page: "/dashboard", anchor: null, titleKey: "step_o1_title", descKey: "step_o1_desc" },
    { page: "/dashboard", anchor: "language-switch", titleKey: "step_lang_title", descKey: "step_lang_desc" },
    { page: "/dashboard", anchor: "notification-bell", openBell: true, titleKey: "step_bell_title", descKey: "step_bell_desc" },
    { page: "/expenses", anchor: "expenses-table", titleKey: "step_o2_title", descKey: "step_o2_desc" },
    { page: "/payments", anchor: "payments-table", titleKey: "step_o3_title", descKey: "step_o3_desc" },
    { page: "/notifications", anchor: "notifications-list", titleKey: "step_o4_title", descKey: "step_o4_desc" },
    { page: "/help", anchor: null, titleKey: "step_o_more_title", descKey: "step_o_more_desc" },
    { page: "/profile", anchor: "tutorial-profile-form", titleKey: "step_o5_title", descKey: "step_o5_desc" },
  ],
};

// ─────────────────────────────────────────────────────────────────────────────
// Zustand store
// ─────────────────────────────────────────────────────────────────────────────

export const useTutorialStore = create((set, get) => ({
  isActive: false,
  role: null,          // 'admin' | 'owner'
  currentStep: 0,

  startTutorial: (role) =>
    set({ isActive: true, role, currentStep: 0 }),

  nextStep: () => {
    const { currentStep, role } = get();
    const total = TUTORIAL_STEPS[role]?.length ?? 0;
    if (currentStep < total - 1) {
      set({ currentStep: currentStep + 1 });
    } else {
      get().endTutorial();
    }
  },

  prevStep: () => {
    const { currentStep } = get();
    if (currentStep > 0) set({ currentStep: currentStep - 1 });
  },

  endTutorial: () => set({ isActive: false, role: null, currentStep: 0 }),
}));

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const CARD_W = 340;
const CARD_H = 300; // upper bound of the real card height (varies with text length and language)
const MARGIN = 18;  // gap between anchor and card
const EDGE   = 12;  // minimum distance from viewport edge
const RING_PAD = 6; // padding around highlight ring

/** Returns { top, left } for the tooltip card so it never clips outside viewport. */
function calcCardPos(rect, vw, vh, isRTL = false, cardH = CARD_H) {
  if (!rect) {
    return { top: vh / 2 - cardH / 2, left: vw / 2 - CARD_W / 2 };
  }

  const candidates = isRTL
    ? [
        { top: rect.bottom + MARGIN, left: rect.right - CARD_W },          // below-right-aligned (RTL preferred)
        { top: rect.bottom + MARGIN, left: rect.left },                    // below-left-aligned
        { top: rect.top - cardH - MARGIN, left: rect.right - CARD_W },    // above-right-aligned
        { top: rect.top - cardH - MARGIN, left: rect.left },              // above-left-aligned
        { top: rect.top, left: rect.left - CARD_W - MARGIN },              // left
        { top: rect.top, left: rect.right + MARGIN },                      // right
      ]
    : [
        { top: rect.bottom + MARGIN, left: rect.left },                    // below
        { top: rect.top - cardH - MARGIN, left: rect.left },              // above
        { top: rect.top, left: rect.right + MARGIN },                      // right
        { top: rect.top, left: rect.left - CARD_W - MARGIN },              // left
        { top: rect.bottom + MARGIN, left: rect.right - CARD_W },          // below-right-aligned
        { top: rect.top - cardH - MARGIN, left: rect.right - CARD_W },    // above-right-aligned
      ];

  for (const pos of candidates) {
    if (
      pos.top >= EDGE &&
      pos.left >= EDGE &&
      pos.left + CARD_W <= vw - EDGE &&
      pos.top + cardH <= vh - EDGE
    ) {
      return pos;
    }
  }

  // Clamp fallback: whichever side of the anchor has more room, kept inside the viewport.
  const left = Math.max(EDGE, Math.min(isRTL ? rect.right - CARD_W : rect.left, vw - CARD_W - EDGE));
  const roomBelow = vh - rect.bottom - MARGIN - EDGE;
  const roomAbove = rect.top - MARGIN - EDGE;
  const top = roomBelow >= roomAbove
    ? Math.min(rect.bottom + MARGIN, vh - cardH - EDGE)
    : Math.max(EDGE, rect.top - cardH - MARGIN);
  return { top: Math.max(EDGE, top), left };
}

/** Waits for an element with id={anchorId} to appear in the DOM (max 2 s). */
function waitForElement(anchorId, maxWaitMs = 2000) {
  return new Promise((resolve) => {
    const el = document.getElementById(anchorId);
    if (el) { resolve(el); return; }

    const start = Date.now();
    const raf = () => {
      const found = document.getElementById(anchorId);
      if (found) { resolve(found); return; }
      if (Date.now() - start > maxWaitMs) { resolve(null); return; }
      requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const BELL_ID = "notification-bell";
const BELL_PANEL_ID = "notification-menu-panel";
const BELL_PANEL_MIN_VW = 600;

const isBellOpen = () => document.getElementById(BELL_ID)?.getAttribute("aria-expanded") === "true";

/** Closes the header notification popover if the tour opened it (Escape is handled by the MUI Popover). */
function closeBellMenu() {
  if (!isBellOpen()) return;
  const target = document.getElementById(BELL_PANEL_ID) ?? document.body;
  target.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", code: "Escape", keyCode: 27, bubbles: true }));
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

/** The green "Tutorial" button placed in the app header. */
export function TutorialButton() {
  const { isAdmin } = useAuth();
  const { isActive, startTutorial } = useTutorialStore();
  const { t } = useTranslation("tutorial");

  const handleClick = () => {
    startTutorial(isAdmin ? "admin" : "owner");
  };

  return (
    <Tooltip title={t("start_tour", "Start tour")}>
      <Button
        id="tutorial-btn"
        size="small"
        variant="contained"
        startIcon={<School sx={{ fontSize: 16 }} />}
        onClick={handleClick}
        disabled={isActive}
        sx={{
          bgcolor: "secondary.main",
          color: "secondary.contrastText",
          textTransform: "none",
          fontWeight: 600,
          fontSize: 13,
          px: 1.5,
          py: 0.5,
          mr: 1,
          borderRadius: 1.5,
          "&:hover": { bgcolor: "secondary.dark" },
          "&.Mui-disabled": { bgcolor: "secondary.main", opacity: 0.45, color: "secondary.contrastText" },
        }}
      >
        {t("tour_button", "Tour")}
      </Button>
    </Tooltip>
  );
}

/** Slim progress bar at the bottom of the tooltip card (dots overflow the card once there are many steps). */
function ProgressDots({ total, current }) {
  return (
    <Box
      role="progressbar"
      aria-valuemin={1}
      aria-valuemax={total}
      aria-valuenow={current + 1}
      sx={{ height: 6, width: 56, flexShrink: 0, borderRadius: 99, bgcolor: "divider", overflow: "hidden" }}
    >
      <Box
        style={{ width: `${((current + 1) / total) * 100}%` }}
        sx={{ height: "100%", borderRadius: 99, bgcolor: "primary.main", transition: "width 0.25s ease" }}
      />
    </Box>
  );
}

/** The floating tooltip card. */
function TutorialCard({ step, stepIndex, totalSteps, cardPos, cardRef, onNext, onPrev, onEnd }) {
  const { t } = useTranslation("tutorial");
  const isLast = stepIndex === totalSteps - 1;

  return (
    <Box
      ref={cardRef}
      style={{
        position: "fixed",
        top: cardPos.top,
        left: cardPos.left,
        width: CARD_W,
        transition: "top 0.3s ease, left 0.3s ease",
      }}
      sx={{
        zIndex: 10001,
        bgcolor: "background.paper",
        border: "0.5px solid",
        borderColor: "divider",
        borderRadius: 2.5,
        boxShadow: "0 20px 60px rgba(0,0,0,0.25)",
        p: 2.5,
      }}
    >
      {/* Step badge */}
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
        <Box
          sx={{
            px: 1,
            py: 0.25,
            bgcolor: "#EFF6FF",
            borderRadius: 1,
            display: "inline-flex",
            alignItems: "center",
          }}
        >
          <Typography
            sx={{ fontSize: 11, fontWeight: 700, color: "#1E40AF", letterSpacing: 0.5 }}
          >
            {t("common:step_counter", { current: stepIndex + 1, total: totalSteps })}
          </Typography>
        </Box>
        <IconButton size="small" onClick={onEnd} sx={{ mt: -0.5, mr: -0.75, color: "#6B7280" }}>
          <Close fontSize="small" />
        </IconButton>
      </Stack>

      {/* Title */}
      <Typography variant="h6" sx={{ fontWeight: 700, fontSize: 15, color: "#1F2937", mb: 0.75 }}>
        {t(step.titleKey)}
      </Typography>

      {/* Description */}
      <Typography variant="body2" sx={{ color: "#6B7280", lineHeight: 1.65, mb: 2 }}>
        {t(step.descKey)}
      </Typography>

      {/* Footer: dots + navigation */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
        <ProgressDots total={totalSteps} current={stepIndex} />
        <Stack direction="row" spacing={0.75}>
          {stepIndex > 0 && (
            <Button
              size="small"
              startIcon={<NavigateBefore />}
              onClick={onPrev}
              sx={{ textTransform: "none", color: "#6B7280", fontWeight: 500 }}
            >
              {t("common:back", "Back")}
            </Button>
          )}
          <Button
            size="small"
            variant="contained"
            endIcon={!isLast ? <NavigateNext /> : undefined}
            onClick={onNext}
            sx={{
              textTransform: "none",
              fontWeight: 600,
              bgcolor: "primary.main",
              "&:hover": { bgcolor: "primary.dark" },
              borderRadius: 1.5,
              px: 2,
            }}
          >
            {isLast ? t("common:finish", "Finish") : t("common:next", "Next")}
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main overlay (SVG mask + ring + card)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * TutorialOverlay — mount this ONCE inside <BrowserRouter> so it can call
 * useNavigate().  It renders into document.body via a portal so it always
 * sits above all other content regardless of CSS stacking contexts.
 */
export function TutorialOverlay() {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { i18n } = useTranslation();
  const {
    isActive, role, currentStep,
    nextStep, prevStep, endTutorial,
  } = useTutorialStore();

  const [anchorRect, setAnchorRect] = useState(null);
  const [cardPos, setCardPos]       = useState({ top: 0, left: 0 });
  const pendingNav = useRef(false);

  const steps = role ? TUTORIAL_STEPS[role] : [];
  const step  = steps[currentStep] ?? null;

  const isRTL = document.documentElement.dir === 'rtl' || document.body.dir === 'rtl';

  const lastBox = useRef("");
  const cardRef = useRef(null);
  const cardH = useRef(CARD_H); // measured height of the card, so it is placed without clipping

  /** Measure the anchor (optionally scrolling it into view) and position the ring and card. */
  const placeAnchor = useCallback((el, scroll) => {
    if (scroll) {
      el.scrollIntoView({ block: "center", inline: "nearest" });
      // A tall anchor (a long table) is brought to the top and only its top part is highlighted.
      if (el.getBoundingClientRect().height > window.innerHeight * 0.5) el.scrollIntoView({ block: "start", inline: "nearest" });
    }
    const full = el.getBoundingClientRect();
    lastBox.current = [full.top, full.left, full.width, full.height].map(Math.round).join();
    const maxH = Math.max(180, window.innerHeight * 0.35);
    const h = full.height > window.innerHeight * 0.5 ? maxH : full.height;
    const rect = { x: full.x, y: full.y, left: full.left, top: full.top, right: full.right, width: full.width, height: h, bottom: full.top + h };
    setAnchorRect(rect);
    setCardPos(calcCardPos(rect, window.innerWidth, window.innerHeight, isRTL, cardH.current));
  }, [isRTL]);

  /** Resolve the anchor element and compute positions. */
  const resolveAnchor = useCallback(async () => {
    if (!step) return;

    if (!step.anchor) {
      setAnchorRect(null);
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      setCardPos({ top: vh / 2 - CARD_H / 2, left: vw / 2 - CARD_W / 2 });
      return;
    }

    let anchorId = step.anchor;
    if (step.openBell) {
      if (window.innerWidth >= BELL_PANEL_MIN_VW) {
        if (!isBellOpen()) (await waitForElement(BELL_ID))?.click();
        anchorId = BELL_PANEL_ID;
      } else {
        closeBellMenu();
      }
    }

    const el = await waitForElement(anchorId);
    if (!el) {
      // Anchor not found — center the card
      setAnchorRect(null);
      setCardPos({ top: window.innerHeight / 2 - CARD_H / 2, left: window.innerWidth / 2 - CARD_W / 2 });
      return;
    }

    if (anchorId === BELL_PANEL_ID) {
      await sleep(300); // let the popover finish its open transition before measuring
      // The open MUI popover marks every other body child aria-hidden; keep the tour card reachable.
      document.getElementById("tutorial-root")?.removeAttribute("aria-hidden");
    }
    placeAnchor(el, anchorId !== BELL_PANEL_ID);
  }, [step, placeAnchor]);

  // Navigate whenever the step changes, then resolve the anchor.
  useEffect(() => {
    if (!isActive || !step) return;

    if (location.pathname !== step.page) {
      pendingNav.current = true;
      navigate(step.page);
    } else {
      resolveAnchor();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, currentStep, i18n.language]);

  // After navigation completes, resolve the anchor.
  useEffect(() => {
    if (!isActive || !pendingNav.current) return;
    pendingNav.current = false;
    resolveAnchor();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // Re-place the card once its real height is known (text length differs per step and language).
  useEffect(() => {
    const h = cardRef.current?.offsetHeight;
    if (h && Math.abs(h - cardH.current) > 1) {
      cardH.current = h;
      lastBox.current = ""; // makes the follow-up poll below re-place the card
    }
  });

  // Content often loads after the step opens (tables, cards) and moves the anchor: follow it.
  useEffect(() => {
    if (!isActive || !step?.anchor) return undefined;
    const timer = setInterval(() => {
      const id = step.openBell && window.innerWidth >= BELL_PANEL_MIN_VW ? BELL_PANEL_ID : step.anchor;
      const el = document.getElementById(id);
      if (!el) return;
      const r = el.getBoundingClientRect();
      if ([r.top, r.left, r.width, r.height].map(Math.round).join() !== lastBox.current) placeAnchor(el, id !== BELL_PANEL_ID);
    }, 300);
    return () => clearInterval(timer);
  }, [isActive, step, placeAnchor]);

  // Close the notification popover whenever the current step does not need it (or the tour ends).
  useEffect(() => {
    if (!isActive || !step?.openBell) closeBellMenu();
  }, [isActive, currentStep, step]);

  // Recompute on viewport resize.
  useEffect(() => {
    if (!isActive) return;
    const handler = () => resolveAnchor();
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, [isActive, resolveAnchor]);

  if (!isActive || !step) return null;

  // SVG mask rect values (with padding ring around anchor)
  const rx = anchorRect ? anchorRect.x - RING_PAD : 0;
  const ry = anchorRect ? anchorRect.y - RING_PAD : 0;
  const rw = anchorRect ? anchorRect.width + RING_PAD * 2 : 0;
  const rh = anchorRect ? anchorRect.height + RING_PAD * 2 : 0;

  return createPortal(
    <div id="tutorial-root">
      {/* Dark overlay with SVG spotlight cutout */}
      <svg
        style={{
          position: "fixed",
          inset: 0,
          width: "100%",
          height: "100%",
          zIndex: 9999,
          pointerEvents: "auto",
        }}
        onClick={endTutorial}
      >
        <defs>
          <mask id="tutorial-spotlight-mask">
            {/* White = overlay visible; black = transparent (the spotlight hole) */}
            <rect width="100%" height="100%" fill="white" />
            {anchorRect && (
              <rect
                x={rx}
                y={ry}
                width={rw}
                height={rh}
                fill="black"
                rx="6"
                style={{ transition: "x 0.3s ease, y 0.3s ease, width 0.3s ease, height 0.3s ease" }}
              />
            )}
          </mask>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="rgba(0,0,0,0.62)"
          mask="url(#tutorial-spotlight-mask)"
        />
      </svg>

      {/* Blue highlight ring around the anchor element.
          Uses inline style (not sx) so stylis-plugin-rtl does NOT flip
          left→right — the ring must use the same viewport coordinates
          as the SVG spotlight cutout regardless of document direction. */}
      {anchorRect && (
        <div
          style={{
            position: "fixed",
            top: ry,
            left: rx,
            width: rw,
            height: rh,
            borderRadius: 6,
            outline: `3px solid ${theme.palette.primary.main}`,
            outlineOffset: 0,
            boxShadow: `0 0 0 6px ${alpha(theme.palette.primary.main, 0.18)}`,
            zIndex: 10000,
            pointerEvents: "none",
            transition: "top 0.3s ease, left 0.3s ease, width 0.3s ease, height 0.3s ease",
          }}
        />
      )}

      {/* Tooltip card — stops click propagation so overlay doesn't close */}
      <Box onClick={(e) => e.stopPropagation()} sx={{ zIndex: 10001 }}>
        <TutorialCard
          step={step}
          stepIndex={currentStep}
          totalSteps={steps.length}
          cardPos={cardPos}
          cardRef={cardRef}
          onNext={nextStep}
          onPrev={prevStep}
          onEnd={endTutorial}
        />
      </Box>
    </div>,
    document.body
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Convenience default export — renders both the role picker and the overlay
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Mount <TutorialSystem /> once inside your router to activate the full
 * tutorial system (spotlight overlay). Role is auto-detected from useAuth().
 */
export default function TutorialSystem() {
  return <TutorialOverlay />;
}
