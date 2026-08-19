// Canonical User type matching the backend API response for /auth/me and user objects
export interface User {
  uuid: string;
  full_name: string;
  email: string;
  theme?: "light" | "dark" | string;
  created_at?: string;
  is_2fa_enabled?: boolean;
  two_factor_enabled?: boolean;
  phone?: string;
  country_code?: string;
  location?: string;
  timezone?: string;
  profile_image?: string;
}
