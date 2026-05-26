"use client";

import { startOfDay } from "date-fns";
import { AlertTriangle, Camera, Check, Loader2, X } from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";
import { toast } from "sonner";

import { formatLoanDate } from "@/components/lending/loanUtils";
import { SearchableSelect } from "@/components/lending/SearchableSelect";
import { BarcodeScanner } from "@/components/shared/BarcodeScanner";
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
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { normalizeISBNFromScan } from "@/lib/isbnUtils";
import { cn } from "@/lib/utils";
import { bookService, lendingService, memberService } from "@/services";
import type { Book, Member } from "@/types";

type ApiClientError = {
  status: string;
  message: string;
  statusCode?: number;
};

type ScanStatus = "idle" | "scanning" | "found" | "not_found" | "error";

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
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [scanStatus, setScanStatus] = useState<ScanStatus>("idle");
  const [scannedISBN, setScannedISBN] = useState<string | null>(null);
  const [scannedBook, setScannedBook] = useState<Book | null>(null);
  const [scanErrorMessage, setScanErrorMessage] = useState<string | null>(null);

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

  const bookSelectItems = useMemo(() => {
    if (
      scannedBook &&
      !availableBooks.some((book) => book.id === scannedBook.id)
    ) {
      return [...availableBooks, scannedBook];
    }
    return availableBooks;
  }, [availableBooks, scannedBook]);

  useDeferredEffect(() => {
    if (!open) {
      return;
    }

    setSelectedMember(null);
    setSelectedBook(null);
    setDueDateInput("");
    setDueDateError(null);
    setApiError(null);
    setFieldError(null);
    setIsScannerOpen(false);
    setScanStatus("idle");
    setScannedISBN(null);
    setScannedBook(null);
    setScanErrorMessage(null);

    let cancelled = false;

    async function loadOptions() {
      setIsLoadingOptions(true);
      try {
        const [membersData, booksData] = await Promise.all([
          memberService.getAll(1, 1000),
          bookService.getAll(1, 1000),
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

  function clearScanStatus() {
    setScanStatus("idle");
    setScannedISBN(null);
    setScannedBook(null);
    setScanErrorMessage(null);
  }

  function handleBookChange(book: Book) {
    setSelectedBook(book);
    if (scannedBook && book.id !== scannedBook.id) {
      clearScanStatus();
    }
  }

  async function handleScan(rawIsbn: string) {
    const isbn = normalizeISBNFromScan(rawIsbn);
    setIsScannerOpen(false);
    setScannedISBN(isbn);
    setScanStatus("scanning");
    setScannedBook(null);
    setScanErrorMessage(null);

    try {
      const book = await bookService.getByISBN(isbn);
      setScannedBook(book);
      setSelectedBook(book);
      setScanStatus("found");
    } catch (err) {
      const error = err as ApiClientError;
      if (error.statusCode === 404 || error.status === "not_found") {
        setScanStatus("not_found");
        return;
      }
      setScanStatus("error");
      setScanErrorMessage(
        typeof error?.message === "string"
          ? error.message
          : "Failed to look up book by ISBN.",
      );
    }
  }

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
      clearScanStatus();
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
            <div className="flex gap-2">
              <div className="min-w-0 flex-1">
                <SearchableSelect
                  items={bookSelectItems}
                  value={selectedBook}
                  onChange={handleBookChange}
                  getKey={(b) => b.id}
                  getSearchText={(b) => `${b.title} ${b.author} ${b.isbn ?? ""}`}
                  placeholder="Select book…"
                  searchPlaceholder="Search books…"
                  disabled={isLoadingOptions || isSubmitting}
                  emptyMessage="No available books."
                  renderValue={(b) => (
                    <span>
                      {b.title}{" "}
                      <span className="text-muted-foreground">
                        by {b.author}
                      </span>
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
              <Button
                type="button"
                variant="outline"
                className="shrink-0 gap-1.5"
                onClick={() => setIsScannerOpen(true)}
                disabled={isLoadingOptions || isSubmitting}
                title="Scan book barcode or QR code"
              >
                <Camera className="size-4" aria-hidden />
                Scan
              </Button>
            </div>

            {scanStatus === "scanning" ? (
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" aria-hidden />
                Looking up book…
              </p>
            ) : null}

            {scanStatus === "found" && scannedBook && scannedISBN ? (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100">
                <p className="flex items-start gap-2 font-medium">
                  <Check className="mt-0.5 size-4 shrink-0" aria-hidden />
                  <span>
                    Book found: &ldquo;{scannedBook.title}&rdquo; by{" "}
                    {scannedBook.author}
                  </span>
                </p>
                <p className="mt-1 pl-6 text-xs opacity-90">
                  ISBN: {scannedISBN} · {scannedBook.copies_available} copies
                  available
                </p>
                <button
                  type="button"
                  className="mt-2 pl-6 text-xs underline underline-offset-2"
                  onClick={() => setIsScannerOpen(true)}
                >
                  Scan Again
                </button>
              </div>
            ) : null}

            {scanStatus === "not_found" && scannedISBN ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
                <p className="flex items-start gap-2 font-medium">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
                  <span>No book found with ISBN {scannedISBN}</span>
                </p>
                <p className="mt-1 pl-6 text-xs opacity-90">
                  Please add this book first or select manually
                </p>
                <button
                  type="button"
                  className="mt-2 pl-6 text-xs underline underline-offset-2"
                  onClick={() => setIsScannerOpen(true)}
                >
                  Scan Again
                </button>
              </div>
            ) : null}

            {scanStatus === "error" ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <p className="flex items-start gap-2 font-medium">
                  <X className="mt-0.5 size-4 shrink-0" aria-hidden />
                  <span>{scanErrorMessage ?? "Failed to look up book."}</span>
                </p>
                <button
                  type="button"
                  className="mt-2 pl-6 text-xs underline underline-offset-2"
                  onClick={() => setIsScannerOpen(true)}
                >
                  Scan Again
                </button>
              </div>
            ) : null}
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

      <BarcodeScanner
        isOpen={isScannerOpen}
        onClose={() => setIsScannerOpen(false)}
        onScan={handleScan}
        title="Scan Book Barcode"
      />
    </Dialog>
  );
}
