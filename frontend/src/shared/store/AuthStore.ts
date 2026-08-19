import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "../../feature/login/types/user";

interface AuthStore {
  user: User | null;
  isLoading: boolean;

  setUser: (user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      isLoading: true,

      setUser: (user) =>
        set({
          user,
          isLoading: false,
        }),

      logout: () =>
        set({
          user: null,
          isLoading: false,
        }),

      setLoading: (loading) =>
        set({
          isLoading: loading,
        }),
    }),
    {
      name: "auth-storage",
    },
  ),
);
