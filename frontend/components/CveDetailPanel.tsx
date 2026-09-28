"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { CveDetail } from "@/lib/types";
import { CveDetailContent } from "@/components/CveDetailContent";

export function CveDetailPanel({
  cveId,
  onClose,
  onOpenItem,
}: {
  cveId: string | null;
  onClose: () => void;
  onOpenItem?: (itemId: string) => void;
}) {
  const [cve, setCve] = useState<CveDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cveId) return;
    setCve(null);
    setError(null);
    setLoading(true);
    apiFetch<CveDetail>(`/cves/${cveId}`)
      .then(setCve)
      .catch(() => setError("Kon deze CVE niet laden."))
      .finally(() => setLoading(false));
  }, [cveId]);

  useEffect(() => {
    if (!cveId) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [cveId, onClose]);

  if (!cveId) return null;

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 50, display: "flex", justifyContent: "flex-end" }}>
      <div onClick={onClose} style={{ position: "absolute", inset: 0, background: "rgba(15, 23, 42, 0.35)" }} aria-hidden />
      <div
        style={{
          position: "relative",
          width: 480,
          maxWidth: "100%",
          height: "100%",
          background: "var(--si-surface)",
          boxShadow: "-8px 0 24px rgba(15, 23, 42, 0.12)",
          display: "flex",
          flexDirection: "column",
          overflowY: "auto",
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
            CVE-details
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

        <div style={{ padding: 20 }}>
          {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
          {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}
          {cve && <CveDetailContent cve={cve} onOpenItem={onOpenItem} />}
        </div>
      </div>
    </div>
  );
}
