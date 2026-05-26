"use client";

import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Filter,
} from "lucide-react";
import { differenceInCalendarDays, parseISO, startOfDay } from "date-fns";

import { formatLoanDate, getLoanStatus } from "@/components/lending/loanUtils";
import { LoanStatusBadge } from "@/components/lending/LoanStatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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

function SortableHeader({
  label,
  column,
  sortBy,
  sortOrder,
  onSortChange,
}: {
  label: string;
  column: SortableColumn;
  sortBy?: LendingFilters["sort_by"];
  sortOrder?: LendingFilters["sort_order"];
  onSortChange: LendingHistoryTableProps["onSortChange"];
}) {
  const isActive = sortBy === column;

  function handleClick() {
    if (isActive) {
      onSortChange(column, sortOrder === "asc" ? "desc" : "asc");
      return;
    }
    onSortChange(column, "desc");
  }

  return (
    <TableHead>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="-ml-3 h-8 gap-1 font-medium"
        onClick={handleClick}
      >
        {label}
        {isActive ? (
          sortOrder === "asc" ? (
            <ArrowUp className="size-3.5" aria-hidden />
          ) : (
            <ArrowDown className="size-3.5" aria-hidden />
          )
        ) : (
          <ArrowUpDown
            className="size-3.5 text-muted-foreground"
            aria-hidden
          />
        )}
      </Button>
    </TableHead>
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

  return (
    <div className="space-y-2">
      <Table>
        <TableHeader>
          <TableRow>
            <SortableHeader
              label="Book Title"
              column="book_title"
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSortChange={onSortChange}
            />
            <TableHead>Author</TableHead>
            <SortableHeader
              label="Member Name"
              column="member_name"
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSortChange={onSortChange}
            />
            <TableHead>Member Email</TableHead>
            <SortableHeader
              label="Borrowed Date"
              column="borrowed_at"
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSortChange={onSortChange}
            />
            <SortableHeader
              label="Due Date"
              column="due_date"
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSortChange={onSortChange}
            />
            <SortableHeader
              label="Returned Date"
              column="returned_at"
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSortChange={onSortChange}
            />
            <TableHead>Status</TableHead>
            <TableHead>Days Info</TableHead>
            <TableHead>Processed By</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((lending) => (
            <TableRow key={lending.id} className={cn(getRowClassName(lending))}>
              <TableCell className="font-medium">{lending.book_title}</TableCell>
              <TableCell>{lending.book_author}</TableCell>
              <TableCell>{lending.member_name}</TableCell>
              <TableCell className="text-muted-foreground">
                {lending.member_email}
              </TableCell>
              <TableCell>{formatLoanDate(lending.borrowed_at)}</TableCell>
              <TableCell>{formatLoanDate(lending.due_date)}</TableCell>
              <TableCell>
                {lending.returned_at
                  ? formatLoanDate(lending.returned_at)
                  : "—"}
              </TableCell>
              <TableCell>
                <HistoryStatusBadge lending={lending} />
              </TableCell>
              <TableCell>
                <DaysInfo lending={lending} />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {lending.processed_by ?? "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
