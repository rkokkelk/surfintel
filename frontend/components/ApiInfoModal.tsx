"use client";

import { useEffect, useState } from "react";
import { apiFetch, ApiError, API_URL } from "@/lib/api";

export function ApiInfoModal({ onClose }: { onClose: () => void }) {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  async function generateToken() {
    setLoading(true);
    setError(null);
    setCopied(false);
    try {
      const result = await apiFetch<{ access_token: string }>("/auth/api-token", { method: "POST" });
      setToken(result.access_token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kon geen API-token aanmaken.");
    } finally {
      setLoading(false);
    }
  }

  async function copyToken() {
    if (!token) return;
    await navigator.clipboard.writeText(token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div onClick={onClose} style={{ position: "absolute", inset: 0, background: "rgba(15, 23, 42, 0.35)" }} aria-hidden />

      <div
        style={{
          position: "relative",
          width: 520,
          maxWidth: "100%",
          maxHeight: "calc(100vh - 48px)",
          overflowY: "auto",
          background: "var(--si-surface)",
          borderRadius: 12,
          boxShadow: "0 12px 40px rgba(15, 23, 42, 0.2)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "16px 20px",
            borderBottom: "1px solid var(--si-border)",
            position: "sticky",
            top: 0,
            background: "var(--si-surface)",
          }}
        >
          <div className="si-display" style={{ fontSize: 15, fontWeight: 600 }}>
            API
          </div>
          <button
            type="button"
            aria-label="Sluiten"
            onClick={onClose}
            style={{
              marginLeft: "auto",
              width: 30,
              height: 30,
              border: "none",
              borderRadius: 8,
              background: "var(--si-bg)",
              color: "var(--si-text-secondary)",
              fontSize: 16,
              cursor: "pointer",
            }}
          >
            ×
          </button>
        </div>

        <div style={{ padding: "18px 20px", display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>Documentatie</div>
            <a
              href={`${API_URL}/docs`}
              target="_blank"
              rel="noreferrer"
              style={{ fontSize: 13.5, color: "var(--si-blue)" }}
            >
              {API_URL}/docs
            </a>
            <div style={{ fontSize: 12, color: "var(--si-text-muted)" }}>
              Interactieve Swagger-documentatie van alle endpoints, inclusief schema&apos;s.
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
              Bearer-token voor API-toegang
            </div>
            <div style={{ fontSize: 12, color: "var(--si-text-muted)" }}>
              Genereert een token met dezelfde rechten als je huidige account, dat niet verloopt —
              handig voor scripts en externe tooling. Bewaar 'm veilig: iedereen met dit token heeft
              dezelfde toegang als jij.
            </div>

            {!token ? (
              <button
                type="button"
                onClick={generateToken}
                disabled={loading}
                style={{
                  alignSelf: "flex-start",
                  height: 36,
                  padding: "0 16px",
                  border: "none",
                  borderRadius: 8,
                  background: "var(--si-navy)",
                  color: "#fff",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {loading ? "Genereren..." : "Genereer API-token"}
              </button>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ display: "flex", gap: 6 }}>
                  <textarea
                    readOnly
                    value={token}
                    rows={3}
                    className="si-mono"
                    onClick={(e) => (e.target as HTMLTextAreaElement).select()}
                    style={{
                      flexGrow: 1,
                      border: "1px solid #d8dce3",
                      borderRadius: 8,
                      padding: "8px 10px",
                      fontSize: 11.5,
                      resize: "vertical",
                      color: "var(--si-text)",
                      background: "var(--si-bg)",
                    }}
                  />
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    type="button"
                    onClick={copyToken}
                    style={{
                      height: 32,
                      padding: "0 14px",
                      border: "1px solid #d8dce3",
                      borderRadius: 8,
                      background: "#fff",
                      color: "#384152",
                      fontSize: 12.5,
                      fontWeight: 500,
                      cursor: "pointer",
                    }}
                  >
                    {copied ? "Gekopieerd!" : "Kopieer token"}
                  </button>
                  <button
                    type="button"
                    onClick={generateToken}
                    disabled={loading}
                    style={{
                      height: 32,
                      padding: "0 14px",
                      border: "1px solid #d8dce3",
                      borderRadius: 8,
                      background: "#fff",
                      color: "#384152",
                      fontSize: 12.5,
                      fontWeight: 500,
                      cursor: "pointer",
                    }}
                  >
                    {loading ? "Genereren..." : "Nieuw token"}
                  </button>
                </div>
              </div>
            )}

            {error && <div style={{ fontSize: 12, color: "var(--si-red)" }}>{error}</div>}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>Gebruik</div>
            <pre
              className="si-mono"
              style={{
                margin: 0,
                fontSize: 11.5,
                background: "var(--si-bg)",
                border: "1px solid var(--si-border)",
                borderRadius: 8,
                padding: "10px 12px",
                overflowX: "auto",
                color: "var(--si-text)",
              }}
            >
              {`curl -H "Authorization: Bearer <token>" ${API_URL}/items`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
