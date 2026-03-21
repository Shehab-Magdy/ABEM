/**
 * T-01 -- Global hook that enables Eastern Arabic-Indic digit input
 * (٠١٢٣٤٥٦٧٨٩) in all number-related fields.
 *
 * How it works:
 *   - Listens for `beforeinput` on the document (capture phase).
 *   - When the user types an Eastern Arabic digit into an <input> whose
 *     type is "number" or "text" (with inputMode "decimal"/"numeric"),
 *     the event is cancelled and the corresponding ASCII digit is inserted
 *     programmatically via `execCommand("insertText")`.
 *   - This avoids the browser rejecting Eastern Arabic digits in
 *     `type="number"` fields while still firing React's synthetic
 *     onChange as expected.
 *
 * Mount once at the app root (e.g. in App.jsx).
 * The listener is only active when the current language is Arabic.
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

    /**
     * `beforeinput` fires before the browser inserts text.  By cancelling
     * it and re-inserting the converted ASCII digit via execCommand we
     * bypass the browser's native validation for type="number" inputs,
     * while still triggering React's onChange through the normal DOM path.
     */
    const handler = (e) => {
      if (e.inputType !== "insertText" && e.inputType !== "insertCompositionText") return;
      const el = e.target;
      if (!isNumericInput(el)) return;
      if (!e.data || !EASTERN_ARABIC_TEST.test(e.data)) return;

      // Convert all Eastern Arabic digits in the inserted chunk
      const converted = e.data.replaceAll(EASTERN_ARABIC_REPLACE, toAsciiDigit);
      e.preventDefault();
      // insertText fires input/change events normally so React picks it up
      document.execCommand("insertText", false, converted);
    };

    document.addEventListener("beforeinput", handler, true);
    return () => document.removeEventListener("beforeinput", handler, true);
  }, [isArabic]);
}
