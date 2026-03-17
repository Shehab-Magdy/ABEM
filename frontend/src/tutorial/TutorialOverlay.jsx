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
 *      TUTORIAL_ANCHORS.md.  Search the codebase for those ids before removing
 *      or renaming elements.
 *
 *   4. To trigger the tutorial programmatically from anywhere:
 *        import { useTutorialStore } from '../tutorial/TutorialOverlay';
 *        useTutorialStore.getState().openRolePicker();
 */

import { useEffect, useRef, useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate, useLocation } from "react-router-dom";
import { create } from "zustand";
import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { Close, NavigateBefore, NavigateNext, School } from "@mui/icons-material";

// ─────────────────────────────────────────────────────────────────────────────
// Step definitions
// ─────────────────────────────────────────────────────────────────────────────

/** @type {Record<'admin'|'owner', Array<{page:string, anchor:string|null, title:string, description:string}>>} */
export const TUTORIAL_STEPS = {
  admin: [
    {
      page: "/dashboard",
      anchor: null,
      title: "Welcome to ABEM",
      description:
        "The dashboard shows total income, total expenses, count of overdue units, and the number of buildings managed — all scoped to the currently selected building and refreshed in real time.",
    },
    {
      page: "/buildings",
      anchor: "add-building-btn",
      title: "Create your first building",
      description:
        "Every workflow starts here. Click \"+ New Building\" to enter the property address, number of floors, apartments, and stores. Each building is fully data-isolated — expenses and balances never mix between buildings.",
    },
    {
      page: "/buildings",
      anchor: "building-actions-row",
      title: "What you can do with a building",
      description:
        "Edit details, manage units (invite/claim), assign owners, activate/deactivate, or delete. Delete performs a soft-delete — records are preserved and visible in the audit log.",
    },
    {
      page: "/expenses",
      anchor: "add-expense-btn",
      title: "Add a shared expense",
      description:
        "Any cost shared across apartments lives here. Select a category, enter the amount, and choose the split method: equally across all units, apartments only, stores only, or a custom weighted subset. Every share is rounded up to the nearest 5 EGP.",
    },
    {
      page: "/expenses",
      anchor: "expense-actions-btn",
      title: "Expense actions explained",
      description:
        "Edit changes amount, category, or description. The detail panel shows a per-unit share breakdown before any notifications go out. Delete removes the expense and reverses outstanding balances — a full audit entry is written for compliance.",
    },
    {
      page: "/users",
      anchor: "add-user-btn",
      title: "Manage users",
      description:
        "Create Admin or Owner accounts here. Admins have full CRUD access. Owners see only their own apartment data. \"Deactivate\" blocks a user's login immediately without deleting payment or expense history — critical for compliance.",
    },
    {
      page: "/expense-categories",
      anchor: "categories-table",
      title: "Expense categories",
      description:
        "ABEM ships with 15 built-in categories. Each has a Material icon, hex color, and optional subcategory hierarchy. Custom categories can be added for building-specific needs.",
    },
    {
      page: "/assets",
      anchor: "assets-table",
      title: "Building assets",
      description:
        "Track physical equipment — elevators, generators, pumps, CCTV. Each asset carries a type, acquisition date, and value. When sold, record buyer details and sale price to maintain a complete asset ledger.",
    },
    {
      page: "/audit",
      anchor: "audit-table",
      title: "Audit log",
      description:
        "Every write action is logged automatically with the actor, action type, affected entity, and timestamp. Admins cannot edit or delete audit entries. Use this screen for financial compliance, dispute resolution, and accountability.",
    },
  ],
  owner: [
    {
      page: "/dashboard",
      anchor: null,
      title: "Your personal overview",
      description:
        "This dashboard is scoped to your unit only. You see your current outstanding balance, most recent payments, and any new expenses the admin has assigned to your unit.",
    },
    {
      page: "/expenses",
      anchor: "expenses-table",
      title: "Your shared expenses",
      description:
        "Every building expense that includes your unit in the split appears here. Each row shows the total building cost, your individual share, and the current payment status. Only the admin can add or modify expenses.",
    },
    {
      page: "/payments",
      anchor: "payments-table",
      title: "Your payment history",
      description:
        "Every payment the admin records for your unit is shown here in reverse-chronological order — amount, method, date, and running balance. Click Receipt to download a PDF for any transaction.",
    },
    {
      page: "/notifications",
      anchor: "notifications-list",
      title: "Notifications centre",
      description:
        "You receive alerts when the admin records a payment for your unit, when a new expense is posted, and for broadcast announcements. Mark individual notifications as read from this list.",
    },
    {
      page: "/profile",
      anchor: "profile-card",
      title: "Your profile",
      description:
        "Update your display name, phone number, or password here. Your email address and role are set by the admin — contact them if either needs to change.",
    },
  ],
};

