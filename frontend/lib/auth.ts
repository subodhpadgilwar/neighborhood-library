import type { StaffResponse } from "@/types";

/**
 * Token storage has moved to an HttpOnly cookie set by the Next.js
 * /api/auth/login route handler. These helpers now only manage the
 * in-memory staff profile cache used for display purposes only.
 * No authorization decisions should be made from this cache.
 */

const STAFF_KEY = "library_staff";

/**
 * Returns cached staff profile for DISPLAY PURPOSES ONLY.
 * Never use this for authorization or role checks.
 * Role-gated UI must read from AuthContext (useAuth().staff).
 */
export function getStoredStaff(): StaffResponse | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STAFF_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StaffResponse;
  } catch {
    return null;
  }
}

export function setStoredStaff(staff: StaffResponse): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STAFF_KEY, JSON.stringify(staff));
}

export function removeStoredStaff(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STAFF_KEY);
}

/** @deprecated Token is now HttpOnly — always returns true if the server
 *  has set the cookie. Use AuthContext.isAuthenticated for UI decisions. */
export function isAuthenticated(): boolean {
  // Cannot read HttpOnly cookies from JS. This function is kept for
  // backward compatibility only. Do not use for authorization checks.
  return false;
}

// Legacy exports kept so existing imports do not break.
// They are no-ops because the token is managed server-side.
export const getToken = () => null;
export const setToken = (_: string) => {};
export const removeToken = () => {};
