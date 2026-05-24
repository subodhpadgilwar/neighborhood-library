export interface Member {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  address: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string | null;
  updated_by: string | null;
}

export interface MemberCreate {
  name: string;
  email: string;
  phone?: string;
  address?: string;
}

export interface MemberUpdate {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
}
