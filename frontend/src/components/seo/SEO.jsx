import { Helmet } from "react-helmet-async";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { BRAND } from "../../brand";

const SITE_URL = BRAND.siteUrl;
const DEFAULT_OG_IMAGE = "/og-image.png";

/**
 * Reusable SEO component for public-facing pages.
 * Adds title, meta description, Open Graph, Twitter Card, canonical, and robots tags.
 */
export function PublicSEO({ title, description, children }) {
  const { pathname } = useLocation();
  const canonicalUrl = `${SITE_URL}${pathname}`;

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={BRAND.keywords} />
      <meta name="robots" content="index, follow" />
      <link rel="canonical" href={canonicalUrl} />

      {/* Open Graph */}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content={BRAND.combined} />
      <meta property="og:locale" content="ar_EG" />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:image" content={`${SITE_URL}${DEFAULT_OG_IMAGE}`} />

      {/* Twitter Card */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />

      {children}
    </Helmet>
  );
}

// Route -> common.json key, so private page titles follow the UI language.
const ROUTE_TITLE_KEYS = {
  "/dashboard": "dashboard",
  "/buildings": "buildings",
  "/expenses": "expenses",
  "/payments": "payments",
  "/operations": "operations",
  "/records": "records",
  "/board": "board",
  "/polls": "polls",
  "/statement": "statement",
  "/maintenance": "maintenance",
  "/notifications": "notifications",
  "/users": "users",
  "/expense-categories": "categories",
  "/subscription": "subscription",
  "/assets": "assets",
  "/plan": "plan",
  "/platform": "platform",
  "/profile": "profile",
  "/help": "help",
};

/**
 * SEO component for authenticated (private) pages.
 * Prevents indexing; the title is localized from the route (falls back to the given title).
 */
export function PrivateSEO({ title }) {
  const { pathname } = useLocation();
  const { t, i18n } = useTranslation("common");
  const key = ROUTE_TITLE_KEYS["/" + pathname.split("/")[1]];
  const isAr = (i18n.language || "en").startsWith("ar");
  const brand = isAr ? BRAND.nameAr : BRAND.nameEn;
  const pageTitle = key ? `${brand} – ${t(key)}` : isAr ? brand : title;
  return (
    <Helmet>
      <title>{pageTitle}</title>
      <meta name="robots" content="noindex, nofollow" />
    </Helmet>
  );
}
