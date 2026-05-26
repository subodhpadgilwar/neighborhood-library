"use client";

import { ChevronDown, Filter } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  dateInputToApiIso,
  dateInputToStartOfDayIso,
  isoToDateInputValue,
} from "@/lib/dateUtils";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { cn } from "@/lib/utils";
import type { LendingFilters as LendingFiltersState } from "@/types";

interface LendingFiltersProps {
  filters: LendingFiltersState;
  onChange: (filters: LendingFiltersState) => void;
  onReset: () => void;
  isLoading: boolean;
}

const dateInputClassName =
  "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30";

function countActiveFilters(filters: LendingFiltersState): number {
  let count = 0;
  if (filters.status) {
    count += 1;
  }
  if (filters.member_name?.trim()) {
    count += 1;
  }
  if (filters.book_title?.trim()) {
    count += 1;
  }
  if (filters.borrowed_from) {
    count += 1;
  }
  if (filters.borrowed_to) {
    count += 1;
  }
  return count;
}

function isoToDateInput(iso: string | undefined): string {
  if (!iso) {
    return "";
  }
  return isoToDateInputValue(iso);
}

export function LendingFilters({
  filters,
  onChange,
  onReset,
  isLoading,
}: LendingFiltersProps) {
  const [expanded, setExpanded] = useState(true);
  const [bookTitleInput, setBookTitleInput] = useState(filters.book_title ?? "");
  const [memberNameInput, setMemberNameInput] = useState(
    filters.member_name ?? "",
  );
  const [borrowedFromInput, setBorrowedFromInput] = useState(
    isoToDateInput(filters.borrowed_from),
  );
  const [borrowedToInput, setBorrowedToInput] = useState(
    isoToDateInput(filters.borrowed_to),
  );

  const activeCount = useMemo(() => countActiveFilters(filters), [filters]);

  useDeferredEffect(() => {
    setBookTitleInput(filters.book_title ?? "");
  }, [filters.book_title]);

  useDeferredEffect(() => {
    setMemberNameInput(filters.member_name ?? "");
  }, [filters.member_name]);

  useDeferredEffect(() => {
    setBorrowedFromInput(isoToDateInput(filters.borrowed_from));
  }, [filters.borrowed_from]);

  useDeferredEffect(() => {
    setBorrowedToInput(isoToDateInput(filters.borrowed_to));
  }, [filters.borrowed_to]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const trimmed = bookTitleInput.trim();
      if ((filters.book_title ?? "") === trimmed) {
        return;
      }
      onChange({
        ...filters,
        book_title: trimmed || undefined,
      });
    }, 400);

    return () => window.clearTimeout(timer);
  }, [bookTitleInput, filters, onChange]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const trimmed = memberNameInput.trim();
      if ((filters.member_name ?? "") === trimmed) {
        return;
      }
      onChange({
        ...filters,
        member_name: trimmed || undefined,
      });
    }, 400);

    return () => window.clearTimeout(timer);
  }, [memberNameInput, filters, onChange]);

  function updateFilters(patch: Partial<LendingFiltersState>) {
    onChange({ ...filters, ...patch });
  }

  function handleBorrowedFromChange(value: string) {
    setBorrowedFromInput(value);
    updateFilters({
      borrowed_from: value ? dateInputToStartOfDayIso(value) : undefined,
    });
  }

  function handleBorrowedToChange(value: string) {
    setBorrowedToInput(value);
    updateFilters({
      borrowed_to: value ? dateInputToApiIso(value) : undefined,
    });
  }

  return (
    <div className="rounded-lg border bg-card">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left"
        onClick={() => setExpanded((open) => !open)}
        aria-expanded={expanded}
      >
        <span className="flex items-center gap-2 text-sm font-medium">
          <Filter className="size-4 text-muted-foreground" aria-hidden />
          Filters{activeCount > 0 ? ` (${activeCount})` : ""}
        </span>
        <ChevronDown
          className={cn(
            "size-4 text-muted-foreground transition-transform",
            expanded && "rotate-180",
          )}
          aria-hidden
        />
      </button>

      {expanded ? (
        <div className="space-y-4 border-t px-4 pb-4 pt-3">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="history-book-title">Book Title</Label>
              <Input
                id="history-book-title"
                placeholder="Search by book title…"
                value={bookTitleInput}
                onChange={(event) => setBookTitleInput(event.target.value)}
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="history-member-name">Member Name</Label>
              <Input
                id="history-member-name"
                placeholder="Search by member name…"
                value={memberNameInput}
                onChange={(event) => setMemberNameInput(event.target.value)}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={filters.status ?? "all"}
                onValueChange={(value) =>
                  updateFilters({
                    status:
                      value === "all"
                        ? undefined
                        : (value as LendingFiltersState["status"]),
                  })
                }
                disabled={isLoading}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="returned">Returned</SelectItem>
                  <SelectItem value="overdue">Overdue</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="history-borrowed-from">Borrowed From</Label>
              <input
                id="history-borrowed-from"
                type="date"
                className={dateInputClassName}
                value={borrowedFromInput}
                onChange={(event) =>
                  handleBorrowedFromChange(event.target.value)
                }
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="history-borrowed-to">Borrowed To</Label>
              <input
                id="history-borrowed-to"
                type="date"
                className={dateInputClassName}
                value={borrowedToInput}
                onChange={(event) => handleBorrowedToChange(event.target.value)}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-end gap-4">
            <div className="min-w-[180px] flex-1 space-y-2">
              <Label>Sort By</Label>
              <Select
                value={filters.sort_by ?? "borrowed_at"}
                onValueChange={(value) =>
                  updateFilters({
                    sort_by: value as LendingFiltersState["sort_by"],
                  })
                }
                disabled={isLoading}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="borrowed_at">Borrow Date</SelectItem>
                  <SelectItem value="due_date">Due Date</SelectItem>
                  <SelectItem value="returned_at">Return Date</SelectItem>
                  <SelectItem value="member_name">Member Name</SelectItem>
                  <SelectItem value="book_title">Book Title</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              type="button"
              variant="outline"
              disabled={isLoading}
              onClick={() =>
                updateFilters({
                  sort_order: filters.sort_order === "asc" ? "desc" : "asc",
                })
              }
            >
              {filters.sort_order === "asc" ? "↑ Asc" : "↓ Desc"}
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={onReset}
              disabled={isLoading}
            >
              Reset Filters
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
