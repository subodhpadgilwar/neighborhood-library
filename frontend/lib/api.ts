import axios, { type AxiosError } from "axios";

import { removeToken } from "@/lib/auth";
import type { ApiError } from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("library_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      removeToken();
      window.location.href = "/login";
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
