"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Source } from "@/lib/types";

export interface OverviewFilterState {
  q: string;
  sourceId: string | null;
  cveId: string;
  from: string; // yyyy-mm-dd, "" = unset
  to: string;
  minCvss: string; // "" = unset, else "0".."10"
  minEpss: string; // "" = unset, else a percentage "0".."100"
  kevOnly: boolean;
}

export const EMPTY_FILTERS: OverviewFilterState = {
  q: "",
  sourceId: null,
  cveId: "",
  from: "",
  to: "",
  minCvss: "",
  minEpss: "",
  kevOnly: false,
};

const PRESETS: { label: string; days: number | null }[] = [
  { label: "Alle tijd", days: null },
  { label: "Vandaag", days: 0 },
  { label: "7 dagen", days: 7 },
  { label: "30 dagen", days: 30 },
];

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

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

export function OverviewFilters({
  value,
  onChange,
}: {
  value: OverviewFilterState;
  onChange: (next: OverviewFilterState) => void;
}) {
  const [sources, setSources] = useState<Source[]>([]);
  const [qDraft, setQDraft] = useState(value.q);
  const [cveDraft, setCveDraft] = useState(value.cveId);
  const [cvssDraft, setCvssDraft] = useState(value.minCvss);
  const [epssDraft, setEpssDraft] = useState(value.minEpss);

  useEffect(() => {
    apiFetch<Source[]>("/sources").then(setSources).catch(() => setSources([]));
  }, []);

  // Debounce the two free-text inputs so we don't fire a request per keystroke;
  // dropdowns and dates apply immediately since those are discrete choices.
  useEffect(() => {
    const id = setTimeout(() => {
      if (qDraft !== value.q) onChange({ ...value, q: qDraft });
    }, 350);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qDraft]);

  useEffect(() => {
    const id = setTimeout(() => {
      if (cveDraft !== value.cveId) onChange({ ...value, cveId: cveDraft });
    }, 350);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cveDraft]);

  useEffect(() => {
    const id = setTimeout(() => {
      if (cvssDraft !== value.minCvss) onChange({ ...value, minCvss: cvssDraft });
    }, 350);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cvssDraft]);

  useEffect(() => {
    const id = setTimeout(() => {
      if (epssDraft !== value.minEpss) onChange({ ...value, minEpss: epssDraft });
    }, 350);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [epssDraft]);

  function applyPreset(days: number | null) {
    if (days === null) {
      onChange({ ...value, from: "", to: "" });
      return;
    }
    const to = new Date();
    const from = new Date();
    from.setDate(from.getDate() - days);
    onChange({ ...value, from: isoDate(from), to: isoDate(to) });
  }

  const activePreset = (() => {
    if (!value.from && !value.to) return "Alle tijd";
    const today = isoDate(new Date());
    for (const p of PRESETS) {
      if (p.days === null) continue;
      const expectedFrom = isoDate(new Date(Date.now() - p.days * 86400000));
      if (value.from === expectedFrom && value.to === today) return p.label;
    }
    return null; // custom range
  })();

  const hasActiveFilters = Boolean(
    value.q || value.sourceId || value.cveId || value.from || value.to || value.minCvss || value.minEpss || value.kevOnly
  );

  return (
    <div
      style={{
        background: "var(--si-surface)",
        border: "1px solid var(--si-border)",
        borderRadius: 12,
        padding: "12px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 10,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>Periode</span>
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => applyPreset(p.days)}
            style={{
              height: 28,
              padding: "0 12px",
              borderRadius: 14,
              border: activePreset === p.label ? "none" : "1px solid #d8dce3",
              background: activePreset === p.label ? "var(--si-navy)" : "#fff",
              color: activePreset === p.label ? "#fff" : "#384152",
              fontSize: 12.5,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            {p.label}
          </button>
        ))}
        <span style={{ width: 1, height: 20, background: "var(--si-border)" }} />
        <input
          type="date"
          value={value.from}
          onChange={(e) => onChange({ ...value, from: e.target.value })}
          style={{ ...fieldStyle(Boolean(value.from)), width: 138 }}
          aria-label="Van datum"
        />
        <span style={{ fontSize: 12, color: "var(--si-text-muted)" }}>t/m</span>
        <input
          type="date"
          value={value.to}
          onChange={(e) => onChange({ ...value, to: e.target.value })}
          style={{ ...fieldStyle(Boolean(value.to)), width: 138 }}
          aria-label="Tot datum"
        />

        {hasActiveFilters && (
          <button
            type="button"
            onClick={() => {
              setQDraft("");
              setCveDraft("");
              setCvssDraft("");
              setEpssDraft("");
              onChange(EMPTY_FILTERS);
            }}
            style={{
              marginLeft: "auto",
              border: "none",
              background: "none",
              color: "var(--si-blue)",
              fontSize: 12.5,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Wis filters
          </button>
        )}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <div style={{ position: "relative", flexGrow: 1, minWidth: 220 }}>
          <svg
            width="14"
            height="14"
            viewBox="0 0 20 20"
            fill="none"
            stroke="#9aa3b2"
            strokeWidth="1.8"
            style={{ position: "absolute", left: 10, top: 11 }}
          >
            <circle cx="9" cy="9" r="6" />
            <path d="M17 17l-4-4" strokeLinecap="round" />
          </svg>
          <input
            value={qDraft}
            onChange={(e) => setQDraft(e.target.value)}
            placeholder="Zoek op trefwoord..."
            style={{ ...fieldStyle(Boolean(value.q)), width: "100%", paddingLeft: 30 }}
          />
        </div>

        <select
          value={value.sourceId ?? ""}
          onChange={(e) => onChange({ ...value, sourceId: e.target.value || null })}
          style={{ ...fieldStyle(Boolean(value.sourceId)), minWidth: 160 }}
        >
          <option value="">Alle bronnen</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>

        <input
          value={cveDraft}
          onChange={(e) => setCveDraft(e.target.value)}
          placeholder="CVE-ID, bv. 2026-1234"
          className="si-mono"
          style={{ ...fieldStyle(Boolean(value.cveId)), width: 180 }}
        />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>CVE-status</span>
        <label style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12.5, color: "var(--si-text)" }}>
          CVSS ≥
          <input
            type="number"
            min={0}
            max={10}
            step={0.1}
            value={cvssDraft}
            onChange={(e) => setCvssDraft(e.target.value)}
            placeholder="bv. 7"
            className="si-mono"
            style={{ ...fieldStyle(Boolean(value.minCvss)), width: 70 }}
          />
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12.5, color: "var(--si-text)" }}>
          EPSS ≥
          <input
            type="number"
            min={0}
            max={100}
            step={1}
            value={epssDraft}
            onChange={(e) => setEpssDraft(e.target.value)}
            placeholder="bv. 10"
            className="si-mono"
            style={{ ...fieldStyle(Boolean(value.minEpss)), width: 70 }}
          />
          %
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: "var(--si-text)" }}>
          <input
            type="checkbox"
            checked={value.kevOnly}
            onChange={(e) => onChange({ ...value, kevOnly: e.target.checked })}
          />
          Alleen CISA KEV
        </label>
      </div>
    </div>
  );
}
