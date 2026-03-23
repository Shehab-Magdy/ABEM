#!/usr/bin/env node
/**
 * Translation key completeness checker for ABEM i18n.
 *
 * Reads all en/*.json and ar/*.json translation files and asserts that
 * every key present in en/ also exists in ar/ (and vice versa).
 * Reports missing keys with file name and key path.
 * Exits with code 1 if any key is missing.
 *
 * Usage:  node scripts/check_translations.js
 */

const fs = require("fs");
const path = require("path");

const LOCALES_DIR = path.join(__dirname, "..", "frontend", "public", "locales");
const LANGS = ["en", "ar"];

function getJsonFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => f.endsWith(".json")).sort();
}

function flattenKeys(obj, prefix = "") {
  const keys = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === "object" && !Array.isArray(value)) {
      keys.push(...flattenKeys(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

let errors = 0;

// Check that both directories exist
for (const lang of LANGS) {
  const dir = path.join(LOCALES_DIR, lang);
  if (!fs.existsSync(dir)) {
    console.error(`ERROR: Locale directory missing: ${dir}`);
    process.exit(1);
  }
}

// Check that en/ and ar/ have the same files
const enFiles = getJsonFiles(path.join(LOCALES_DIR, "en"));
const arFiles = getJsonFiles(path.join(LOCALES_DIR, "ar"));

for (const f of enFiles) {
  if (!arFiles.includes(f)) {
    console.error(`MISSING FILE: ar/${f} (exists in en/)`);
    errors++;
  }
}
for (const f of arFiles) {
  if (!enFiles.includes(f)) {
    console.error(`EXTRA FILE: ar/${f} (does not exist in en/)`);
    errors++;
  }
}

// Check key parity in each file
const commonFiles = enFiles.filter((f) => arFiles.includes(f));
for (const file of commonFiles) {
  const enData = JSON.parse(
    fs.readFileSync(path.join(LOCALES_DIR, "en", file), "utf-8")
  );
  const arData = JSON.parse(
    fs.readFileSync(path.join(LOCALES_DIR, "ar", file), "utf-8")
  );

  const enKeys = new Set(flattenKeys(enData));
  const arKeys = new Set(flattenKeys(arData));

  for (const key of enKeys) {
    if (!arKeys.has(key)) {
      console.error(`MISSING KEY: ar/${file} is missing "${key}"`);
      errors++;
    }
  }
  // i18next Arabic pluralization uses _zero, _one, _two, _few, _many, _other
  // English only needs _one and _other, so Arabic may have extra plural keys
  // that are valid and expected.  Only flag a key as extra if it is NOT an
  // Arabic plural variant of an English base key.
  const PLURAL_SUFFIXES = ["_zero", "_one", "_two", "_few", "_many", "_other"];
  for (const key of arKeys) {
    if (!enKeys.has(key)) {
      const isArabicPlural = PLURAL_SUFFIXES.some((suffix) => {
        if (!key.endsWith(suffix)) return false;
        const base = key.slice(0, -suffix.length);
        // Accept if en/ has ANY plural form of the same base
        return PLURAL_SUFFIXES.some((s) => enKeys.has(base + s));
      });
      if (!isArabicPlural) {
        console.error(`EXTRA KEY: ar/${file} has extra "${key}" (not in en/)`);
        errors++;
      }
    }
  }
}

if (errors > 0) {
  console.error(`\n${errors} translation issue(s) found. Fix before merging.`);
  process.exit(1);
} else {
  console.log(
    `All ${commonFiles.length} translation files verified — en/ and ar/ keys match.`
  );
  process.exit(0);
}
