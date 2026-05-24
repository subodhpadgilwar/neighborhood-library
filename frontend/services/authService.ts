import { api } from "@/lib/api";
import type { StaffResponse, TokenResponse } from "@/types";

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const { data } = await api.post<TokenResponse>("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function getMe(): Promise<StaffResponse> {
  const { data } = await api.get<StaffResponse>("/auth/me");
  return data;
}
