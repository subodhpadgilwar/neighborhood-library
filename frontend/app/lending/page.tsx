"use client";

import { ArrowLeftRight } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useState } from "react";

import { AppLayout } from "@/components/layout/AppLayout";
import { ActiveLoansTable } from "@/components/lending/ActiveLoansTable";
import { BorrowModal } from "@/components/lending/BorrowModal";
import { LendingFilters } from "@/components/lending/LendingFilters";
import { LendingHistoryTable } from "@/components/lending/LendingHistoryTable";
import { OverdueTable } from "@/components/lending/OverdueTable";
import { UpdateDueDateModal } from "@/components/lending/UpdateDueDateModal";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Pagination } from "@/components/shared/Pagination";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { usePaginatedQuery } from "@/hooks/usePaginatedQuery";
import { lendingService } from "@/services";
import type {
  Lending,
  LendingFilters as LendingFiltersState,
  LendingHistoryResponse,
  ActiveLoansResponse,
  OverdueLoansResponse,
} from "@/types";

const DEFAULT_HISTORY_FILTERS: LendingFiltersState = {
  sort_by: "borrowed_at",
  sort_order: "desc",
  skip: 0,
  limit: 25,
};

function resolveTab(tabParam: string | null): string {
  if (tabParam === "overdue") {
    return "overdue";
  }
  if (tabParam === "history") {
    return "history";
  }
  return "active";
}

function LendingPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [activeData, setActiveData] = useState<ActiveLoansResponse | null>(null);
  const [overdueData, setOverdueData] = useState<OverdueLoansResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [borrowModalOpen, setBorrowModalOpen] = useState(false);
  const [selectedLending, setSelectedLending] = useState<Lending | null>(null);
  const [isUpdateDueDateModalOpen, setIsUpdateDueDateModalOpen] =
    useState(false);
  const [tab, setTab] = useState(() => resolveTab(searchParams.get("tab")));

  const [historyData, setHistoryData] = useState<LendingHistoryResponse | null>(
    null,
  );
  const [historyFilters, setHistoryFilters] =
    useState<LendingFiltersState>(DEFAULT_HISTORY_FILTERS);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyTabOpened, setHistoryTabOpened] = useState(
    searchParams.get("tab") === "history",
  );

  const activePagination = usePaginatedQuery({ defaultLimit: 50 });
  const overduePagination = usePaginatedQuery({ defaultLimit: 50 });

  const loadLoans = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [active, overdue] = await Promise.all([
        lendingService.getActivePage({
          skip: activePagination.skip,
          limit: activePagination.limit,
        }),
        lendingService.getOverduePage({
          skip: overduePagination.skip,
          limit: overduePagination.limit,
        }),
      ]);
      setActiveData(active);
      setOverdueData(overdue);
    } catch (err) {
      const apiError = err as { message?: string };
      setError(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to load loans.",
      );
      setActiveData(null);
      setOverdueData(null);
    } finally {
      setIsLoading(false);
    }
  }, [activePagination.limit, activePagination.skip, overduePagination.limit, overduePagination.skip]);

  const fetchHistory = useCallback(async () => {
    setIsHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await lendingService.getHistory(historyFilters);
      setHistoryData(response);
    } catch (err) {
      const apiError = err as { message?: string };
      setHistoryError(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to load lending history.",
      );
      setHistoryData(null);
    } finally {
      setIsHistoryLoading(false);
    }
  }, [historyFilters]);

  useDeferredEffect(() => {
    void loadLoans();
  }, [loadLoans]);

  useDeferredEffect(() => {
    setTab(resolveTab(searchParams.get("tab")));
    if (searchParams.get("tab") === "history") {
      setHistoryTabOpened(true);
    }
  }, [searchParams]);

  useDeferredEffect(() => {
    if (searchParams.get("action") === "borrow") {
      setBorrowModalOpen(true);
      router.replace("/lending", { scroll: false });
    }
  }, [searchParams, router]);

  useDeferredEffect(() => {
    if (tab === "history") {
      setHistoryTabOpened(true);
    }
  }, [tab]);

  useDeferredEffect(() => {
    if (!historyTabOpened) {
      return;
    }
    void fetchHistory();
  }, [historyTabOpened, fetchHistory]);

  const overdueCount = overdueData?.total ?? 0;
  const historyPage = historyData?.page ?? 1;
  const historyTotalPages = historyData?.total_pages ?? 0;

  const activeTotalPages = activeData
    ? Math.ceil(activeData.total / activeData.limit)
    : 0;
  const overdueTotalPages = overdueData
    ? Math.ceil(overdueData.total / overdueData.limit)
    : 0;

  function handleActivePageChange(page: number) {
    activePagination.setPage(page);
  }

  function handleActiveLimitChange(limit: number) {
    activePagination.setLimit(limit);
  }

  function handleOverduePageChange(page: number) {
    overduePagination.setPage(page);
  }

  function handleOverdueLimitChange(limit: number) {
    overduePagination.setLimit(limit);
  }

  function handleEditDueDate(lending: Lending) {
    setSelectedLending(lending);
    setIsUpdateDueDateModalOpen(true);
  }

  function handleDueDateUpdateSuccess() {
    setIsUpdateDueDateModalOpen(false);
    setSelectedLending(null);
    void loadLoans();
    if (historyTabOpened) {
      void fetchHistory();
    }
  }

  function handleFilterChange(newFilters: LendingFiltersState) {
    setHistoryFilters({
      ...newFilters,
      skip: 0,
    });
  }

  function handlePageChange(page: number) {
    setHistoryFilters((prev) => ({
      ...prev,
      skip: (page - 1) * (prev.limit ?? 25),
    }));
  }

  function handleLimitChange(limit: number) {
    setHistoryFilters((prev) => ({
      ...prev,
      limit,
      skip: 0,
    }));
  }

  function handleSortChange(
    sortBy: NonNullable<LendingFiltersState["sort_by"]>,
    sortOrder: NonNullable<LendingFiltersState["sort_order"]>,
  ) {
    setHistoryFilters((prev) => ({
      ...prev,
      sort_by: sortBy,
      sort_order: sortOrder,
      skip: 0,
    }));
  }

  function handleFilterReset() {
    setHistoryFilters(DEFAULT_HISTORY_FILTERS);
  }

  return (
    <AppLayout title="Lending">
      <div className="space-y-6">
        <div className="flex justify-end">
          <Button
            onClick={() => setBorrowModalOpen(true)}
            className="gap-2"
          >
            <ArrowLeftRight className="size-4" aria-hidden />
            Borrow Book
          </Button>
        </div>

        {error ? <ErrorMessage message={error} /> : null}

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="active">Active Loans</TabsTrigger>
            <TabsTrigger value="overdue" className="gap-2">
              Overdue
              {overdueCount > 0 ? (
                <Badge
                  variant="destructive"
                  className="h-5 min-w-5 justify-center px-1.5 tabular-nums"
                >
                  {overdueCount}
                </Badge>
              ) : null}
            </TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <TabsContent value="active" className="mt-4">
            {isLoading ? (
              <LoadingSkeleton rows={5} columns={7} />
            ) : (
              <div className="space-y-4">
                <ActiveLoansTable
                  loans={activeData?.items ?? []}
                  onReturn={() => void loadLoans()}
                  onEditDueDate={handleEditDueDate}
                />
                {activeData && activeData.total > 0 ? (
                  <Pagination
                    currentPage={activePagination.page}
                    totalPages={activeTotalPages}
                    totalItems={activeData.total}
                    itemsPerPage={activePagination.limit}
                    onPageChange={handleActivePageChange}
                    onLimitChange={handleActiveLimitChange}
                  />
                ) : null}
              </div>
            )}
          </TabsContent>

          <TabsContent value="overdue" className="mt-4">
            {isLoading ? (
              <LoadingSkeleton rows={5} columns={7} />
            ) : (
              <div className="space-y-4">
                <OverdueTable loans={overdueData?.items ?? []} />
                {overdueData && overdueData.total > 0 ? (
                  <Pagination
                    currentPage={overduePagination.page}
                    totalPages={overdueTotalPages}
                    totalItems={overdueData.total}
                    itemsPerPage={overduePagination.limit}
                    onPageChange={handleOverduePageChange}
                    onLimitChange={handleOverdueLimitChange}
                  />
                ) : null}
              </div>
            )}
          </TabsContent>

          <TabsContent value="history" className="mt-4 space-y-4">
            <LendingFilters
              filters={historyFilters}
              onChange={handleFilterChange}
              onReset={handleFilterReset}
              isLoading={isHistoryLoading}
            />

            {historyError ? (
              <div className="space-y-3">
                <ErrorMessage message={historyError} />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => void fetchHistory()}
                >
                  Retry
                </Button>
              </div>
            ) : null}

            {!historyError ? (
              <>
                <p className="text-sm text-muted-foreground">
                  {isHistoryLoading
                    ? "Loading records…"
                    : historyData && historyData.total > 0
                      ? `${historyData.total} records found`
                      : "No records found"}
                </p>

                {isHistoryLoading ? (
                  <LoadingSkeleton rows={5} columns={9} />
                ) : (
                  <>
                    <LendingHistoryTable
                      items={historyData?.items ?? []}
                      sortBy={historyFilters.sort_by}
                      sortOrder={historyFilters.sort_order}
                      onSortChange={handleSortChange}
                    />

                    {historyData && historyData.total > 0 ? (
                      <Pagination
                        currentPage={historyPage}
                        totalPages={historyTotalPages}
                        totalItems={historyData.total}
                        itemsPerPage={historyData.limit}
                        onPageChange={handlePageChange}
                        onLimitChange={handleLimitChange}
                      />
                    ) : null}
                  </>
                )}
              </>
            ) : null}
          </TabsContent>
        </Tabs>
      </div>

      <BorrowModal
        open={borrowModalOpen}
        onOpenChange={setBorrowModalOpen}
        onSuccess={() => {
          void loadLoans();
          if (historyTabOpened) {
            void fetchHistory();
          }
        }}
      />

      {selectedLending ? (
        <UpdateDueDateModal
          isOpen={isUpdateDueDateModalOpen}
          onClose={() => {
            setIsUpdateDueDateModalOpen(false);
            setSelectedLending(null);
          }}
          onSuccess={handleDueDateUpdateSuccess}
          lending={selectedLending}
        />
      ) : null}
    </AppLayout>
  );
}

function LendingPageFallback() {
  return (
    <AppLayout title="Lending">
      <LoadingSkeleton rows={5} columns={7} />
    </AppLayout>
  );
}

export default function LendingPage() {
  return (
    <Suspense fallback={<LendingPageFallback />}>
      <LendingPageContent />
    </Suspense>
  );
}
