export type StaffRole = "admin" | "staff";

export interface Staff {
  id: string;
  full_name: string;
  email: string;
  role: StaffRole;
  is_active: boolean;
  is_default_admin: boolean;
  created_at: string;
  updated_at: string;
}

export interface StaffCreate {
  full_name: string;
  email: string;
  password: string;
  role: StaffRole;
}

export interface StaffUpdate {
  full_name?: string;
  email?: string;
  role?: StaffRole;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface AdminChangePasswordRequest {
  new_password: string;
  confirm_password: string;
}

export type StaffListResponse = import("./common").PaginatedResponse<Staff>;
