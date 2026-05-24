"use client";

import { ArrowDown, ArrowUp, Pencil, RefreshCw, UserX } from "lucide-react";

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
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>
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
          </TableHead>
          <TableHead>Author</TableHead>
          <TableHead>ISBN</TableHead>
          <TableHead>Genre</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Available/Total</TableHead>
          <TableHead>Added By</TableHead>
          <TableHead className="w-[120px] text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {books.map((book) => {
          const isActive = book.is_active;

          return (
            <TableRow
              key={book.id}
              className={cn(
                !isActive && "opacity-60",
                highlightedBookId === book.id &&
                  "bg-emerald-50/80 ring-1 ring-emerald-200 dark:bg-emerald-950/30 dark:ring-emerald-800",
              )}
            >
              <TableCell
                className={cn(
                  "max-w-[200px] truncate font-medium",
                  !isActive && "text-muted-foreground line-through",
                )}
              >
                {book.title}
              </TableCell>
              <TableCell
                className={cn(
                  "max-w-[160px] truncate",
                  !isActive && "text-muted-foreground",
                )}
              >
                {book.author}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {book.isbn ?? "—"}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {book.genre ?? "—"}
              </TableCell>
              <TableCell>
                {!isActive ? (
                  <Badge
                    variant="destructive"
                    className="bg-destructive/15 hover:bg-destructive/15"
                  >
                    Inactive
                  </Badge>
                ) : null}
              </TableCell>
              <TableCell>
                <AvailabilityBadge
                  available={book.copies_available}
                  total={book.copies_total}
                />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {book.created_by ?? "—"}
              </TableCell>
              <TableCell className="text-right">
                {isActive ? (
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
                      <UserX className="size-4" />
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
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
