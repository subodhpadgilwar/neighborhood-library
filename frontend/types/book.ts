export interface Book {
  id: string;
  title: string;
  author: string;
  isbn: string | null;
  genre: string | null;
  copies_total: number;
  copies_available: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string | null;
  updated_by: string | null;
}

export interface BookCreate {
  title: string;
  author: string;
  isbn?: string;
  genre?: string;
  copies_total: number;
}

export interface BookUpdate {
  title?: string;
  author?: string;
  isbn?: string;
  genre?: string;
  copies_total?: number;
}
