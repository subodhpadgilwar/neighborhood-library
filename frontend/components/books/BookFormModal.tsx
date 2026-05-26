"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { FormDialog } from "@/components/shared/FormDialog";
import { LocationScanner } from "@/components/shared/LocationScanner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { bookService } from "@/services";
import type { Book, BookCreate, BookUpdate } from "@/types";

type ApiClientError = {
  status: string;
  message: string;
};

interface BookFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  book?: Book | null;
  initialISBN?: string;
  onSuccess: () => void;
}

interface FormState {
  title: string;
  author: string;
  isbn: string;
  genre: string;
  shelf_location: string;
  copies_total: string;
}

const emptyForm: FormState = {
  title: "",
  author: "",
  isbn: "",
  genre: "",
  shelf_location: "",
  copies_total: "1",
};

function bookToForm(book: Book): FormState {
  return {
    title: book.title,
    author: book.author,
    isbn: book.isbn ?? "",
    genre: book.genre ?? "",
    shelf_location: book.shelf_location ?? "",
    copies_total: String(book.copies_total),
  };
}

export function BookFormModal({
  open,
  onOpenChange,
  book,
  initialISBN,
  onSuccess,
}: BookFormModalProps) {
  const isEdit = book != null;
  const [form, setForm] = useState<FormState>(emptyForm);
  const [fieldErrors, setFieldErrors] = useState<Partial<FormState>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useDeferredEffect(() => {
    if (!open) {
      return;
    }
    setForm(
      book
        ? bookToForm(book)
        : { ...emptyForm, isbn: initialISBN?.trim() ?? "" },
    );
    setFieldErrors({});
    setApiError(null);
  }, [open, book, initialISBN]);

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => ({ ...prev, [key]: undefined }));
    setApiError(null);
  }

  function validate(): boolean {
    const errors: Partial<FormState> = {};
    if (!form.title.trim()) {
      errors.title = "Title is required";
    }
    if (!form.author.trim()) {
      errors.author = "Author is required";
    }
    const copies = Number(form.copies_total);
    if (!form.copies_total.trim() || Number.isNaN(copies) || copies < 1) {
      errors.copies_total = "Total copies must be at least 1";
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validate()) {
      return;
    }

    const payload = {
      title: form.title.trim(),
      author: form.author.trim(),
      isbn: form.isbn.trim() || undefined,
      genre: form.genre.trim() || undefined,
      shelf_location: form.shelf_location.trim() || undefined,
      copies_total: Number(form.copies_total),
    };

    setIsSubmitting(true);
    setApiError(null);

    try {
      if (isEdit && book) {
        await bookService.update(book.id, payload as BookUpdate);
        toast.success("Book updated");
      } else {
        await bookService.create(payload as BookCreate);
        toast.success("Book added successfully");
      }
      setForm(emptyForm);
      setFieldErrors({});
      onOpenChange(false);
      onSuccess();
    } catch (err) {
      const error = err as ApiClientError;
      setApiError(
        typeof error?.message === "string"
          ? error.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit Book" : "Add Book"}
      description={
        isEdit
          ? "Update book details below."
          : "Enter details for a new book in the catalog."
      }
      submitLabel={isEdit ? "Save Changes" : "Add Book"}
      isSubmitting={isSubmitting}
      apiError={apiError}
      onSubmit={handleSubmit}
    >
          <div className="space-y-2">
            <Label htmlFor="book-title">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="book-title"
              value={form.title}
              onChange={(e) => updateField("title", e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.title)}
            />
            {fieldErrors.title ? (
              <p className="text-xs text-destructive">{fieldErrors.title}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="book-author">
              Author <span className="text-destructive">*</span>
            </Label>
            <Input
              id="book-author"
              value={form.author}
              onChange={(e) => updateField("author", e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.author)}
            />
            {fieldErrors.author ? (
              <p className="text-xs text-destructive">{fieldErrors.author}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="book-isbn">ISBN</Label>
            <Input
              id="book-isbn"
              value={form.isbn}
              onChange={(e) => updateField("isbn", e.target.value)}
              disabled={isSubmitting}
              placeholder="13-digit ISBN"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="book-genre">Genre</Label>
            <Input
              id="book-genre"
              value={form.genre}
              onChange={(e) => updateField("genre", e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <Label>Shelf Location (optional)</Label>
            <LocationScanner
              value={form.shelf_location}
              onChange={(value) => updateField("shelf_location", value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="book-copies">
              Total Copies <span className="text-destructive">*</span>
            </Label>
            <Input
              id="book-copies"
              type="number"
              min={1}
              value={form.copies_total}
              onChange={(e) => updateField("copies_total", e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.copies_total)}
            />
            {fieldErrors.copies_total ? (
              <p className="text-xs text-destructive">
                {fieldErrors.copies_total}
              </p>
            ) : null}
          </div>

    </FormDialog>
  );
}
