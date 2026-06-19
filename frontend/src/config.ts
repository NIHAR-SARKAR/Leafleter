function normalizeApiUrl(url: string): string {
  let normalized = url.trim();
  // Avoid double /api/v1 if the env value already includes it.
  normalized = normalized.replace(/\/api\/v1\/?$/, "");
  normalized = normalized.replace(/\/+$/, "");
  return normalized || "http://localhost:8085";
}

export const CONFIG = {
  apiUrl: normalizeApiUrl(import.meta.env.VITE_API_URL || "http://localhost:8085"),
  timeout: Number(import.meta.env.VITE_TIMEOUT || 30000),
};
