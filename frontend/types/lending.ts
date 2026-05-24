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
