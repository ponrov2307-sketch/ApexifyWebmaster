import axios from "axios";

const api = axios.create({
  baseURL: "",
  headers: { "Content-Type": "application/json" },
});

// Attach token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// On 401, try to refresh token once; if still 401, redirect to login
let isRefreshing = false;

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      // Don't retry if already refreshing or if this was a login/me request
      const url = err.config?.url || "";
      if (isRefreshing || url.includes("/auth/login") || url.includes("/auth/token-login")) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        document.cookie = "access_token=; path=/; max-age=0";
        window.location.href = "/login";
        return Promise.reject(err);
      }

      // Try refreshing user data to check if token is still valid
      isRefreshing = true;
      try {
        const { data } = await axios.get("/api/auth/me", {
          headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
        });
        localStorage.setItem("user", JSON.stringify(data));
        isRefreshing = false;
        // Retry original request
        return api(err.config);
      } catch {
        // Token truly expired — clear and redirect
        isRefreshing = false;
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        document.cookie = "access_token=; path=/; max-age=0";
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  },
);

export default api;
