import type { StaffResponse } from "@/types";

const TOKEN_KEY = "library_token";
const STAFF_KEY = "library_staff";
/** Matches backend ACCESS_TOKEN_EXPIRE_MINUTES (480) */
const TOKEN_MAX_AGE_SECONDS = 480 * 60;

function setAuthCookie(token: string): void {
  document.cookie = `${TOKEN_KEY}=${encodeURIComponent(token)}; path=/; max-age=${TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
}

function clearAuthCookie(): void {
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
}

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(TOKEN_KEY, token);
  setAuthCookie(token);
}

export function removeToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
  clearAuthCookie();
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export function getStoredStaff(): StaffResponse | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = localStorage.getItem(STAFF_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as StaffResponse;
  } catch {
    return null;
  }
}

export function setStoredStaff(staff: StaffResponse): void {
  localStorage.setItem(STAFF_KEY, JSON.stringify(staff));
}

export function removeStoredStaff(): void {
  localStorage.removeItem(STAFF_KEY);
}
