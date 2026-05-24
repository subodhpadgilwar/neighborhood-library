"use client";

import { startOfDay } from "date-fns";
import { Loader2 } from "lucide-react";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { toast } from "sonner";

import { formatLoanDate } from "@/components/lending/loanUtils";
import { SearchableSelect } from "@/components/lending/SearchableSelect";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  dateInputToApiIso,
  defaultDueDateFromToday,
  formatDate,
  formatDateInputValue,
  isCalendarDayBefore,
} from "@/lib/dateUtils";
import { cn } from "@/lib/utils";
import { bookService, lendingService, memberService } from "@/services";
import type { Book, Member } from "@/types";

type ApiClientError = {
  status: string;
  message: string;
};

interface BorrowModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function BorrowModal({ open, onOpenChange, onSuccess }: BorrowModalProps) {
  const [members, setMembers] = useState<Member[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [dueDateInput, setDueDateInput] = useState("");
  const [dueDateError, setDueDateError] = useState<string | null>(null);
  const [isLoadingOptions, setIsLoadingOptions] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);

  const todayInput = formatDateInputValue(startOfDay(new Date()));
  const defaultDueDateLabel = formatDate(
    defaultDueDateFromToday(14).toISOString(),
  );

  const activeMembers = useMemo(
    () => members.filter((member) => member.is_active),
    [members],
  );

  const availableBooks = useMemo(
    () =>
      books.filter((book) => book.is_active && book.copies_available > 0),
    [books],
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    setSelectedMember(null);
    setSelectedBook(null);
    setDueDateInput("");
    setDueDateError(null);
    setApiError(null);
    setFieldError(null);

    let cancelled = false;

    async function loadOptions() {
      setIsLoadingOptions(true);
      try {
        const [membersData, booksData] = await Promise.all([
          memberService.getAll(0, 1000),
          bookService.getAll(0, 1000),
        ]);
        if (!cancelled) {
          setMembers(membersData);
          setBooks(booksData);
        }
      } catch {
        if (!cancelled) {
          setApiError("Failed to load members and books.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingOptions(false);
        }
      }
    }

    void loadOptions();

    return () => {
      cancelled = true;
    };
  }, [open]);

  function validateDueDate(): boolean {
    if (!dueDateInput) {
      setDueDateError(null);
      return true;
    }
    if (isCalendarDayBefore(dueDateInput, todayInput)) {
      setDueDateError("Due date cannot be in the past");
      return false;
    }
    setDueDateError(null);
    return true;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldError(null);
    setApiError(null);

    if (!selectedMember || !selectedBook) {
      setFieldError("Please select both a member and a book.");
      return;
    }

    if (!validateDueDate()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const lending = await lendingService.borrowBook({
        member_id: selectedMember.id,
        book_id: selectedBook.id,
        ...(dueDateInput ? { due_date: dateInputToApiIso(dueDateInput) } : {}),
      });
      toast.success(
        `Book borrowed successfully. Due: ${formatLoanDate(lending.due_date)}`,
      );
      setSelectedMember(null);
      setSelectedBook(null);
      setDueDateInput("");
      setFieldError(null);
      onOpenChange(false);
      onSuccess();
    } catch (err) {
      const error = err as ApiClientError;
      setApiError(
        typeof error?.message === "string"
          ? error.message
          : "Failed to borrow book.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Borrow Book</DialogTitle>
          <DialogDescription>
            Select a member and an available book to create a loan.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Member</Label>
            <SearchableSelect
              items={activeMembers}
              value={selectedMember}
              onChange={setSelectedMember}
              getKey={(m) => m.id}
              getSearchText={(m) => `${m.name} ${m.email}`}
              placeholder="Select member…"
              searchPlaceholder="Search members…"
              disabled={isLoadingOptions || isSubmitting}
              emptyMessage="No members found."
              renderValue={(m) => (
                <span>
                  {m.name}{" "}
                  <span className="text-muted-foreground">({m.email})</span>
                </span>
              )}
              renderItem={(m) => (
                <span>
                  <span className="font-medium">{m.name}</span>
                  <br />
                  <span className="text-xs text-muted-foreground">
                    {m.email}
                  </span>
                </span>
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>Book</Label>
            <SearchableSelect
              items={availableBooks}
              value={selectedBook}
              onChange={setSelectedBook}
              getKey={(b) => b.id}
              getSearchText={(b) => `${b.title} ${b.author}`}
              placeholder="Select book…"
              searchPlaceholder="Search books…"
              disabled={isLoadingOptions || isSubmitting}
              emptyMessage="No available books."
              renderValue={(b) => (
                <span>
                  {b.title}{" "}
                  <span className="text-muted-foreground">by {b.author}</span>
                </span>
              )}
              renderItem={(b) => (
                <span>
                  <span className="font-medium">{b.title}</span>
                  <br />
                  <span className="text-xs text-muted-foreground">
                    {b.author} · {b.copies_available} copies left
                  </span>
                </span>
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="borrow-due-date">Due Date (optional)</Label>
            <Input
              id="borrow-due-date"
              type="date"
              min={todayInput}
              value={dueDateInput}
              onChange={(e) => {
                setDueDateInput(e.target.value);
                setDueDateError(null);
                setApiError(null);
              }}
              disabled={isSubmitting}
              className={cn(
                "w-full",
                "[&::-webkit-calendar-picker-indicator]:cursor-pointer",
              )}
              aria-invalid={Boolean(dueDateError)}
            />
            <p className="text-xs text-muted-foreground">
              Leave empty to use default 14-day period (due: {defaultDueDateLabel}
              )
            </p>
            {dueDateError ? (
              <p className="text-xs text-destructive">{dueDateError}</p>
            ) : null}
          </div>

          {fieldError ? (
            <p className="text-sm text-destructive">{fieldError}</p>
          ) : null}
          {apiError ? (
            <p role="alert" className="text-sm text-destructive">
              {apiError}
            </p>
          ) : null}

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || isLoadingOptions}>
              {isSubmitting ? (
                <>
                  <Loader2 className="animate-spin" />
                  Loading...
                </>
              ) : (
                "Borrow Book"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
