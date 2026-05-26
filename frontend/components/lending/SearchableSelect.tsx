"use client";

import { Check, ChevronsUpDown } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface SearchableSelectProps<T> {
  items: T[];
  value: T | null;
  onChange: (item: T) => void;
  getKey: (item: T) => string;
  getSearchText: (item: T) => string;
  renderItem: (item: T) => ReactNode;
  renderValue: (item: T) => ReactNode;
  placeholder: string;
  searchPlaceholder?: string;
  disabled?: boolean;
  emptyMessage?: string;
}

export function SearchableSelect<T>({
  items,
  value,
  onChange,
  getKey,
  getSearchText,
  renderItem,
  renderValue,
  placeholder,
  searchPlaceholder = "Search…",
  disabled = false,
  emptyMessage = "No results found.",
}: SearchableSelectProps<T>) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return items;
    }
    return items.filter((item) =>
      getSearchText(item).toLowerCase().includes(query),
    );
  }, [items, search, getSearchText]);

  return (
    <Popover open={open} onOpenChange={setOpen} modal>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className="h-auto min-h-8 w-full justify-between py-2 font-normal"
        >
          <span className="truncate text-left">
            {value ? renderValue(value) : (
              <span className="text-muted-foreground">{placeholder}</span>
            )}
          </span>
          <ChevronsUpDown className="ml-2 size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="flex w-[var(--radix-popover-trigger-width)] max-h-72 flex-col overflow-hidden p-0"
        align="start"
        onOpenAutoFocus={(event) => event.preventDefault()}
      >
        <div className="shrink-0 border-b p-2">
          <Input
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8"
            onKeyDown={(event) => event.stopPropagation()}
          />
        </div>
        <div
          className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-1"
          onWheel={(event) => event.stopPropagation()}
          onTouchMove={(event) => event.stopPropagation()}
        >
          {filtered.length === 0 ? (
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">
              {emptyMessage}
            </p>
          ) : (
            filtered.map((item) => {
              const key = getKey(item);
              const selected = value != null && getKey(value) === key;
              return (
                <button
                  key={key}
                  type="button"
                  className={cn(
                    "flex w-full items-start gap-2 rounded-md px-2 py-2 text-left text-sm hover:bg-muted",
                    selected && "bg-muted",
                  )}
                  onClick={() => {
                    onChange(item);
                    setOpen(false);
                    setSearch("");
                  }}
                >
                  <Check
                    className={cn(
                      "mt-0.5 size-4 shrink-0",
                      selected ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <span className="flex-1">{renderItem(item)}</span>
                </button>
              );
            })
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
