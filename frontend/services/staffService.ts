import { api } from "@/lib/api";
import type {
  AdminChangePasswordRequest,
  ChangePasswordRequest,
  Staff,
  StaffCreate,
  StaffUpdate,
} from "@/types";

export async function getAll(includeInactive = false): Promise<Staff[]> {
  const { data } = await api.get<Staff[]>("/staff", {
    params: { include_inactive: includeInactive },
  });
  return data;
}

export async function getById(id: string): Promise<Staff> {
  const { data } = await api.get<Staff>(`/staff/${id}`);
  return data;
}

export async function create(staff: StaffCreate): Promise<Staff> {
  const { data } = await api.post<Staff>("/staff", staff);
  return data;
}

export async function update(id: string, staff: StaffUpdate): Promise<Staff> {
  const { data } = await api.put<Staff>(`/staff/${id}`, staff);
  return data;
}

export async function deactivate(id: string): Promise<Staff> {
  const { data } = await api.delete<Staff>(`/staff/${id}`);
  return data;
}

export async function restore(id: string): Promise<Staff> {
  const { data } = await api.put<Staff>(`/staff/${id}/restore`);
  return data;
}

export async function changeOwnPassword(
  payload: ChangePasswordRequest,
): Promise<Staff> {
  const { data } = await api.put<Staff>("/staff/me/change-password", payload);
  return data;
}

export async function adminChangePassword(
  id: string,
  payload: AdminChangePasswordRequest,
): Promise<Staff> {
  const { data } = await api.put<Staff>(`/staff/${id}/change-password`, payload);
  return data;
}