// ─────────────────────────────────────────────────────────────────────────────
// Zustand store
// ─────────────────────────────────────────────────────────────────────────────

export const useTutorialStore = create((set, get) => ({
  isActive: false,
  isRolePicking: false,
  role: null,          // 'admin' | 'owner'
  currentStep: 0,

  openRolePicker: () => set({ isRolePicking: true }),
  closeRolePicker: () => set({ isRolePicking: false }),

  startTutorial: (role) =>
    set({ isActive: true, isRolePicking: false, role, currentStep: 0 }),

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
const CARD_H = 220; // approximate; real height varies
const MARGIN = 18;  // gap between anchor and card
const EDGE   = 12;  // minimum distance from viewport edge
const RING_PAD = 6; // padding around highlight ring

/** Returns { top, left } for the tooltip card so it never clips outside viewport. */
function calcCardPos(rect, vw, vh) {
  if (!rect) {
    return { top: vh / 2 - CARD_H / 2, left: vw / 2 - CARD_W / 2 };
  }

  const candidates = [
    { top: rect.bottom + MARGIN, left: rect.left },                    // below
    { top: rect.top - CARD_H - MARGIN, left: rect.left },              // above
    { top: rect.top, left: rect.right + MARGIN },                      // right
    { top: rect.top, left: rect.left - CARD_W - MARGIN },              // left
    { top: rect.bottom + MARGIN, left: rect.right - CARD_W },          // below-right-aligned
    { top: rect.top - CARD_H - MARGIN, left: rect.right - CARD_W },    // above-right-aligned
  ];

  for (const pos of candidates) {
    if (
      pos.top >= EDGE &&
      pos.left >= EDGE &&
      pos.left + CARD_W <= vw - EDGE &&
      pos.top + CARD_H <= vh - EDGE
    ) {
      return pos;
    }
  }

  // Clamp fallback
  return {
    top: Math.max(EDGE, Math.min(rect.bottom + MARGIN, vh - CARD_H - EDGE)),
    left: Math.max(EDGE, Math.min(rect.left, vw - CARD_W - EDGE)),
  };
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

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

/** The green "Tutorial" button placed in the app header. */
export function TutorialButton() {
  const openRolePicker = useTutorialStore((s) => s.openRolePicker);
  const isActive = useTutorialStore((s) => s.isActive);

  return (
    <Tooltip title="Start tour">
      <Button
        id="tutorial-btn"
        size="small"
        variant="contained"
        startIcon={<School sx={{ fontSize: 16 }} />}
        onClick={openRolePicker}
        disabled={isActive}
        sx={{
          bgcolor: "#10B981",
          color: "white",
          textTransform: "none",
          fontWeight: 600,
          fontSize: 13,
          px: 1.5,
          py: 0.5,
          mr: 1,
          borderRadius: 1.5,
          "&:hover": { bgcolor: "#059669" },
          "&.Mui-disabled": { bgcolor: "#10B981", opacity: 0.45, color: "white" },
        }}
      >
        Tour
      </Button>
    </Tooltip>
  );
}

/** Role-picker modal — shown before the tour starts. */
function RolePickerModal() {
  const { isRolePicking, closeRolePicker, startTutorial } = useTutorialStore();

  return (
    <Dialog
      open={isRolePicking}
      onClose={closeRolePicker}
      maxWidth="xs"
      fullWidth
      PaperProps={{ sx: { borderRadius: 3, p: 1 } }}
    >
      <DialogTitle sx={{ fontWeight: 700, fontSize: 18, pb: 0.5 }}>
        Choose a tour
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
          Select the role you want to explore. The tour will navigate the app
          step by step and highlight key features.
        </Typography>
        <Stack spacing={1.5}>
          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={() => startTutorial("admin")}
            sx={{
              bgcolor: "#2563EB",
              fontWeight: 600,
              textTransform: "none",
              borderRadius: 2,
              py: 1.5,
              "&:hover": { bgcolor: "#1D4ED8" },
            }}
          >
            Admin tour — 9 steps
          </Button>
          <Button
            fullWidth
            variant="outlined"
            size="large"
            onClick={() => startTutorial("owner")}
            sx={{
              borderColor: "#2563EB",
              color: "#2563EB",
              fontWeight: 600,
              textTransform: "none",
              borderRadius: 2,
              py: 1.5,
              "&:hover": { bgcolor: "#EFF6FF", borderColor: "#1D4ED8" },
            }}
          >
            Owner tour — 5 steps
          </Button>
        </Stack>
      </DialogContent>
    </Dialog>
  );
}

/** Progress dots row at the bottom of the tooltip card. */
function ProgressDots({ total, current }) {
  return (
    <Stack direction="row" spacing={0.5} alignItems="center">
      {Array.from({ length: total }).map((_, i) => (
        <Box
          key={i}
          sx={{
            height: 6,
            borderRadius: 99,
            bgcolor: i === current ? "#2563EB" : "#CBD5E1",
            width: i === current ? 18 : 6,
            transition: "all 0.25s ease",
          }}
        />
      ))}
    </Stack>
  );
}

/** The floating tooltip card. */
function TutorialCard({ step, stepIndex, totalSteps, cardPos, onNext, onPrev, onEnd }) {
  const isLast = stepIndex === totalSteps - 1;

  return (
    <Box
      sx={{
        position: "fixed",
        top: cardPos.top,
        left: cardPos.left,
        width: CARD_W,
        zIndex: 10001,
        bgcolor: "white",
        border: "0.5px solid #E5E7EB",
        borderRadius: 2.5,
        boxShadow: "0 20px 60px rgba(0,0,0,0.25)",
        p: 2.5,
        transition: "top 0.3s ease, left 0.3s ease",
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
            STEP {stepIndex + 1} OF {totalSteps}
          </Typography>
        </Box>
        <IconButton size="small" onClick={onEnd} sx={{ mt: -0.5, mr: -0.75, color: "#6B7280" }}>
          <Close fontSize="small" />
        </IconButton>
      </Stack>

      {/* Title */}
      <Typography variant="h6" sx={{ fontWeight: 700, fontSize: 15, color: "#1F2937", mb: 0.75 }}>
        {step.title}
      </Typography>

      {/* Description */}
      <Typography variant="body2" sx={{ color: "#6B7280", lineHeight: 1.65, mb: 2 }}>
        {step.description}
      </Typography>

      {/* Footer: dots + navigation */}
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <ProgressDots total={totalSteps} current={stepIndex} />
        <Stack direction="row" spacing={0.75}>
          {stepIndex > 0 && (
            <Button
              size="small"
              startIcon={<NavigateBefore />}
              onClick={onPrev}
              sx={{ textTransform: "none", color: "#6B7280", fontWeight: 500 }}
            >
              Back
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
              bgcolor: "#2563EB",
              "&:hover": { bgcolor: "#1D4ED8" },
              borderRadius: 1.5,
              px: 2,
            }}
          >
            {isLast ? "Finish" : "Next"}
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
  const navigate = useNavigate();
  const location = useLocation();
  const {
    isActive, role, currentStep,
    nextStep, prevStep, endTutorial,
  } = useTutorialStore();

  const [anchorRect, setAnchorRect] = useState(null);
  const [cardPos, setCardPos]       = useState({ top: 0, left: 0 });
  const pendingNav = useRef(false);

  const steps = role ? TUTORIAL_STEPS[role] : [];
  const step  = steps[currentStep] ?? null;

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

    const el = await waitForElement(step.anchor);
    if (!el) {
      // Anchor not found — center the card
      setAnchorRect(null);
      setCardPos({ top: window.innerHeight / 2 - CARD_H / 2, left: window.innerWidth / 2 - CARD_W / 2 });
      return;
    }

    const rect = el.getBoundingClientRect();
    setAnchorRect(rect);
    setCardPos(calcCardPos(rect, window.innerWidth, window.innerHeight));
  }, [step]);

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
  }, [isActive, currentStep]);

  // After navigation completes, resolve the anchor.
  useEffect(() => {
    if (!isActive || !pendingNav.current) return;
    pendingNav.current = false;
    resolveAnchor();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // Recompute on viewport resize.
  useEffect(() => {
    if (!isActive) return;
    const handler = () => resolveAnchor();
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, [isActive, resolveAnchor]);

  if (!isActive || !step) return null;

  const vw = window.innerWidth;
  const vh = window.innerHeight;

  // SVG mask rect values (with padding ring around anchor)
  const rx = anchorRect ? anchorRect.x - RING_PAD : 0;
  const ry = anchorRect ? anchorRect.y - RING_PAD : 0;
  const rw = anchorRect ? anchorRect.width + RING_PAD * 2 : 0;
  const rh = anchorRect ? anchorRect.height + RING_PAD * 2 : 0;

  return createPortal(
    <>
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

      {/* Blue highlight ring around the anchor element */}
      {anchorRect && (
        <Box
          sx={{
            position: "fixed",
            top: ry,
            left: rx,
            width: rw,
            height: rh,
            borderRadius: "6px",
            outline: "3px solid #2563EB",
            outlineOffset: "0px",
            boxShadow: "0 0 0 6px rgba(37,99,235,0.18)",
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
          onNext={nextStep}
          onPrev={prevStep}
          onEnd={endTutorial}
        />
      </Box>
    </>,
    document.body
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Convenience default export — renders both the role picker and the overlay
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Mount <TutorialSystem /> once inside your router to activate the full
 * tutorial system (role picker modal + spotlight overlay).
 */
export default function TutorialSystem() {
  return (
    <>
      <RolePickerModal />
      <TutorialOverlay />
    </>
  );
}
