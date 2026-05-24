import { api } from "@/lib/api";
import type { BorrowRequest, Lending } from "@/types";

export async function getAllActive(): Promise<Lending[]> {
  const { data } = await api.get<Lending[]>("/lending");
  return data;
}

export async function getOverdue(): Promise<Lending[]> {
  const { data } = await api.get<Lending[]>("/lending/overdue");
  return data;
}

export async function borrowBook(request: BorrowRequest): Promise<Lending> {
  const { data } = await api.post<Lending>("/lending/borrow", request);
  return data;
}

export async function returnBook(lendingId: string): Promise<Lending> {
  const { data } = await api.put<Lending>(`/lending/${lendingId}/return`);
  return data;
}
