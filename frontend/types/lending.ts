export interface Lending {
  id: string;
  book_title: string;
  book_author: string;
  member_name: string;
  member_email: string;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
  is_overdue: boolean;
  processed_by: string | null;
}

export interface BorrowRequest {
  book_id: string;
  member_id: string;
  due_date?: string;
}

export interface UpdateDueDateRequest {
  due_date: string;
}

export interface LendingFilters {
  status?: "active" | "returned" | "overdue";
  member_name?: string;
  book_title?: string;
  /** ISO 8601 string or any value parseable by `new Date()` */
  borrowed_from?: string;
  /** ISO 8601 string or any value parseable by `new Date()` */
  borrowed_to?: string;
  sort_by?:
    | "borrowed_at"
    | "due_date"
    | "member_name"
    | "book_title"
    | "returned_at";
  sort_order?: "asc" | "desc";
  page?: number;
  limit?: number;
}

export interface LendingHistoryResponse {
  items: Lending[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ActiveLoansResponse {
  items: Lending[];
  total: number;
  skip: number;
  limit: number;
}

export interface OverdueLoansResponse {
  items: Lending[];
  total: number;
  skip: number;
  limit: number;
}
