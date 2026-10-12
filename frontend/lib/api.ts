declare global {
  interface Window {
    __ENV__?: { API_URL?: string };
  }
}

// Read at call time, not module load — window.__ENV__ is injected by a
// server-rendered <script> in app/layout.tsx so the API URL can be set per
// deployment (env var) rather than baked into the build.
export function getApiUrl(): string {
  if (typeof window !== "undefined" && window.__ENV__?.API_URL) return window.__ENV__.API_URL;
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

const TOKEN_KEY = "surfintel_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export function apiURL(path: string): string {
  return `${getApiUrl()}${path}`
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${getApiUrl()}${path}`, { ...options, headers });

  if (!response.ok) {
    if (response.status === 401) clearToken();
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function imgFetch<T>(path: string, options: RequestInit ={}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${getApiUrl()}${path}`, { ...options, headers });

  if (!response.ok) {
    if (response.status === 401) clearToken();
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }

  return (await response.blob()) as T;
}

export async function textFetch<T>(path: string, options: RequestInit={}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const response = await fetch(`${getApiUrl()}${path}`, { ...options, headers });

  return (await response.text()) as T;
}

export async function login(email: string, password: string): Promise<string> {
  const result = await apiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(result.access_token);
  return result.access_token;
}
