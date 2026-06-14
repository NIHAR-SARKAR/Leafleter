export const CONFIG = {
  apiUrl: import.meta.env.VITE_API_URL || "http://localhost:8081",
  timeout: Number(import.meta.env.VITE_TIMEOUT || 30000),
};
