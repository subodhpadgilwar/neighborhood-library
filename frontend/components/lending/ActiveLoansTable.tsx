"use client";

import { Calendar } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { formatLoanDate, getLoanStatus } from "@/components/lending/loanUtils";
import { LoanStatusBadge } from "@/components/lending/LoanStatusBadge";
import { ConfirmPopover } from "@/components/shared/ConfirmPopover";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type DataTableColumn } from "@/components/shared/DataTable";
import { Button } from "@/components/ui/button";
import { lendingService } from "@/services";
import type { Lending } from "@/types";

interface ActiveLoansTableProps {
  loans: Lending[];
  onReturn: () => void;
  onEditDueDate: (lending: Lending) => void;
}

export function ActiveLoansTable({
  loans,
  onReturn,
  onEditDueDate,
}: ActiveLoansTableProps) {
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [returningId, setReturningId] = useState<string | null>(null);

  async function handleReturn(lendingId: string) {
    setReturningId(lendingId);
    try {
      await lendingService.returnBook(lendingId);
      toast.success("Book returned");
      setConfirmingId(null);
      onReturn();
    } catch (err) {
      const error = err as { message?: string };
      toast.error(
        typeof error?.message === "string"
          ? error.message
          : "Failed to return book.",
      );
    } finally {
      setReturningId(null);
    }
  }

  if (loans.length === 0) {
    return <EmptyState message="No active loans." />;
  }

  const columns: DataTableColumn<Lending>[] = [
    {
      key: "book",
      header: "Book",
      cell: (loan) => <span className="font-medium">{loan.book_title}</span>,
    },
    {
      key: "author",
      header: "Author",
      cell: (loan) => (
        <span className="text-muted-foreground">{loan.book_author}</span>
      ),
    },
    {
      key: "member",
      header: "Member",
      cell: (loan) => (
        <div>
          <div className="max-w-[160px] truncate">{loan.member_name}</div>
          <div className="truncate text-xs text-muted-foreground">
            {loan.member_email}
          </div>
        </div>
      ),
    },
    {
      key: "borrowed_at",
      header: "Borrowed Date",
      cell: (loan) => formatLoanDate(loan.borrowed_at),
    },
    {
      key: "due_date",
      header: "Due Date",
      cell: (loan) => formatLoanDate(loan.due_date),
    },
    {
      key: "actions",
      header: <span className="sr-only">Actions</span>,
      headerClassName: "text-right",
      className: "text-right",
      cell: (loan) => {
        const isReturning = returningId === loan.id;
        const isActive = loan.returned_at === null;

        return (
          <div className="flex items-center justify-end gap-2">
            <LoanStatusBadge status={getLoanStatus(loan)} />
            {isActive ? (
              <>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => onEditDueDate(loan)}
                  title="Update due date"
                  aria-label={`Update due date for ${loan.book_title}`}
                >
                  <Calendar className="size-4" />
                </Button>
                <ConfirmPopover
                  message="Are you sure?"
                  open={confirmingId === loan.id}
                  onOpenChange={(open) => {
                    if (!open) {
                      setConfirmingId(null);
                    }
                  }}
                  onCancel={() => setConfirmingId(null)}
                  onConfirm={() => handleReturn(loan.id)}
                  isLoading={isReturning}
                >
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={isReturning}
                    onClick={() => setConfirmingId(loan.id)}
                  >
                    Return Book
                  </Button>
                </ConfirmPopover>
              </>
            ) : null}
          </div>
        );
      },
    },
  ];

  return (
    <DataTable
      data={loans}
      columns={columns}
      getRowKey={(loan) => loan.id}
    />
  );
}
