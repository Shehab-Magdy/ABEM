import createCache from "@emotion/cache";
import rtlPlugin from "stylis-plugin-rtl";
import { prefixer } from "stylis";

/**
 * Create a fresh Emotion cache for the given direction.
 * Must create a NEW cache on every direction switch so Emotion
 * re-processes all CSS through the correct stylis plugins.
 * Reusing a static cache does not flush old LTR/RTL styles.
 */
export function createDirectionCache(dir) {
  if (dir === "rtl") {
    return createCache({
      key: "muirtl",
      stylisPlugins: [prefixer, rtlPlugin],
    });
  }
  return createCache({ key: "css" });
}
