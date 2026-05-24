import { api } from "@/lib/api";
import type { Lending, Member, MemberCreate, MemberUpdate } from "@/types";

export async function getAll(skip = 0, limit = 100): Promise<Member[]> {
  const { data } = await api.get<Member[]>("/members", {
    params: { skip, limit },
  });
  return data;
}

export async function getById(id: string): Promise<Member> {
  const { data } = await api.get<Member>(`/members/${id}`);
  return data;
}

export async function create(member: MemberCreate): Promise<Member> {
  const { data } = await api.post<Member>("/members", member);
  return data;
}

export async function update(id: string, member: MemberUpdate): Promise<Member> {
  const { data } = await api.put<Member>(`/members/${id}`, member);
  return data;
}

export async function getLoans(memberId: string): Promise<Lending[]> {
  const { data } = await api.get<Lending[]>(`/members/${memberId}/loans`);
  return data;
}
