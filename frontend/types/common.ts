export interface ApiError {
  status: string;
  message: string;
}

export interface ValidationError {
  status: string;
  message: string;
  errors: { field: string; message: string }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
