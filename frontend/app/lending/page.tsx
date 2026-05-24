"use client";

import { ArrowLeftRight } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { AppLayout } from "@/components/layout/AppLayout";
import { ActiveLoansTable } from "@/components/lending/ActiveLoansTable";
import { BorrowModal } from "@/components/lending/BorrowModal";
import { OverdueTable } from "@/components/lending/OverdueTable";
import { UpdateDueDateModal } from "@/components/lending/UpdateDueDateModal";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { lendingService } from "@/services";
import type { Lending } from "@/types";

function LendingPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [activeLoans, setActiveLoans] = useState<Lending[]>([]);
  const [overdueLoans, setOverdueLoans] = useState<Lending[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [borrowModalOpen, setBorrowModalOpen] = useState(false);
  const [selectedLending, setSelectedLending] = useState<Lending | null>(null);
  const [isUpdateDueDateModalOpen, setIsUpdateDueDateModalOpen] =
    useState(false);
  const [tab, setTab] = useState(
    searchParams.get("tab") === "overdue" ? "overdue" : "active",
  );

  const loadLoans = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [active, overdue] = await Promise.all([
        lendingService.getAllActive(),
        lendingService.getOverdue(),
      ]);
      setActiveLoans(active);
      setOverdueLoans(overdue);
    } catch (err) {
      const apiError = err as { message?: string };
      setError(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to load loans.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadLoans();
  }, [loadLoans]);

  useEffect(() => {
    if (searchParams.get("tab") === "overdue") {
      setTab("overdue");
    }
  }, [searchParams]);

  useEffect(() => {
    if (searchParams.get("action") === "borrow") {
      setBorrowModalOpen(true);
      router.replace("/lending", { scroll: false });
    }
  }, [searchParams, router]);

  const overdueCount = overdueLoans.length;

  function handleEditDueDate(lending: Lending) {
    setSelectedLending(lending);
    setIsUpdateDueDateModalOpen(true);
  }

  function handleDueDateUpdateSuccess() {
    setIsUpdateDueDateModalOpen(false);
    setSelectedLending(null);
    void loadLoans();
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
          </TabsList>

          <TabsContent value="active" className="mt-4">
            {isLoading ? (
              <LoadingSkeleton rows={5} columns={7} />
            ) : (
              <ActiveLoansTable
                loans={activeLoans}
                onReturn={() => void loadLoans()}
                onEditDueDate={handleEditDueDate}
              />
            )}
          </TabsContent>

          <TabsContent value="overdue" className="mt-4">
            {isLoading ? (
              <LoadingSkeleton rows={5} columns={7} />
            ) : (
              <OverdueTable loans={overdueLoans} />
            )}
          </TabsContent>
        </Tabs>
      </div>

      <BorrowModal
        open={borrowModalOpen}
        onOpenChange={setBorrowModalOpen}
        onSuccess={() => void loadLoans()}
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
