import { pageLimitToSkip } from "@/lib/pagination";
import { api } from "@/lib/api";
import { apiPaths } from "@/lib/apiPaths";
import type {
  ActiveLoansResponse,
  BorrowRequest,
  Lending,
  LendingFilters,
  LendingHistoryResponse,
  OverdueLoansResponse,
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
    const d = new Date(filters.borrowed_from);
    if (!isNaN(d.getTime())) {
      params.borrowed_from = d.toISOString();
    }
  }
  if (filters.borrowed_to) {
    const d = new Date(filters.borrowed_to);
    if (!isNaN(d.getTime())) {
      params.borrowed_to = d.toISOString();
    }
  }
  if (filters.sort_by) {
    params.sort_by = filters.sort_by;
  }
  if (filters.sort_order) {
    params.sort_order = filters.sort_order;
  }
  if (filters.page !== undefined && filters.limit !== undefined) {
    params.skip = pageLimitToSkip(filters.page, filters.limit);
    params.limit = filters.limit;
  } else if (filters.limit !== undefined) {
    params.limit = filters.limit;
  }

  return params;
}

export async function getAllActive(): Promise<Lending[]> {
  const { data } = await api.get<ActiveLoansResponse>(apiPaths.lending.list, {
    params: { skip: 0, limit: 50 },
  });
  return data.items;
}

export async function getOverdue(): Promise<Lending[]> {
  const { data } = await api.get<OverdueLoansResponse>(apiPaths.lending.overdue, {
    params: { skip: 0, limit: 50 },
  });
  return data.items;
}

export async function getActivePage(params: {
  page: number;
  limit: number;
}): Promise<ActiveLoansResponse> {
  const { data } = await api.get<ActiveLoansResponse>(apiPaths.lending.list, {
    params: {
      skip: pageLimitToSkip(params.page, params.limit),
      limit: params.limit,
    },
  });
  return data;
}

export async function getOverduePage(params: {
  page: number;
  limit: number;
}): Promise<OverdueLoansResponse> {
  const { data } = await api.get<OverdueLoansResponse>(apiPaths.lending.overdue, {
    params: {
      skip: pageLimitToSkip(params.page, params.limit),
      limit: params.limit,
    },
  });
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
