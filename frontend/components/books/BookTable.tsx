"use client";

import { ArrowDown, ArrowUp, BookX, Pencil, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/shared/DataTable";
import { cn } from "@/lib/utils";
import type { Book } from "@/types";

export type TitleSortDirection = "asc" | "desc";

interface BookTableProps {
  books: Book[];
  sortDirection: TitleSortDirection;
  highlightedBookId?: string | null;
  onSortChange: () => void;
  onEdit: (book: Book) => void;
  onDeactivate: (book: Book) => void;
  onRestore: (book: Book) => void;
}

function AvailabilityBadge({
  available,
  total,
}: {
  available: number;
  total: number;
}) {
  if (available > 0) {
    return (
      <Badge className="border-emerald-200 bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
        {available}/{total}
      </Badge>
    );
  }
  return (
    <Badge
      variant="destructive"
      className="bg-destructive/15 hover:bg-destructive/15"
    >
      Unavailable
    </Badge>
  );
}

function SortIcon({ direction }: { direction: TitleSortDirection }) {
  if (direction === "asc") {
    return <ArrowUp className="size-4" aria-hidden />;
  }
  return <ArrowDown className="size-4" aria-hidden />;
}

export function BookTable({
  books,
  sortDirection,
  highlightedBookId,
  onSortChange,
  onEdit,
  onDeactivate,
  onRestore,
}: BookTableProps) {
  const columns: DataTableColumn<Book>[] = [
    {
      key: "title",
      header: (
        <button
          type="button"
          onClick={onSortChange}
          className={cn(
            "inline-flex items-center gap-1 font-medium transition-colors hover:text-foreground",
          )}
        >
          Title
          <SortIcon direction={sortDirection} />
        </button>
      ),
      className: "max-w-[200px] truncate font-medium",
      cell: (book) => (
        <span
          className={cn(
            !book.is_active && "text-muted-foreground line-through",
          )}
        >
          {book.title}
        </span>
      ),
    },
    {
      key: "author",
      header: "Author",
      className: "max-w-[160px] truncate",
      cell: (book) => (
        <span className={cn(!book.is_active && "text-muted-foreground")}>
          {book.author}
        </span>
      ),
    },
    {
      key: "isbn",
      header: "ISBN",
      className: "text-muted-foreground",
      cell: (book) => book.isbn ?? "—",
    },
    {
      key: "genre",
      header: "Genre",
      className: "text-muted-foreground",
      cell: (book) => book.genre ?? "—",
    },
    {
      key: "shelf",
      header: "Shelf Location",
      headerClassName: "max-w-[120px]",
      className: "max-w-[120px] truncate text-muted-foreground",
      cell: (book) => (
        <span title={book.shelf_location ?? undefined}>
          {book.shelf_location ?? "—"}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      cell: (book) =>
        !book.is_active ? (
          <Badge
            variant="destructive"
            className="bg-destructive/15 hover:bg-destructive/15"
          >
            Inactive
          </Badge>
        ) : null,
    },
    {
      key: "availability",
      header: "Available/Total",
      cell: (book) => (
        <AvailabilityBadge
          available={book.copies_available}
          total={book.copies_total}
        />
      ),
    },
    {
      key: "createdBy",
      header: "Added By",
      className: "text-muted-foreground",
      cell: (book) => book.created_by ?? "—",
    },
    {
      key: "actions",
      header: "Actions",
      headerClassName: "w-[120px] text-right",
      className: "text-right",
      cell: (book) =>
        book.is_active ? (
          <div className="flex justify-end gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => onEdit(book)}
              aria-label={`Edit ${book.title}`}
            >
              <Pencil className="size-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="text-destructive hover:text-destructive"
              onClick={() => onDeactivate(book)}
              aria-label={`Deactivate ${book.title}`}
            >
              <BookX className="size-4" />
            </Button>
          </div>
        ) : (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="text-emerald-600 hover:text-emerald-600"
            onClick={() => onRestore(book)}
            aria-label={`Restore ${book.title}`}
          >
            <RefreshCw className="size-4" />
          </Button>
        ),
    },
  ];

  return (
    <DataTable
      data={books}
      columns={columns}
      getRowKey={(book) => book.id}
      getRowClassName={(book) =>
        cn(
          !book.is_active && "opacity-60",
          highlightedBookId === book.id &&
            "bg-emerald-50/80 ring-1 ring-emerald-200 dark:bg-emerald-950/30 dark:ring-emerald-800",
        )
      }
    />
  );
}
