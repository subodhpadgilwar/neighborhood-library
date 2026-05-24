"use client";

import { useState } from "react";
import { toast } from "sonner";

import { formatLoanDate, getLoanStatus } from "@/components/lending/loanUtils";
import { LoanStatusBadge } from "@/components/lending/LoanStatusBadge";
import { ConfirmPopover } from "@/components/shared/ConfirmPopover";
import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { lendingService } from "@/services";
import type { Lending } from "@/types";

interface ActiveLoansTableProps {
  loans: Lending[];
  onReturn: () => void;
}

export function ActiveLoansTable({ loans, onReturn }: ActiveLoansTableProps) {
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

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Book</TableHead>
          <TableHead>Author</TableHead>
          <TableHead>Member</TableHead>
          <TableHead>Borrowed Date</TableHead>
          <TableHead>Due Date</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {loans.map((loan) => {
          const isReturning = returningId === loan.id;
          return (
            <TableRow key={loan.id}>
              <TableCell className="font-medium">{loan.book_title}</TableCell>
              <TableCell className="text-muted-foreground">
                {loan.book_author}
              </TableCell>
              <TableCell>
                <div className="max-w-[160px] truncate">{loan.member_name}</div>
                <div className="truncate text-xs text-muted-foreground">
                  {loan.member_email}
                </div>
              </TableCell>
              <TableCell>{formatLoanDate(loan.borrowed_at)}</TableCell>
              <TableCell>{formatLoanDate(loan.due_date)}</TableCell>
              <TableCell>
                <LoanStatusBadge status={getLoanStatus(loan)} />
              </TableCell>
              <TableCell className="text-right">
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
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
