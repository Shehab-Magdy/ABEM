import { Helmet } from "react-helmet-async";
import { useLocation } from "react-router-dom";

const SITE_URL = "https://abem.app";
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
      <meta name="robots" content="index, follow" />
      <link rel="canonical" href={canonicalUrl} />

      {/* Open Graph */}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="website" />
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

/**
 * SEO component for authenticated (private) pages.
 * Prevents indexing and adds a simple title.
 */
export function PrivateSEO({ title }) {
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="robots" content="noindex, nofollow" />
    </Helmet>
  );
}
