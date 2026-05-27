import axios, { type AxiosError } from "axios";
import type { ApiError } from "@/types";
import { PROXY_BASE_PATH } from "@/lib/apiConfig";

/**
 * All API calls go through the Next.js proxy route at /api/proxy/*.
 * The proxy attaches the HttpOnly cookie token as a Bearer header.
 * No token or backend URL is ever exposed to client-side JavaScript.
 */
export const api = axios.create({
  baseURL: PROXY_BASE_PATH,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const onLoginPage = window.location.pathname.startsWith("/login");
      if (!onLoginPage) {
        window.location.href = "/login";
      }
    }

    const data = error.response?.data;
    const message =
      data && typeof data.message === "string"
        ? data.message
        : "An unexpected error occurred";
    const status =
      data && typeof data.status === "string" ? data.status : "error";

    return Promise.reject({ status, message });
  },
);
