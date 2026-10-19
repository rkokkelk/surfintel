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
    border: `1px solid ${active ? "var(--si-blue)" : "var(--si-border)"}`,
    borderRadius: 8,
    padding: "0 10px",
    fontSize: 13,
    color: "var(--si-text)",
    background: active ? "var(--si-blue-bg)" : "var(--si-surface)",
  };
}

function presetButtonStyle(active: boolean): React.CSSProperties {
  return {
    height: 36,
    padding: "0 16px",
    borderRadius: 18,
    border: active ? "none" : "1px solid var(--si-border)",
    background: active ? "var(--si-navy)" : "var(--si-surface)",
    color: active ? "#fff" : "var(--si-text-secondary)",
    fontSize: 12.5,
    fontWeight: 500,
    cursor: "pointer",
    flex: "1 1 auto",
    minWidth: "100px",
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

  // Single responsive layout that adapts to viewport
  return (
    <div className="overview-filters">
      <div className="overview-filters-section">
        <span className="overview-filters-label">Periode</span>
        <div className="overview-filters-presets">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => applyPreset(p.days)}
              className="overview-filters-preset-button"
              style={presetButtonStyle(activePreset === p.label)}
            >
              {p.label}
            </button>
          ))}
        </div>
        
        <div className="overview-filters-daterange">
          <input
            type="date"
            value={value.from}
            onChange={(e) => onChange({ ...value, from: e.target.value })}
            style={{ ...fieldStyle(Boolean(value.from)), flex: "1 1 120px" }}
            aria-label="Van datum"
          />
          <span className="overview-filters-to">t/m</span>
          <input
            type="date"
            value={value.to}
            onChange={(e) => onChange({ ...value, to: e.target.value })}
            style={{ ...fieldStyle(Boolean(value.to)), flex: "1 1 120px" }}
            aria-label="Tot datum"
          />
        </div>
      </div>

      <div className="overview-filters-section">
        <div className="overview-filters-search-container">
          <svg
            width="14"
            height="14"
            viewBox="0 0 20 20"
            fill="none"
            stroke="var(--si-text-muted)"
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
          style={{ ...fieldStyle(Boolean(value.sourceId)), width: "100%" }}
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
          style={{ ...fieldStyle(Boolean(value.cveId)), width: "100%" }}
        />
      </div>

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
          className="overview-filters-clear"
        >
          Wis filters
        </button>
      )}
    </div>
  );
}
