/**
 * T-01 -- Global hook that enables Eastern Arabic-Indic digit input
 * (٠١٢٣٤٥٦٧٨٩) in all number-related fields.
 *
 * Two-layer approach:
 *
 * 1. `beforeinput` (inline conversion — best UX)
 *    Listens for `beforeinput` on the document (capture phase).
 *    When the user types an Eastern Arabic digit into a numeric <input>,
 *    the event is cancelled and the corresponding ASCII digit is inserted
 *    programmatically via `execCommand("insertText")`.
 *    This avoids the browser rejecting Eastern Arabic digits in
 *    `type="number"` fields while still firing React's synthetic
 *    onChange as expected. Digits appear as ASCII immediately.
 *
 * 2. `focusout` (blur safety net)
 *    Listens for `focusout` on the document (capture phase).
 *    When a numeric input loses focus, if any Eastern Arabic digits
 *    remain in its value (e.g. from paste, autofill, or a browser that
 *    didn't fire beforeinput), they are converted to ASCII and a
 *    React-compatible input event is dispatched so state stays in sync.
 *
 * Mount once at the app root (e.g. in App.jsx).
 * Both listeners are only active when the current language is Arabic.
 */
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

/** Regex without `g` for testing (avoids stateful lastIndex). */
const EASTERN_ARABIC_TEST = /[٠-٩]/;
/** Regex with `g` for replaceAll. */
const EASTERN_ARABIC_REPLACE = /[٠-٩]/g;

function toAsciiDigit(ch) {
  return String(ch.codePointAt(0) - 0x0660);
}

function isNumericInput(el) {
  if (el.tagName !== "INPUT") return false;
  if (el.type === "number") return true;
  if (
    el.type === "text" &&
    (el.inputMode === "decimal" || el.inputMode === "numeric")
  ) {
    return true;
  }
  // Also accept fields explicitly opted-in via a data attribute
  if (el.dataset.acceptArabicDigits != null) return true;
  return false;
}

export function useEasternArabicInput() {
  const { i18n } = useTranslation();
  const isArabic = (i18n.language || "en").startsWith("ar");

  useEffect(() => {
    if (!isArabic) return;

    // ── Layer 1: beforeinput — inline conversion as the user types ───────
    const beforeInputHandler = (e) => {
      if (
        e.inputType !== "insertText" &&
        e.inputType !== "insertCompositionText"
      )
        return;
      const el = e.target;
      if (!isNumericInput(el)) return;
      if (!e.data || !EASTERN_ARABIC_TEST.test(e.data)) return;

      // Convert all Eastern Arabic digits in the inserted chunk
      const converted = e.data.replaceAll(EASTERN_ARABIC_REPLACE, toAsciiDigit);
      e.preventDefault();
      // insertText fires input/change events normally so React picks it up
      document.execCommand("insertText", false, converted);
    };

    // ── Layer 2: focusout — catch anything that slipped through ──────────
    const focusOutHandler = (e) => {
      const el = e.target;
      if (!isNumericInput(el)) return;

      const raw = el.value;
      if (!raw || !EASTERN_ARABIC_TEST.test(raw)) return;

      const converted = raw.replaceAll(EASTERN_ARABIC_REPLACE, toAsciiDigit);

      // Use the native setter to bypass React's synthetic value tracking,
      // then dispatch an input event so React state updates.
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        globalThis.HTMLInputElement.prototype,
        "value"
      ).set;
      nativeInputValueSetter.call(el, converted);
      el.dispatchEvent(new Event("input", { bubbles: true }));
    };

    document.addEventListener("beforeinput", beforeInputHandler, true);
    document.addEventListener("focusout", focusOutHandler, true);

    return () => {
      document.removeEventListener("beforeinput", beforeInputHandler, true);
      document.removeEventListener("focusout", focusOutHandler, true);
    };
  }, [isArabic]);
}
