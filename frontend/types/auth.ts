export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface StaffResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_default_admin: boolean;
  created_at: string;
  updated_at: string;
}
