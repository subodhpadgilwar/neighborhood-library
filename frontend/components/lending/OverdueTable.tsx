"use client";

import {
  daysOverdue,
  formatLoanDate,
  getLoanStatus,
} from "@/components/lending/loanUtils";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoanStatusBadge } from "@/components/lending/LoanStatusBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { Lending } from "@/types";

interface OverdueTableProps {
  loans: Lending[];
}

export function OverdueTable({ loans }: OverdueTableProps) {
  if (loans.length === 0) {
    return <EmptyState message="No overdue loans. Great work!" />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow className="border-destructive/20 bg-destructive/5 hover:bg-destructive/5">
          <TableHead>Book</TableHead>
          <TableHead>Author</TableHead>
          <TableHead>Member</TableHead>
          <TableHead>Borrowed Date</TableHead>
          <TableHead>Due Date</TableHead>
          <TableHead>Days Overdue</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {loans.map((loan) => {
          const overdueDays = daysOverdue(loan.due_date);
          return (
            <TableRow
              key={loan.id}
              className={cn(
                "border-destructive/10 bg-destructive/[0.03] hover:bg-destructive/15",
              )}
            >
              <TableCell className="font-medium text-destructive">
                {loan.book_title}
              </TableCell>
              <TableCell className="text-destructive/80">
                {loan.book_author}
              </TableCell>
              <TableCell>
                <div className="max-w-[160px] truncate font-medium">
                  {loan.member_name}
                </div>
                <div className="truncate text-xs text-muted-foreground">
                  {loan.member_email}
                </div>
              </TableCell>
              <TableCell>{formatLoanDate(loan.borrowed_at)}</TableCell>
              <TableCell className="font-medium text-destructive">
                {formatLoanDate(loan.due_date)}
              </TableCell>
              <TableCell>
                <span className="font-semibold tabular-nums text-destructive">
                  {overdueDays} {overdueDays === 1 ? "day" : "days"}
                </span>
              </TableCell>
              <TableCell>
                <LoanStatusBadge status={getLoanStatus(loan)} />
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
