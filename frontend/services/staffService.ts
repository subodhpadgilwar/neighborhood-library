import { api } from "@/lib/api";
import { apiPaths } from "@/lib/apiPaths";
import type {
  AdminChangePasswordRequest,
  ChangePasswordRequest,
  Staff,
  StaffCreate,
  StaffUpdate,
} from "@/types";

export async function getAll(includeInactive = false): Promise<Staff[]> {
  const { data } = await api.get<Staff[]>(apiPaths.staff.list, {
    params: { include_inactive: includeInactive },
  });
  return data;
}

export async function getById(id: string): Promise<Staff> {
  const { data } = await api.get<Staff>(apiPaths.staff.byId(id));
  return data;
}

export async function create(staff: StaffCreate): Promise<Staff> {
  const { data } = await api.post<Staff>(apiPaths.staff.list, staff);
  return data;
}

export async function update(id: string, staff: StaffUpdate): Promise<Staff> {
  const { data } = await api.put<Staff>(apiPaths.staff.byId(id), staff);
  return data;
}

export async function deactivate(id: string): Promise<Staff> {
  const { data } = await api.delete<Staff>(apiPaths.staff.byId(id));
  return data;
}

export async function restore(id: string): Promise<Staff> {
  const { data } = await api.put<Staff>(apiPaths.staff.restore(id));
  return data;
}

export async function changeOwnPassword(
  payload: ChangePasswordRequest,
): Promise<Staff> {
  const { data } = await api.put<Staff>(
    apiPaths.staff.changeOwnPassword,
    payload,
  );
  return data;
}

export async function adminChangePassword(
  id: string,
  payload: AdminChangePasswordRequest,
): Promise<Staff> {
  const { data } = await api.put<Staff>(
    apiPaths.staff.adminChangePassword(id),
    payload,
  );
  return data;
}
