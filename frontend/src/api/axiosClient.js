/**
 * Axios client with JWT interceptors.
 * - Attaches access token to every request.
 * - Automatically refreshes expired tokens (401) using the refresh token.
 * - On refresh failure, redirects to /401.
 * - On 500, redirects to /500.
 */
import axios from "axios";
import { useAuthStore } from "../contexts/authStore";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const axiosClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// ── Request interceptor: inject access token ─────────────────────────────────
axiosClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 + token refresh ─────────────────────────
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  failedQueue = [];
};

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const isAuthEndpoint = originalRequest.url?.includes("/auth/login") ||
                           originalRequest.url?.includes("/auth/refresh");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return axiosClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = useAuthStore.getState().refreshToken;
      try {
        const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });
        useAuthStore.getState().setTokens(data.access, refreshToken);
        processQueue(null, data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return axiosClient(originalRequest);
      } catch (err) {
        processQueue(err, null);
        useAuthStore.getState().logout();
        window.location.replace("/401");
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    // 500-range errors → server error page (skip if caller opted out)
    if (error.response?.status >= 500 && !originalRequest?._skipGlobalError) {
      window.location.replace("/500");
    }

    return Promise.reject(error);
  }
);

export default axiosClient;
