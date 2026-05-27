"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";

import { removeStoredStaff, setStoredStaff } from "@/lib/auth";
import { NEXT_AUTH_ROUTES } from "@/lib/apiConfig";
import { authService } from "@/services";
import type { StaffResponse } from "@/types";

interface AuthContextValue {
  staff: StaffResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [staff, setStaff] = useState<StaffResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    let cancelled = false;

    async function loadSession() {
      try {
        const me = await authService.getMe();
        if (!cancelled) {
          setStaff(me);
          setStoredStaff(me);
        }
      } catch {
        if (!cancelled) {
          removeStoredStaff();
          setStaff(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!isLoading && staff !== null && pathname === "/login") {
      router.replace("/");
    }
  }, [isLoading, staff, pathname, router]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(NEXT_AUTH_ROUTES.login, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(
        typeof err.message === "string" ? err.message : "Login failed",
      );
    }
    const me = await authService.getMe();
    setStaff(me);
    setStoredStaff(me);
  }, []);

  const logout = useCallback(async () => {
    await fetch(NEXT_AUTH_ROUTES.logout, { method: "POST" }).catch(() => {});
    removeStoredStaff();
    setStaff(null);
    router.push("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      staff,
      isAuthenticated: staff !== null,
      isLoading,
      login,
      logout,
    }),
    [staff, isLoading, login, logout],
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
