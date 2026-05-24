"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { getLoanStatus } from "@/components/lending/loanUtils";
import { LoanStatusBadge } from "@/components/lending/LoanStatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDate } from "@/lib/dateUtils";
import { memberService } from "@/services";
import type { Lending, Member } from "@/types";

interface MemberLoansModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  member: Member | null;
}

export function MemberLoansModal({
  open,
  onOpenChange,
  member,
}: MemberLoansModalProps) {
  const [loans, setLoans] = useState<Lending[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !member) {
      return;
    }

    const memberId = member.id;
    let cancelled = false;

    async function loadLoans() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await memberService.getLoans(memberId);
        if (!cancelled) {
          setLoans(data);
        }
      } catch (err) {
        const apiError = err as { message?: string };
        if (!cancelled) {
          setError(
            typeof apiError?.message === "string"
              ? apiError.message
              : "Failed to load loans.",
          );
          setLoans([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadLoans();

    return () => {
      cancelled = true;
    };
  }, [open, member]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Active Loans</DialogTitle>
          <DialogDescription>
            {member ? member.name : "Member loans"}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <ErrorMessage message={error} />
        ) : loans.length === 0 ? (
          <EmptyState message="No active loans" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Book Title</TableHead>
                <TableHead>Borrowed Date</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loans.map((loan) => (
                <TableRow key={loan.id}>
                  <TableCell className="font-medium">
                    {loan.book_title}
                  </TableCell>
                  <TableCell>{formatDate(loan.borrowed_at)}</TableCell>
                  <TableCell>{formatDate(loan.due_date)}</TableCell>
                  <TableCell>
                    <LoanStatusBadge status={getLoanStatus(loan)} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
