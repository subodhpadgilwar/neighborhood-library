import { api } from "@/lib/api";
import { apiPaths } from "@/lib/apiPaths";
import type {
  AdminChangePasswordRequest,
  ChangePasswordRequest,
  Staff,
  StaffCreate,
  StaffListResponse,
  StaffUpdate,
} from "@/types";

export async function getAll(includeInactive = false): Promise<Staff[]> {
  const { data } = await api.get<StaffListResponse>(apiPaths.staff.list, {
    params: { page: 1, limit: 10_000, include_inactive: includeInactive },
  });
  return data.items;
}

export async function getPage(params: {
  page: number;
  limit: number;
  includeInactive?: boolean;
  sortBy?: "full_name" | "email" | "created_at";
  sortOrder?: "asc" | "desc";
}): Promise<StaffListResponse> {
  const { data } = await api.get<StaffListResponse>(apiPaths.staff.list, {
    params: {
      page: params.page,
      limit: params.limit,
      include_inactive: params.includeInactive ?? false,
      sort_by: params.sortBy ?? "full_name",
      sort_order: params.sortOrder ?? "asc",
    },
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
