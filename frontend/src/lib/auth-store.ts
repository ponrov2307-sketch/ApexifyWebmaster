import { create } from "zustand";
import api from "./api";

export interface User {
  user_id: string;
  username: string;
  role: string;
  status: string;
  vip_expiry: string | null;
  telegram_id?: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (telegramId: string, password: string) => Promise<void>;
  tokenLogin: (token: string) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => void;
  refreshUser: () => Promise<void>;
}

function setAuthCookie(token: string) {
  // Set cookie so middleware can validate server-side
  document.cookie = `access_token=${token}; path=/; max-age=${60 * 60 * 24}; SameSite=Lax`;
}

function clearAuthCookie() {
  document.cookie = "access_token=; path=/; max-age=0";
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: true,

  login: async (telegramId, password) => {
    const { data } = await api.post("/api/auth/login", {
      telegram_id: telegramId,
      password,
    });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setAuthCookie(data.access_token);
    set({ user: data.user });
  },

  tokenLogin: async (token) => {
    const { data } = await api.post("/api/auth/token-login", { token });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setAuthCookie(data.access_token);
    set({ user: data.user });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    clearAuthCookie();
    set({ user: null });
    window.location.href = "/login";
  },

  loadFromStorage: () => {
    const raw = localStorage.getItem("user");
    const token = localStorage.getItem("access_token");
    if (raw && token) {
      try {
        // Keep cookie in sync
        setAuthCookie(token);
        set({ user: JSON.parse(raw), loading: false });
        return;
      } catch {
        /* corrupted */
      }
    }
    set({ user: null, loading: false });
  },

  refreshUser: async () => {
    try {
      // Re-issue JWT with latest DB role (handles role promotions without re-login)
      const { data } = await api.post("/api/auth/refresh");
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      // Keep cookie in sync
      document.cookie = `access_token=${data.access_token}; path=/; max-age=${60 * 60 * 24}; SameSite=Lax`;
      set({ user: data.user });
    } catch {
      /* token invalid — interceptor handles redirect */
    }
  },
}));
