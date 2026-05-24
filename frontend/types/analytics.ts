export interface GenreStats {
  genre: string;
  total_books: number;
  total_copies: number;
  available_copies: number;
  percentage: number;
}

export interface MonthlyLendingStats {
  month: string;
  total_loans: number;
  returned_loans: number;
  overdue_loans: number;
  active_loans: number;
}

export interface TopBookStats {
  id: string;
  title: string;
  author: string;
  genre: string | null;
  shelf_location: string | null;
  copies_total: number;
  copies_available: number;
  total_borrows: number;
  current_borrows: number;
  utilization_rate: number;
}

export interface SummaryStats {
  total_books: number;
  total_members: number;
  active_loans: number;
  overdue_loans: number;
  total_copies: number;
  available_copies: number;
  loans_today: number;
  returns_today: number;
}
