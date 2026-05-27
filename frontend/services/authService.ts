import { api } from "@/lib/api";
import { apiPaths } from "@/lib/apiPaths";
import type { StaffResponse } from "@/types";

export async function getMe(): Promise<StaffResponse> {
  const { data } = await api.get<StaffResponse>(apiPaths.auth.me);
  return data;
}
