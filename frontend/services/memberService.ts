import { api } from "@/lib/api";
import { apiPaths } from "@/lib/apiPaths";
import type {
  Lending,
  Member,
  MemberCreate,
  MemberListResponse,
  MemberUpdate,
} from "@/types";

interface MemberPageParams {
  page?: number;
  limit?: number;
  includeInactive?: boolean;
  search?: string;
  sortBy?: "name" | "email" | "created_at";
  sortOrder?: "asc" | "desc";
}

export async function getPage({
  page = 1,
  limit = 100,
  includeInactive = false,
  search,
  sortBy = "name",
  sortOrder = "asc",
}: MemberPageParams = {}): Promise<MemberListResponse> {
  const { data } = await api.get<MemberListResponse>(apiPaths.members.list, {
    params: {
      page,
      limit,
      include_inactive: includeInactive,
      search: search?.trim() || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  return data;
}

export async function getAll(
  page = 1,
  limit = 100,
  includeInactive = false,
): Promise<Member[]> {
  const data = await getPage({ page, limit, includeInactive });
  return data.items;
}

export async function getById(id: string): Promise<Member> {
  const { data } = await api.get<Member>(apiPaths.members.byId(id));
  return data;
}

export async function create(member: MemberCreate): Promise<Member> {
  const { data } = await api.post<Member>(apiPaths.members.list, member);
  return data;
}

export async function update(id: string, member: MemberUpdate): Promise<Member> {
  const { data } = await api.put<Member>(apiPaths.members.byId(id), member);
  return data;
}

export async function deactivate(id: string): Promise<Member> {
  const { data } = await api.delete<Member>(apiPaths.members.byId(id));
  return data;
}

export async function restore(id: string): Promise<Member> {
  const { data } = await api.put<Member>(apiPaths.members.restore(id));
  return data;
}

export async function getLoans(memberId: string): Promise<Lending[]> {
  const { data } = await api.get<Lending[]>(apiPaths.members.loans(memberId));
  return data;
}
