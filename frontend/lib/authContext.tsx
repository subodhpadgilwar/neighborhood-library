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

import {
  getToken,
  removeStoredStaff,
  removeToken,
  setStoredStaff,
  setToken,
} from "@/lib/auth";
import { authService } from "@/services";
import type { StaffResponse } from "@/types";

interface AuthContextValue {
  staff: StaffResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
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
      const token = getToken();
      if (!token) {
        if (!cancelled) {
          setStaff(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        const me = await authService.getMe();
        if (!cancelled) {
          setStaff(me);
          setStoredStaff(me);
        }
      } catch {
        if (!cancelled) {
          removeToken();
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
    const { access_token } = await authService.login(email, password);
    setToken(access_token);
    const me = await authService.getMe();
    setStaff(me);
    setStoredStaff(me);
  }, []);

  const logout = useCallback(() => {
    removeToken();
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
