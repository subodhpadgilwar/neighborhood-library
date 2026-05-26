import { api } from "@/lib/api";
import { apiPaths } from "@/lib/apiPaths";
import type {
  BorrowRequest,
  Lending,
  LendingFilters,
  LendingHistoryResponse,
} from "@/types";

function buildHistoryQueryParams(
  filters?: LendingFilters,
): Record<string, string | number> {
  if (!filters) {
    return {};
  }

  const params: Record<string, string | number> = {};

  if (filters.status) {
    params.status = filters.status;
  }
  if (filters.member_name?.trim()) {
    params.member_name = filters.member_name.trim();
  }
  if (filters.book_title?.trim()) {
    params.book_title = filters.book_title.trim();
  }
  if (filters.borrowed_from) {
    params.borrowed_from = filters.borrowed_from;
  }
  if (filters.borrowed_to) {
    params.borrowed_to = filters.borrowed_to;
  }
  if (filters.sort_by) {
    params.sort_by = filters.sort_by;
  }
  if (filters.sort_order) {
    params.sort_order = filters.sort_order;
  }
  if (filters.skip !== undefined) {
    params.skip = filters.skip;
  }
  if (filters.limit !== undefined) {
    params.limit = filters.limit;
  }

  return params;
}

export async function getAllActive(): Promise<Lending[]> {
  const { data } = await api.get<Lending[]>(apiPaths.lending.list);
  return data;
}

export async function getOverdue(): Promise<Lending[]> {
  const { data } = await api.get<Lending[]>(apiPaths.lending.overdue);
  return data;
}

export async function borrowBook(request: BorrowRequest): Promise<Lending> {
  const { data } = await api.post<Lending>(apiPaths.lending.borrow, request);
  return data;
}

export async function returnBook(lendingId: string): Promise<Lending> {
  const { data } = await api.put<Lending>(
    apiPaths.lending.returnBook(lendingId),
  );
  return data;
}

export async function updateDueDate(
  lendingId: string,
  dueDate: string,
): Promise<Lending> {
  const { data } = await api.put<Lending>(
    apiPaths.lending.dueDate(lendingId),
    {
      due_date: dueDate,
    },
  );
  return data;
}

export async function getHistory(
  filters?: LendingFilters,
): Promise<LendingHistoryResponse> {
  const { data } = await api.get<LendingHistoryResponse>(apiPaths.lending.history, {
    params: buildHistoryQueryParams(filters),
  });
  return data;
}
