import { useCallback, useMemo, useState } from "react";

export interface PaginationState {
  page: number;
  limit: number;
}

/**
 * Shared pagination state helper for list views.
 * Keeps list pages consistent (page/limit + derived skip).
 */
export function usePaginatedQuery(options?: {
  defaultPage?: number;
  defaultLimit?: number;
}) {
  const [page, setPage] = useState(options?.defaultPage ?? 1);
  const [limit, setLimit] = useState(options?.defaultLimit ?? 10);

  const skip = useMemo(() => (page - 1) * limit, [page, limit]);

  const setLimitAndResetPage = useCallback((nextLimit: number) => {
    setLimit(nextLimit);
    setPage(1);
  }, []);

  const setPageSafe = useCallback((nextPage: number) => {
    setPage(Math.max(1, nextPage));
  }, []);

  return {
    page,
    limit,
    skip,
    setPage: setPageSafe,
    setLimit: setLimitAndResetPage,
    rawSetLimit: setLimit,
  };
}

