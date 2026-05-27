"use client";

import { Filter } from "lucide-react";
import { differenceInCalendarDays, parseISO, startOfDay } from "date-fns";

import { formatLoanDate, getLoanStatus } from "@/components/lending/loanUtils";
import { LoanStatusBadge } from "@/components/lending/LoanStatusBadge";
import { DataTable, type DataTableColumn } from "@/components/shared/DataTable";
import { Badge } from "@/components/ui/badge";
import { daysOverdue, daysUntilDue } from "@/lib/dateUtils";
import { cn } from "@/lib/utils";
import type { Lending, LendingFilters } from "@/types";

type SortableColumn =
  | "book_title"
  | "member_name"
  | "borrowed_at"
  | "due_date"
  | "returned_at";

interface LendingHistoryTableProps {
  items: Lending[];
  sortBy: LendingFilters["sort_by"];
  sortOrder: LendingFilters["sort_order"];
  onSortChange: (
    sortBy: NonNullable<LendingFilters["sort_by"]>,
    sortOrder: NonNullable<LendingFilters["sort_order"]>,
  ) => void;
}

function daysReturnedLate(lending: Lending): number {
  if (!lending.returned_at) {
    return 0;
  }
  return Math.max(
    0,
    differenceInCalendarDays(
      startOfDay(parseISO(lending.returned_at)),
      startOfDay(parseISO(lending.due_date)),
    ),
  );
}

function HistoryStatusBadge({ lending }: { lending: Lending }) {
  if (lending.returned_at) {
    return (
      <Badge
        variant="secondary"
        className="bg-slate-100 text-slate-700 hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-200"
      >
        Returned
      </Badge>
    );
  }

  return <LoanStatusBadge status={getLoanStatus(lending)} />;
}

function DaysInfo({ lending }: { lending: Lending }) {
  if (lending.returned_at) {
    const lateDays = daysReturnedLate(lending);
    if (lateDays === 0) {
      return (
        <span className="text-sm text-emerald-600 dark:text-emerald-400">
          Returned on time
        </span>
      );
    }
    return (
      <span className="text-sm text-destructive">
        Returned {lateDays} day{lateDays === 1 ? "" : "s"} late
      </span>
    );
  }

  if (lending.is_overdue) {
    const overdue = daysOverdue(lending.due_date);
    return (
      <span className="text-sm text-destructive">
        {overdue} day{overdue === 1 ? "" : "s"} overdue
      </span>
    );
  }

  const left = daysUntilDue(lending.due_date);
  return (
    <span className="text-sm text-emerald-600 dark:text-emerald-400">
      {left} day{left === 1 ? "" : "s"} left
    </span>
  );
}

function getRowClassName(lending: Lending): string {
  if (lending.returned_at) {
    return "bg-muted/40 text-muted-foreground";
  }
  if (lending.is_overdue) {
    return "bg-red-50/80 dark:bg-red-950/20";
  }
  return "";
}

export function LendingHistoryTable({
  items,
  sortBy,
  sortOrder,
  onSortChange,
}: LendingHistoryTableProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
        <Filter
          className="mb-3 size-10 stroke-1 text-muted-foreground"
          aria-hidden
        />
        <p className="text-sm font-medium">No lending records found</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Try adjusting your filters
        </p>
      </div>
    );
  }

  const columns: DataTableColumn<Lending>[] = [
    {
      key: "book_title",
      header: "Book Title",
      sortKey: "book_title",
      cell: (lending) => (
        <span className="font-medium">{lending.book_title}</span>
      ),
    },
    {
      key: "book_author",
      header: "Author",
      cell: (lending) => lending.book_author,
    },
    {
      key: "member_name",
      header: "Member Name",
      sortKey: "member_name",
      cell: (lending) => lending.member_name,
    },
    {
      key: "member_email",
      header: "Member Email",
      cell: (lending) => (
        <span className="text-muted-foreground">{lending.member_email}</span>
      ),
    },
    {
      key: "borrowed_at",
      header: "Borrowed Date",
      sortKey: "borrowed_at",
      cell: (lending) => formatLoanDate(lending.borrowed_at),
    },
    {
      key: "due_date",
      header: "Due Date",
      sortKey: "due_date",
      cell: (lending) => formatLoanDate(lending.due_date),
    },
    {
      key: "returned_at",
      header: "Returned Date",
      sortKey: "returned_at",
      cell: (lending) =>
        lending.returned_at ? formatLoanDate(lending.returned_at) : "—",
    },
    {
      key: "status",
      header: "Status",
      cell: (lending) => <HistoryStatusBadge lending={lending} />,
    },
    {
      key: "days_info",
      header: "Days Info",
      cell: (lending) => <DaysInfo lending={lending} />,
    },
    {
      key: "processed_by",
      header: "Processed By",
      cell: (lending) => (
        <span className="text-muted-foreground">
          {lending.processed_by ?? "—"}
        </span>
      ),
    },
  ];

  return (
    <DataTable
      data={items}
      columns={columns}
      getRowKey={(lending) => lending.id}
      getRowClassName={(lending) => cn(getRowClassName(lending))}
      sort={{
        sortBy: sortBy ?? undefined,
        sortOrder: sortOrder ?? undefined,
        onSortChange: (nextSortBy, nextSortOrder) => {
          onSortChange(nextSortBy as SortableColumn, nextSortOrder);
        },
      }}
    />
  );
}
