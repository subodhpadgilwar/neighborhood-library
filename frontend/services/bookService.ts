import { api } from "@/lib/api";
import type { Book, BookCreate, BookUpdate } from "@/types";

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
