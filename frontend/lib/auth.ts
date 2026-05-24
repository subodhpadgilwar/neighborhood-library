import type { StaffResponse } from "@/types";

const TOKEN_KEY = "library_token";
const STAFF_KEY = "library_staff";

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
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
