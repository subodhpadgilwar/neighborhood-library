/**
 * Centralized API constants used across the frontend.
 *
 * - Client-side calls always go through the Next.js proxy at `/api/proxy/*`.
 * - Next.js server-side route handlers proxy to the backend under `/api/v1/*`.
 */

/** Next.js proxy route base (client -> Next.js) */
export const PROXY_BASE_PATH = "/api/proxy";

/** Next.js auth route handlers (client -> Next.js) */
export const NEXT_AUTH_ROUTES = {
  login: "/api/auth/login",
  logout: "/api/auth/logout",
} as const;

/** Backend API prefix (Next.js server -> backend) */
export const BACKEND_API_V1_PREFIX = "/api/v1";

