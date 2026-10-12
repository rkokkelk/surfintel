import { getToken } from "./api";

export interface TokenClaims {
  sub: string;
  org_id: string;
  role: "admin" | "viewer";
  is_platform_admin: boolean;
  exp: number;
  iat: number;
}

/** Decodes the stored JWT's payload for UI gating only (show/hide nav items,
 * redirect from admin-only pages) — never trust this for actual authorization,
 * the backend re-checks every write with its own `require_platform_admin`.
 */
export function getClaims(): TokenClaims | null {
  const token = getToken();
  if (!token) return null;

  try {
    const payload = token.split(".")[1];
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    return JSON.parse(atob(padded)) as TokenClaims;
  } catch {
    return null;
  }
}

export function isPlatformAdmin(): boolean {
  return getClaims()?.is_platform_admin ?? false;
}
