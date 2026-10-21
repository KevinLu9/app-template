// Types mirroring the backend's JSON responses.

export type CurrentUser = {
  user_id: string;
  email: string;
  display_name: string;
  groups: string[] | null;
};

export type Item = {
  id: number;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type ItemInput = { name: string; description?: string | null };
