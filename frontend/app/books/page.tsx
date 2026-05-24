"use client";

import { Plus, Search } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { BookFormModal } from "@/components/books/BookFormModal";
import {
  BookTable,
  type TitleSortDirection,
} from "@/components/books/BookTable";
import { AppLayout } from "@/components/layout/AppLayout";
import { DeactivateConfirmDialog } from "@/components/shared/DeactivateConfirmDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { bookService } from "@/services";
import type { Book } from "@/types";

const PAGE_SIZE = 10;

function sortByTitle(books: Book[], direction: TitleSortDirection): Book[] {
  return [...books].sort((a, b) => {
    const cmp = a.title.localeCompare(b.title, undefined, {
      sensitivity: "base",
    });
    return direction === "asc" ? cmp : -cmp;
  });
}

function BooksPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [books, setBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortDirection, setSortDirection] =
    useState<TitleSortDirection>("asc");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [showInactive, setShowInactive] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isDeactivateModalOpen, setIsDeactivateModalOpen] = useState(false);

  const loadBooks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await bookService.getAll(0, 1000, showInactive);
      setBooks(data);
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
  }, [showInactive]);

  useEffect(() => {
    void loadBooks();
  }, [loadBooks]);

  useEffect(() => {
    if (searchParams.get("action") === "add") {
      setEditingBook(null);
      setModalOpen(true);
      router.replace("/books", { scroll: false });
    }
  }, [searchParams, router]);

  const filteredBooks = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return books;
    }
    return books.filter(
      (book) =>
        book.title.toLowerCase().includes(query) ||
        book.author.toLowerCase().includes(query),
    );
  }, [books, search]);

  const sortedBooks = useMemo(
    () => sortByTitle(filteredBooks, sortDirection),
    [filteredBooks, sortDirection],
  );

  const totalPages = Math.max(1, Math.ceil(sortedBooks.length / PAGE_SIZE));

  const paginatedBooks = useMemo(() => {
    const safePage = Math.min(page, totalPages);
    const start = (safePage - 1) * PAGE_SIZE;
    return sortedBooks.slice(start, start + PAGE_SIZE);
  }, [sortedBooks, page, totalPages]);

  useEffect(() => {
    setPage(1);
  }, [search, sortDirection]);

  useEffect(() => {
    if (page > totalPages) {
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
    }
  }

  function toggleSort() {
    setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
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

  const isEmpty = !isLoading && !error && sortedBooks.length === 0;

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
            <div className="relative max-w-md flex-1">
              <Search
                className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden
              />
              <Input
                type="search"
                placeholder="Search by title or author…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8"
                disabled={isLoading}
              />
            </div>
          </div>
          <Button onClick={openCreateModal} className="shrink-0 gap-2">
            <Plus className="size-4" aria-hidden />
            Add Book
          </Button>
        </div>

        {error ? <ErrorMessage message={error} /> : null}

        {isLoading ? (
          <LoadingSkeleton rows={6} columns={8} />
        ) : isEmpty ? (
          <EmptyState
            message="No books found"
            actionLabel="Add Book"
            onAction={openCreateModal}
          />
        ) : (
          <>
            <BookTable
              books={paginatedBooks}
              sortDirection={sortDirection}
              onSortChange={toggleSort}
              onEdit={openEditModal}
              onDeactivate={handleDeactivate}
              onRestore={handleRestore}
            />

            {totalPages > 1 ? (
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm text-muted-foreground">
                  Showing {(page - 1) * PAGE_SIZE + 1}–
                  {Math.min(page * PAGE_SIZE, sortedBooks.length)} of{" "}
                  {sortedBooks.length}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    Previous
                  </Button>
                  <span className="text-sm tabular-nums">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            ) : null}
          </>
        )}
      </div>

      <BookFormModal
        open={modalOpen}
        onOpenChange={handleModalOpenChange}
        book={editingBook}
        onSuccess={() => void loadBooks()}
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
