"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface SourceHealthDay {
  date: string;
  total: number;
  discovered: number;
  fetched: number;
  enriched: number;
  error: number;
}

interface SourceHealth {
  days: SourceHealthDay[];
}

type StatusKey = "discovered" | "fetched" | "enriched" | "error";

// Fixed order and reserved colors — a status color is never reassigned to a
// different meaning, and the order stays the same in every bar and the legend.
const STATUSES: { key: StatusKey; label: string; color: string }[] = [
  { key: "discovered", label: "Ontdekt", color: "var(--si-neutral)" },
  { key: "fetched", label: "Opgehaald", color: "var(--si-blue)" },
  { key: "enriched", label: "Verrijkt", color: "var(--si-green)" },
  { key: "error", label: "Fout", color: "var(--si-red)" },
];

const DAY_LABEL = new Intl.DateTimeFormat("nl-NL", { day: "2-digit", month: "short" });

interface Tooltip {
  x: number;
  y: number;
  dayLabel: string;
  statusLabel: string;
  count: number;
  pct: number;
  color: string;
}

export function SourceHealthChart({ sourceId }: { sourceId: string }) {
  const [health, setHealth] = useState<SourceHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTable, setShowTable] = useState(false);
  const [tooltip, setTooltip] = useState<Tooltip | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setTooltip(null);
    apiFetch<SourceHealth>(`/sources/${sourceId}/health`)
      .then(setHealth)
      .catch(() => setError("Kon de bron-gezondheid niet laden."))
      .finally(() => setLoading(false));
  }, [sourceId]);

  const days = health?.days ?? [];
  const totals = STATUSES.reduce<Record<StatusKey, number>>(
    (acc, s) => ({ ...acc, [s.key]: days.reduce((sum, d) => sum + d[s.key], 0) }),
    { discovered: 0, fetched: 0, enriched: 0, error: 0 },
  );
  const grandTotal = STATUSES.reduce((sum, s) => sum + totals[s.key], 0);

  return (
    <div
      style={{
        background: "var(--si-surface)",
        border: "1px solid var(--si-border)",
        borderRadius: 12,
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 14,
        position: "relative",
      }}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <div className="si-display" style={{ fontSize: 15, fontWeight: 600 }}>
          Bron-gezondheid
        </div>
        <div style={{ fontSize: 12, color: "var(--si-text-muted)" }}>verdeling van itemstatus per dag</div>
        {days.length > 0 && (
          <button
            type="button"
            onClick={() => setShowTable((v) => !v)}
            style={{
              marginLeft: "auto",
              border: "none",
              background: "none",
              color: "var(--si-blue)",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {showTable ? "Toon grafiek" : "Toon als tabel"}
          </button>
        )}
      </div>

      {loading && <div style={{ fontSize: 13, color: "var(--si-text-muted)" }}>Laden...</div>}
      {error && <div style={{ fontSize: 13, color: "var(--si-red)" }}>{error}</div>}
      {!loading && !error && days.length === 0 && (
        <div style={{ fontSize: 13, color: "var(--si-text-muted)" }}>
          Nog geen items opgehaald voor deze bron.
        </div>
      )}

      {!loading && !error && days.length > 0 && (
        <>
          {/* Legend: always present for >= 2 series, and — since a tooltip value must
              also be reachable without hovering — carries each status's own total/percentage. */}
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {STATUSES.map((s) => (
              <div key={s.key} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: s.color, flexShrink: 0 }} />
                <span style={{ fontSize: 12, color: "var(--si-text)" }}>
                  <strong>{totals[s.key]}</strong> {s.label.toLowerCase()}
                  {grandTotal > 0 && (
                    <span style={{ color: "var(--si-text-muted)" }}> ({Math.round((totals[s.key] / grandTotal) * 100)}%)</span>
                  )}
                </span>
              </div>
            ))}
          </div>

          {showTable ? (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--si-text-muted)", fontWeight: 500 }}>
                  <th style={{ padding: "4px 6px" }}>Datum</th>
                  {STATUSES.map((s) => (
                    <th key={s.key} style={{ padding: "4px 6px", textAlign: "right" }}>
                      {s.label}
                    </th>
                  ))}
                  <th style={{ padding: "4px 6px", textAlign: "right" }}>Totaal</th>
                </tr>
              </thead>
              <tbody>
                {days.map((d) => (
                  <tr key={d.date} style={{ borderTop: "1px solid var(--si-border)" }}>
                    <td style={{ padding: "6px 6px" }}>{DAY_LABEL.format(new Date(d.date))}</td>
                    {STATUSES.map((s) => (
                      <td key={s.key} style={{ padding: "6px 6px", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                        {d[s.key]}
                      </td>
                    ))}
                    <td style={{ padding: "6px 6px", textAlign: "right", fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
                      {d.total}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {days.map((day) => {
                const segments = STATUSES.map((s) => ({ ...s, count: day[s.key] }))
                  .filter((s) => s.count > 0)
                  .map((s) => ({ ...s, pct: (s.count / day.total) * 100 }));
                const firstIdx = 0;
                const lastIdx = segments.length - 1;

                return (
                  <div key={day.date} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 60, flexShrink: 0, fontSize: 12, color: "var(--si-text-secondary)" }}>
                      {DAY_LABEL.format(new Date(day.date))}
                    </div>
                    <div style={{ flexGrow: 1, display: "flex", gap: 2, height: 24 }}>
                      {segments.map((seg, i) => (
                        <div
                          key={seg.key}
                          onMouseMove={(e) =>
                            setTooltip({
                              x: e.clientX,
                              y: e.clientY,
                              dayLabel: DAY_LABEL.format(new Date(day.date)),
                              statusLabel: seg.label,
                              count: seg.count,
                              pct: seg.pct,
                              color: seg.color,
                            })
                          }
                          onMouseLeave={() => setTooltip(null)}
                          tabIndex={0}
                          onFocus={() =>
                            setTooltip({
                              x: 0,
                              y: 0,
                              dayLabel: DAY_LABEL.format(new Date(day.date)),
                              statusLabel: seg.label,
                              count: seg.count,
                              pct: seg.pct,
                              color: seg.color,
                            })
                          }
                          style={{
                            width: `${seg.pct}%`,
                            background: seg.color,
                            borderTopLeftRadius: i === firstIdx ? 4 : 0,
                            borderBottomLeftRadius: i === firstIdx ? 4 : 0,
                            borderTopRightRadius: i === lastIdx ? 4 : 0,
                            borderBottomRightRadius: i === lastIdx ? 4 : 0,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            cursor: "default",
                            outline: "none",
                          }}
                          aria-label={`${seg.label}: ${seg.count} van ${day.total} (${Math.round(seg.pct)}%) op ${DAY_LABEL.format(new Date(day.date))}`}
                        >
                          {seg.pct >= 12 && (
                            <span style={{ fontSize: 10.5, fontWeight: 600, color: "#fff" }}>
                              {Math.round(seg.pct)}%
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                    <div
                      style={{
                        width: 32,
                        flexShrink: 0,
                        textAlign: "right",
                        fontSize: 12,
                        color: "var(--si-text-muted)",
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {day.total}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {tooltip && (
        <div
          style={{
            position: "fixed",
            left: tooltip.x + 12,
            top: tooltip.y + 12,
            zIndex: 60,
            background: "var(--si-text)",
            color: "#fff",
            borderRadius: 8,
            padding: "6px 10px",
            fontSize: 12,
            pointerEvents: "none",
            boxShadow: "0 4px 12px rgba(15,23,42,0.25)",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span style={{ width: 8, height: 8, borderRadius: 2, background: tooltip.color, flexShrink: 0 }} />
          <span>
            <strong>
              {tooltip.count} ({Math.round(tooltip.pct)}%)
            </strong>{" "}
            {tooltip.statusLabel.toLowerCase()} · {tooltip.dayLabel}
          </span>
        </div>
      )}
    </div>
  );
}
