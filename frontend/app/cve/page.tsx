"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getToken } from "@/lib/api";
import { CVSS_SEVERITY_STYLE, cvssSeverity } from "@/lib/cvss";
import type { Cve } from "@/lib/types";
import { Shell } from "@/components/Shell";
import { CveDetailPanel } from "@/components/CveDetailPanel";
import { ItemDetailPanel } from "@/components/ItemDetailPanel";

type Sort = "recent" | "cvss" | "epss";

const SORT_OPTIONS: { value: Sort; label: string }[] = [
  { value: "recent", label: "Recent bijgewerkt" },
  { value: "cvss", label: "CVSS-score" },
  { value: "epss", label: "EPSS-score" },
];

function fieldStyle(active: boolean): React.CSSProperties {
  return {
    height: 36,
    border: `1px solid ${active ? "var(--si-blue)" : "#d8dce3"}`,
    borderRadius: 8,
    padding: "0 10px",
    fontSize: 13,
    color: "var(--si-text)",
    background: active ? "#f7fbfe" : "#fff",
  };
}

export default function CveListPage() {
  const router = useRouter();
  const [cves, setCves] = useState<Cve[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [qDraft, setQDraft] = useState("");
  const [q, setQ] = useState("");
  const [inKevOnly, setInKevOnly] = useState(false);
  const [sort, setSort] = useState<Sort>("recent");
  const [selectedCveId, setSelectedCveId] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  useEffect(() => {
    const id = setTimeout(() => setQ(qDraft), 350);
    return () => clearTimeout(id);
  }, [qDraft]);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    setLoading(true);
    const params = new URLSearchParams({ sort });
    if (q) params.set("q", q);
    if (inKevOnly) params.set("in_kev", "true");
    apiFetch<Cve[]>(`/cves?${params.toString()}`)
      .then(setCves)
      .catch(() => setError("Kon de CVE-lijst niet laden."))
      .finally(() => setLoading(false));
  }, [q, inKevOnly, sort, router]);

  return (
    <Shell active="cve">
      <div style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <div className="si-display" style={{ fontSize: 18, fontWeight: 600 }}>
            CVE database
          </div>
          <div style={{ fontSize: 13, color: "var(--si-text-muted)" }}>{cves.length} CVE's</div>
        </div>

        <div
          style={{
            background: "var(--si-surface)",
            border: "1px solid var(--si-border)",
            borderRadius: 12,
            padding: "12px 16px",
            display: "flex",
            alignItems: "center",
            gap: 10,
            flexWrap: "wrap",
          }}
        >
          <input
            value={qDraft}
            onChange={(e) => setQDraft(e.target.value)}
            placeholder="Zoek op CVE-ID of titel..."
            style={{ ...fieldStyle(Boolean(q)), flexGrow: 1, minWidth: 220 }}
          />
          <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} style={fieldStyle(false)}>
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                Sorteer: {o.label}
              </option>
            ))}
          </select>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "var(--si-text)" }}>
            <input type="checkbox" checked={inKevOnly} onChange={(e) => setInKevOnly(e.target.checked)} />
            Alleen CISA KEV
          </label>
        </div>

        {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
        {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}
        {!loading && !error && cves.length === 0 && (
          <div style={{ color: "var(--si-text-muted)" }}>Geen CVE&apos;s gevonden.</div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 900 }}>
          {cves.map((cve) => {
            const severity = cvssSeverity(cve.cvss_v4_score ?? cve.cvss_v3_score);
            const style = severity ? CVSS_SEVERITY_STYLE[severity] : null;
            return (
              <button
                key={cve.cve_id}
                type="button"
                onClick={() => setSelectedCveId(cve.cve_id)}
                style={{
                  background: "var(--si-surface)",
                  border: "1px solid var(--si-border)",
                  borderRadius: 10,
                  padding: "12px 16px",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  textAlign: "left",
                  color: "inherit",
                  cursor: "pointer",
                  width: "100%",
                }}
              >
                <span className="si-mono" style={{ fontSize: 13, fontWeight: 600, color: "var(--si-navy)", width: 150, flexShrink: 0 }}>
                  {cve.cve_id}
                </span>
                <span style={{ fontSize: 13.5, color: "var(--si-text)", flexGrow: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {cve.title ?? "—"}
                </span>
                {cve.in_kev && (
                  <span style={{ fontSize: 11, fontWeight: 600, color: "var(--si-red)", background: "var(--si-red-bg)", borderRadius: 6, padding: "3px 8px" }}>
                    KEV
                  </span>
                )}
                {cve.epss_score !== null && (
                  <span className="si-mono" style={{ fontSize: 11.5, color: "var(--si-text-muted)", width: 80, textAlign: "right" }}>
                    EPSS {(cve.epss_score * 100).toFixed(1)}%
                  </span>
                )}
                {style && (
                  <span style={{ fontSize: 11, fontWeight: 600, color: style.color, background: style.bg, borderRadius: 6, padding: "3px 8px", width: 56, textAlign: "center" }}>
                    {(cve.cvss_v4_score ?? cve.cvss_v3_score)?.toFixed(1)}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
      <CveDetailPanel
        cveId={selectedCveId}
        onClose={() => setSelectedCveId(null)}
        onOpenItem={(id) => {
          setSelectedCveId(null);
          setSelectedItemId(id);
        }}
      />
      <ItemDetailPanel itemId={selectedItemId} onClose={() => setSelectedItemId(null)} onOpenCve={setSelectedCveId} />
    </Shell>
  );
}
