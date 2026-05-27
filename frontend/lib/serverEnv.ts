/**
 * Backend URL used ONLY in Next.js server-side code (Route Handlers,
 * Server Components, middleware). Never imported in client components.
 * Falls back to localhost for local dev without Docker.
 */
export const INTERNAL_API_URL =
  process.env.INTERNAL_API_URL ?? "http://localhost:8000";

export const COOKIE_SECURE = process.env.NODE_ENV === "production";

export const COOKIE_SAMESITE: "lax" | "strict" | "none" = "lax";

/** Matches backend ACCESS_TOKEN_EXPIRE_MINUTES (480 minutes) */
export const TOKEN_MAX_AGE_SECONDS = 480 * 60;
