import { create } from "zustand";

type AuthState = {
  token: string | null;
  setToken: (token: string | null) => void;
  hydrateToken: () => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,

  setToken: (token) => {
    if (token) {
      localStorage.setItem("token", token);
    } else {
      localStorage.removeItem("token");
    }

    set({ token });
  },

  hydrateToken: () => {
    if (typeof window === "undefined") return;

    const token = localStorage.getItem("token");

    set({ token });
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ token: null });
  },
}));