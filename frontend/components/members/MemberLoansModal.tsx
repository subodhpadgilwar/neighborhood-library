"use client";

import {
  differenceInCalendarDays,
  format,
  parseISO,
  startOfDay,
} from "date-fns";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
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
import { memberService } from "@/services";
import type { Lending, Member } from "@/types";

type LoanStatus = "overdue" | "due-soon" | "active";

interface MemberLoansModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  member: Member | null;
}

function getLoanStatus(lending: Lending): LoanStatus {
  if (lending.is_overdue) {
    return "overdue";
  }
  const due = startOfDay(parseISO(lending.due_date));
  const today = startOfDay(new Date());
  const daysUntilDue = differenceInCalendarDays(due, today);
  if (daysUntilDue >= 0 && daysUntilDue <= 3) {
    return "due-soon";
  }
  return "active";
}

function formatDate(iso: string): string {
  return format(parseISO(iso), "MMM d, yyyy");
}

function LoanStatusBadge({ status }: { status: LoanStatus }) {
  if (status === "overdue") {
    return (
      <Badge
        variant="destructive"
        className="bg-destructive/15 text-destructive hover:bg-destructive/15"
      >
        Overdue
      </Badge>
    );
  }
  if (status === "due-soon") {
    return (
      <Badge className="border-amber-200 bg-amber-100 text-amber-800 hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
        Due Soon
      </Badge>
    );
  }
  return (
    <Badge className="border-emerald-200 bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
      Active
    </Badge>
  );
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
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : loans.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No active loans
          </p>
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
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
