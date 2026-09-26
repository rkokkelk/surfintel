"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { ItemDetail } from "@/lib/types";
import {
  ACTOR_STYLE,
  AiClassification,
  ENTITY_STYLE,
  SEVERITY_STYLE,
  VICTIM_STYLE,
  countryLabel,
  enrichmentData,
  industryLabel,
} from "@/lib/enrichment";
import { ItemScreenshot } from "@/components/ItemScreenshot";

function Badge({ color, bg, children }: { color: string; bg: string; children: React.ReactNode }) {
  return (
    <span style={{ fontSize: 12, fontWeight: 600, color, background: bg, borderRadius: 6, padding: "4px 9px" }}>
      {children}
    </span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)", letterSpacing: "0.03em" }}>
        {title.toUpperCase()}
      </div>
      {children}
    </div>
  );
}

const KNOWN_MODULES = new Set(["ai_categorizer", "cve_extractor", "cpe_extractor", "kev_checker"]);

export function ItemDetailPanel({ itemId, onClose }: { itemId: string | null; onClose: () => void }) {
  const [item, setItem] = useState<ItemDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!itemId) return;
    setItem(null);
    setError(null);
    setLoading(true);
    apiFetch<ItemDetail>(`/items/${itemId}`)
      .then(setItem)
      .catch(() => setError("Kon de details van dit item niet laden."))
      .finally(() => setLoading(false));
  }, [itemId]);

  useEffect(() => {
    if (!itemId) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [itemId, onClose]);

  if (!itemId) return null;

  const classification = item ? (enrichmentData(item, "ai_categorizer") as AiClassification | undefined) : undefined;
  const cve = item ? enrichmentData(item, "cve_extractor") : undefined;
  const cpe = item ? enrichmentData(item, "cpe_extractor") : undefined;
  const kev = item ? enrichmentData(item, "kev_checker") : undefined;
  const cveIds = (cve?.cve_ids as string[]) ?? [];
  const cpeIds = (cpe?.cpe_ids as string[]) ?? [];
  const otherEnrichments = item?.enrichments?.filter((e) => !KNOWN_MODULES.has(e.module_name)) ?? [];

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 50, display: "flex", justifyContent: "flex-end" }}>
      <div
        onClick={onClose}
        style={{ position: "absolute", inset: 0, background: "rgba(15, 23, 42, 0.35)" }}
        aria-hidden
      />
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
            Itemdetails
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

        <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 20 }}>
          {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
          {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}

          {item && (
            <>
              <ItemScreenshot itemId={item.id} width={440} height={280} />

              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {classification?.severity && (
                  <div>
                    <Badge color={SEVERITY_STYLE[classification.severity].color} bg={SEVERITY_STYLE[classification.severity].bg}>
                      {SEVERITY_STYLE[classification.severity].label}
                    </Badge>
                  </div>
                )}
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="si-display"
                  style={{ fontSize: 18, fontWeight: 600, color: "var(--si-text)" }}
                >
                  {item.title ?? item.url}
                </a>
                {item.description && (
                  <div style={{ fontSize: 13, color: "var(--si-text-secondary)", lineHeight: 1.5 }}>
                    {item.description}
                  </div>
                )}
              </div>

              <Section title="Bron">
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  {item.source.favicon && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={`data:image/png;base64,${item.source.favicon}`} width={16} height={16} alt="" />
                  )}
                  <span style={{ fontSize: 13.5, fontWeight: 600 }}>{item.source.name}</span>
                  <span
                    className="si-mono"
                    style={{ fontSize: 11, color: "#425066", background: "#eef1f5", borderRadius: 6, padding: "2px 8px" }}
                  >
                    {item.source.type}
                  </span>
                </div>
                <a href={item.url} target="_blank" rel="noreferrer" style={{ fontSize: 12.5, wordBreak: "break-all" }}>
                  {item.url}
                </a>
                <div style={{ fontSize: 12, color: "var(--si-text-muted)" }}>
                  Gepubliceerd: {item.published_at ? new Date(item.published_at).toLocaleString("nl-NL") : "onbekend"}
                  {" · "}Status: {item.status}
                  {item.last_changed_at && <> · Laatst gewijzigd: {new Date(item.last_changed_at).toLocaleString("nl-NL")}</>}
                </div>
              </Section>

              {classification && (
                <Section title="AI-classificatie">
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {classification.actor && <Badge color={ACTOR_STYLE.color} bg={ACTOR_STYLE.bg}>{classification.actor}</Badge>}
                    {(classification.entity ?? []).map((name) => (
                      <Badge key={name} color={ENTITY_STYLE.color} bg={ENTITY_STYLE.bg}>
                        {name}
                      </Badge>
                    ))}
                    {classification.victim_country && (
                      <Badge color={VICTIM_STYLE.color} bg={VICTIM_STYLE.bg}>
                        {countryLabel(classification.victim_country)}
                      </Badge>
                    )}
                    {classification.victim_industry && (
                      <Badge color={VICTIM_STYLE.color} bg={VICTIM_STYLE.bg}>
                        {industryLabel(classification.victim_industry)}
                      </Badge>
                    )}
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--si-text-secondary)" }}>
                    Impact {classification.impact}/5 · Waarschijnlijkheid {classification.chance}/5
                  </div>
                </Section>
              )}

              {(cveIds.length > 0 || cpeIds.length > 0 || kev) && (
                <Section title="Kwetsbaarheden">
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {cveIds.map((id) => (
                      <span
                        key={id}
                        className="si-mono"
                        style={{ fontSize: 12, color: "var(--si-purple)", background: "var(--si-purple-bg)", borderRadius: 6, padding: "4px 9px" }}
                      >
                        {id}
                      </span>
                    ))}
                    {cpeIds.map((id) => (
                      <span
                        key={id}
                        className="si-mono"
                        style={{ fontSize: 11.5, color: "var(--si-text-secondary)", background: "var(--si-bg)", borderRadius: 6, padding: "4px 9px" }}
                      >
                        {id}
                      </span>
                    ))}
                    {kev?.in_kev === true && (
                      <Badge color="var(--si-red)" bg="var(--si-red-bg)">
                        In CISA KEV-catalogus
                      </Badge>
                    )}
                  </div>
                </Section>
              )}

              {otherEnrichments.map((e) => (
                <Section key={e.module_name} title={e.module_name}>
                  <pre
                    className="si-mono"
                    style={{
                      fontSize: 11,
                      background: "var(--si-bg)",
                      border: "1px solid var(--si-border)",
                      borderRadius: 8,
                      padding: 10,
                      margin: 0,
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                    }}
                  >
                    {JSON.stringify(e.data, null, 2)}
                  </pre>
                </Section>
              ))}

              {item.extracted_text && (
                <Section title="Opgehaalde tekst">
                  <div
                    style={{
                      fontSize: 12.5,
                      color: "var(--si-text-secondary)",
                      lineHeight: 1.5,
                      maxHeight: 220,
                      overflowY: "auto",
                      background: "var(--si-bg)",
                      border: "1px solid var(--si-border)",
                      borderRadius: 8,
                      padding: 10,
                    }}
                  >
                    {item.extracted_text}
                  </div>
                </Section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
