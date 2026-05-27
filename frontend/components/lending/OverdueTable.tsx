"use client";

import {
  daysOverdue,
  formatLoanDate,
  getLoanStatus,
} from "@/components/lending/loanUtils";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoanStatusBadge } from "@/components/lending/LoanStatusBadge";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/shared/DataTable";
import { cn } from "@/lib/utils";
import type { Lending } from "@/types";

interface OverdueTableProps {
  loans: Lending[];
}

export function OverdueTable({ loans }: OverdueTableProps) {
  if (loans.length === 0) {
    return <EmptyState message="No overdue loans. Great work!" />;
  }

  const columns: DataTableColumn<Lending>[] = [
    {
      key: "book",
      header: "Book",
      cell: (loan) => (
        <span className="font-medium text-destructive">{loan.book_title}</span>
      ),
    },
    {
      key: "author",
      header: "Author",
      cell: (loan) => (
        <span className="text-destructive/80">{loan.book_author}</span>
      ),
    },
    {
      key: "member",
      header: "Member",
      cell: (loan) => (
        <div>
          <div className="max-w-[160px] truncate font-medium">
            {loan.member_name}
          </div>
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
      cell: (loan) => (
        <span className="font-medium text-destructive">
          {formatLoanDate(loan.due_date)}
        </span>
      ),
    },
    {
      key: "days_overdue",
      header: "Days Overdue",
      cell: (loan) => {
        const overdueDays = daysOverdue(loan.due_date);
        return (
          <span className="font-semibold tabular-nums text-destructive">
            {overdueDays} {overdueDays === 1 ? "day" : "days"}
          </span>
        );
      },
    },
    {
      key: "status",
      header: "Status",
      cell: (loan) => <LoanStatusBadge status={getLoanStatus(loan)} />,
    },
  ];

  return (
    <DataTable
      data={loans}
      columns={columns}
      getRowKey={(loan) => loan.id}
      getRowClassName={() =>
        cn("border-destructive/10 bg-destructive/[0.03] hover:bg-destructive/15")
      }
    />
  );
}
