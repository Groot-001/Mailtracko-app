import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

export const api = axios.create({
  // Keep one API base contract for local proxy and deployed builds.
  baseURL: API_BASE_URL,
  withCredentials: true,
  // Let Axios infer Content-Type per request. A global application/json header
  // breaks FormData uploads because the browser cannot add the multipart boundary.
});

// Authentication is carried by the backend-owned HttpOnly session cookie. Do
// not copy the session identifier
// into JavaScript-readable storage or an Authorization header.

const IGNORE_401_ENDPOINTS = [
  "/auth/login",
  "/auth/signup",
  "/auth/email/verify",
  "/auth/me",
  "/auth/logout",
  "/auth/2fa/verify-login",
];

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url: string = error.config?.url ?? "";

    const isAuthFlowRequest = IGNORE_401_ENDPOINTS.some((endpoint) =>
      url.includes(endpoint),
    );

    if (error.response?.status === 401 && !isAuthFlowRequest) {
      window.location.href = "/login";
    }

    return Promise.reject(error);
  },
);
