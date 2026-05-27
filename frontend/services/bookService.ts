import { isAxiosError } from "axios";

import { api } from "@/lib/api";
import { apiPaths } from "@/lib/apiPaths";
import type { Book, BookCreate, BookListResponse, BookUpdate } from "@/types";

interface BookPageParams {
  page?: number;
  limit?: number;
  includeInactive?: boolean;
  search?: string;
  genre?: string;
  sortBy?: "title" | "author" | "genre" | "created_at";
  sortOrder?: "asc" | "desc";
}

export async function getPage({
  page = 1,
  limit = 100,
  includeInactive = false,
  search,
  genre,
  sortBy = "title",
  sortOrder = "asc",
}: BookPageParams = {}): Promise<BookListResponse> {
  const { data } = await api.get<BookListResponse>(apiPaths.books.list, {
    params: {
      page,
      limit,
      include_inactive: includeInactive,
      search: search?.trim() || undefined,
      genre: genre?.trim() || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  return data;
}

export async function getAll(
  page = 1,
  limit = 100,
  includeInactive = false,
): Promise<Book[]> {
  const data = await getPage({ page, limit, includeInactive });
  return data.items;
}

export async function getById(id: string): Promise<Book> {
  const { data } = await api.get<Book>(apiPaths.books.byId(id));
  return data;
}

export async function getByISBN(isbn: string): Promise<Book> {
  try {
    const { data } = await api.get<Book>(apiPaths.books.byISBN(isbn));
    return data;
  } catch (error) {
    if (isAxiosError(error)) {
      if (error.response?.status === 404) {
        throw {
          status: "not_found",
          message: "Book not found",
          statusCode: 404,
        };
      }
      const detail = error.response?.data;
      const message =
        detail && typeof detail.detail === "string"
          ? detail.detail
          : detail && typeof detail.message === "string"
            ? detail.message
            : "Failed to look up book by ISBN";
      throw { status: "error", message, statusCode: error.response?.status };
    }
    throw { status: "error", message: "Failed to look up book by ISBN" };
  }
}

export async function create(book: BookCreate): Promise<Book> {
  const { data } = await api.post<Book>(apiPaths.books.list, book);
  return data;
}

export async function update(id: string, book: BookUpdate): Promise<Book> {
  const { data } = await api.put<Book>(apiPaths.books.byId(id), book);
  return data;
}

export async function deactivate(id: string): Promise<Book> {
  const { data } = await api.delete<Book>(apiPaths.books.byId(id));
  return data;
}

export async function restore(id: string): Promise<Book> {
  const { data } = await api.put<Book>(apiPaths.books.restore(id));
  return data;
}
