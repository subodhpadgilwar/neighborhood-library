import axios from "axios";

import { api } from "@/lib/api";
import type { Book, BookCreate, BookUpdate } from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getAll(
  skip = 0,
  limit = 100,
  includeInactive = false,
): Promise<Book[]> {
  const { data } = await api.get<Book[]>("/books", {
    params: { skip, limit, include_inactive: includeInactive },
  });
  return data;
}

export async function getById(id: string): Promise<Book> {
  const { data } = await api.get<Book>(`/books/${id}`);
  return data;
}

export async function getByISBN(isbn: string): Promise<Book> {
  try {
    const { data } = await axios.get<Book>(
      `${API_BASE_URL}/api/v1/books/isbn/${encodeURIComponent(isbn)}`,
    );
    return data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
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
  const { data } = await api.post<Book>("/books", book);
  return data;
}

export async function update(id: string, book: BookUpdate): Promise<Book> {
  const { data } = await api.put<Book>(`/books/${id}`, book);
  return data;
}

export async function deactivate(id: string): Promise<Book> {
  const { data } = await api.delete<Book>(`/books/${id}`);
  return data;
}

export async function restore(id: string): Promise<Book> {
  const { data } = await api.put<Book>(`/books/${id}/restore`);
  return data;
}
