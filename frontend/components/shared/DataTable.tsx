"use client";

import type { ReactNode } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type SortOrder = "asc" | "desc";

export interface DataTableColumn<T> {
  key: string;
  header: ReactNode;
  cell: (item: T) => ReactNode;
  className?: string;
  headerClassName?: string;
  /** If set, column header becomes clickable to drive server-side sorting. */
  sortKey?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: DataTableColumn<T>[];
  getRowKey: (item: T) => string;
  getRowClassName?: (item: T) => string | undefined;
  sort?: {
    sortBy?: string;
    sortOrder?: SortOrder;
    onSortChange: (sortBy: string, sortOrder: SortOrder) => void;
  };
}

export function DataTable<T>({
  data,
  columns,
  getRowKey,
  getRowClassName,
  sort,
}: DataTableProps<T>) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((column) => {
            const canSort = Boolean(sort && column.sortKey);
            const isActive = canSort && sort?.sortBy === column.sortKey;
            const sortOrder = sort?.sortOrder;

            function handleSortClick() {
              if (!sort || !column.sortKey) return;
              if (sort.sortBy === column.sortKey) {
                sort.onSortChange(
                  column.sortKey,
                  sortOrder === "asc" ? "desc" : "asc",
                );
                return;
              }
              sort.onSortChange(column.sortKey, "desc");
            }

            return (
              <TableHead
                key={column.key}
                className={cn(column.headerClassName)}
              >
                {canSort ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="-ml-3 h-8 gap-1 font-medium"
                    onClick={handleSortClick}
                  >
                    {column.header}
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
                ) : (
                  column.header
                )}
              </TableHead>
            );
          })}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((item) => (
          <TableRow key={getRowKey(item)} className={getRowClassName?.(item)}>
            {columns.map((column) => (
              <TableCell key={column.key} className={cn(column.className)}>
                {column.cell(item)}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
