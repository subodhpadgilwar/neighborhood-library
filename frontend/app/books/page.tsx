"use client";

import { Camera, Plus, Search } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useState } from "react";
import { toast } from "sonner";

import { BookFormModal } from "@/components/books/BookFormModal";
import {
  BookTable,
  type TitleSortDirection,
} from "@/components/books/BookTable";
import { AppLayout } from "@/components/layout/AppLayout";
import { BarcodeScanner } from "@/components/shared/BarcodeScanner";
import { DeactivateConfirmDialog } from "@/components/shared/DeactivateConfirmDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Pagination } from "@/components/shared/Pagination";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { normalizeISBNFromScan } from "@/lib/isbnUtils";
import { bookService } from "@/services";
import type { Book } from "@/types";

const DEFAULT_PAGE_SIZE = 10;

function BooksPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [books, setBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebouncedValue(searchInput);
  const [sortDirection, setSortDirection] =
    useState<TitleSortDirection>("asc");
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(DEFAULT_PAGE_SIZE);
  const [totalBooks, setTotalBooks] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [showInactive, setShowInactive] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isDeactivateModalOpen, setIsDeactivateModalOpen] = useState(false);
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [highlightedBookId, setHighlightedBookId] = useState<string | null>(
    null,
  );
  const [initialISBN, setInitialISBN] = useState<string | undefined>();

  const loadBooks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await bookService.getPage({
        page,
        limit,
        includeInactive: showInactive,
        search: debouncedSearch,
        sortBy: "title",
        sortOrder: sortDirection,
      });
      setBooks(data.items);
      setTotalBooks(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      const apiError = err as { message?: string };
      setError(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to load books.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, limit, page, showInactive, sortDirection]);

  useDeferredEffect(() => {
    void loadBooks();
  }, [loadBooks]);

  useDeferredEffect(() => {
    if (searchParams.get("action") === "add") {
      setEditingBook(null);
      setModalOpen(true);
      router.replace("/books", { scroll: false });
    }
  }, [searchParams, router]);

  useDeferredEffect(() => {
    setPage(1);
  }, [debouncedSearch, showInactive, sortDirection]);

  useDeferredEffect(() => {
    if (totalPages > 0 && page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  function openCreateModal() {
    setEditingBook(null);
    setModalOpen(true);
  }

  function openEditModal(book: Book) {
    setEditingBook(book);
    setModalOpen(true);
  }

  function handleModalOpenChange(open: boolean) {
    setModalOpen(open);
    if (!open) {
      setEditingBook(null);
      setInitialISBN(undefined);
    }
  }

  async function handleBookPageScan(rawIsbn: string) {
    const isbn = normalizeISBNFromScan(rawIsbn);
    setIsScannerOpen(false);

    try {
      const book = await bookService.getByISBN(isbn);
      setSearchInput(book.title);
      setHighlightedBookId(book.id);
      setPage(1);
      toast.success(`Book found: ${book.title}`);
    } catch (err) {
      const error = err as { statusCode?: number; status?: string };
      if (error.statusCode === 404 || error.status === "not_found") {
        toast.error("Book not found. Add it first?");
        setInitialISBN(isbn);
        setEditingBook(null);
        setModalOpen(true);
        return;
      }
      toast.error("Failed to look up book by ISBN.");
    }
  }

  function toggleSort() {
    setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
  }

  function handleLimitChange(nextLimit: number) {
    setLimit(nextLimit);
    setPage(1);
  }

  function handleDeactivate(book: Book) {
    setSelectedBook(book);
    setIsDeactivateModalOpen(true);
  }

  async function handleRestore(book: Book) {
    try {
      await bookService.restore(book.id);
      toast.success("Book restored successfully");
      void loadBooks();
    } catch (err) {
      const apiError = err as { message?: string };
      toast.error(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to restore book.",
      );
    }
  }

  function handleDeactivateSuccess() {
    setIsDeactivateModalOpen(false);
    setSelectedBook(null);
    void loadBooks();
  }

  const isEmpty = !isLoading && !error && books.length === 0;

  return (
    <AppLayout title="Books">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-center">
            <div className="flex items-center gap-3">
              <Switch
                id="show-inactive-books"
                checked={showInactive}
                onCheckedChange={setShowInactive}
                disabled={isLoading}
              />
              <Label htmlFor="show-inactive-books" className="cursor-pointer">
                Show inactive
              </Label>
            </div>
            <div className="flex max-w-md flex-1 gap-2">
              <div className="relative min-w-0 flex-1">
                <Search
                  className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
                  aria-hidden
                />
                <Input
                  type="search"
                  placeholder="Search by title or author…"
                  value={searchInput}
                  onChange={(e) => {
                    setSearchInput(e.target.value);
                    setHighlightedBookId(null);
                  }}
                  className="pl-8"
                  disabled={isLoading}
                />
              </div>
              <Button
                type="button"
                variant="outline"
                className="shrink-0 gap-1.5"
                onClick={() => setIsScannerOpen(true)}
                disabled={isLoading}
                title="Scan book barcode or QR code"
              >
                <Camera className="size-4" aria-hidden />
                Scan
              </Button>
            </div>
          </div>
          <Button onClick={openCreateModal} className="shrink-0 gap-2">
            <Plus className="size-4" aria-hidden />
            Add Book
          </Button>
        </div>

        {error ? <ErrorMessage message={error} /> : null}

        {isLoading ? (
          <LoadingSkeleton rows={6} columns={9} />
        ) : isEmpty ? (
          <EmptyState
            message="No books found"
            actionLabel="Add Book"
            onAction={openCreateModal}
          />
        ) : (
          <>
            <BookTable
              books={books}
              sortDirection={sortDirection}
              highlightedBookId={highlightedBookId}
              onSortChange={toggleSort}
              onEdit={openEditModal}
              onDeactivate={handleDeactivate}
              onRestore={handleRestore}
            />

            <Pagination
              currentPage={page}
              totalPages={totalPages}
              totalItems={totalBooks}
              itemsPerPage={limit}
              onPageChange={setPage}
              onLimitChange={handleLimitChange}
            />
          </>
        )}
      </div>

      <BookFormModal
        open={modalOpen}
        onOpenChange={handleModalOpenChange}
        book={editingBook}
        initialISBN={initialISBN}
        onSuccess={() => void loadBooks()}
      />

      <BarcodeScanner
        isOpen={isScannerOpen}
        onClose={() => setIsScannerOpen(false)}
        onScan={handleBookPageScan}
        title="Scan Book Barcode"
      />

      <DeactivateConfirmDialog
        isOpen={isDeactivateModalOpen}
        onClose={() => setIsDeactivateModalOpen(false)}
        onSuccess={handleDeactivateSuccess}
        entityType="book"
        entityName={selectedBook?.title ?? ""}
        id={selectedBook?.id ?? ""}
        onConfirm={bookService.deactivate}
      />
    </AppLayout>
  );
}

function BooksPageFallback() {
  return (
    <AppLayout title="Books">
      <LoadingSkeleton rows={6} columns={8} />
    </AppLayout>
  );
}

export default function BooksPage() {
  return (
    <Suspense fallback={<BooksPageFallback />}>
      <BooksPageContent />
    </Suspense>
  );
}
