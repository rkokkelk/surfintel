"use client";

import { useEffect, useState } from "react";
import type { Item } from "@/lib/types";
import { imgFetch } from "@/lib/api";

const THUMB_WIDTH = 160;
const THUMB_HEIGHT = 120;

function ItemScreenshot({ itemId }: { itemId: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    setSrc(null);
    setFailed(false);

    imgFetch<Blob>(`/items/${itemId}/screenshot`)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [itemId]);

  return (
    <div
      style={{
        width: THUMB_WIDTH,
        height: THUMB_HEIGHT,
        flexShrink: 0,
        borderRadius: 8,
        overflow: "hidden",
        background: "var(--si-bg)",
        border: "1px solid var(--si-border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element -- object URL from an authenticated blob fetch, not a static/optimizable asset
        <img src={src} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <span style={{ fontSize: 11, color: "var(--si-text-muted)" }}>
          {failed ? "Geen screenshot" : "Laden…"}
        </span>
      )}
    </div>
  );
}

const SEVERITY_STYLE: Record<string, { color: string; bg: string }> = {
  kritiek: { color: "var(--si-red)", bg: "var(--si-red-bg)" },
  hoog: { color: "var(--si-amber)", bg: "var(--si-amber-bg)" },
  midden: { color: "var(--si-indigo)", bg: "var(--si-indigo-bg)" },
};

const CATEGORY_STYLE: Record<string, { color: string; bg: string; label: string }> = {
  advisory: { color: "var(--si-teal)", bg: "var(--si-teal-bg)", label: "Advisory" },
  patch: { color: "var(--si-green)", bg: "var(--si-green-bg)", label: "Patch" },
  malware: { color: "var(--si-indigo)", bg: "var(--si-indigo-bg)", label: "Malware" },
};

function enrichment(item: Item, moduleName: string) {
  return item.enrichments?.find((e) => e.module_name === moduleName)?.data as
    | Record<string, unknown>
    | undefined;
}

export function FeedCard({ item }: { item: Item }) {
  const categorization = enrichment(item, "ai_categorizer");
  const cve = enrichment(item, "cve_extractor");
  const severity = (categorization?.severity as string) ?? null;
  const category = (categorization?.category as string) ?? null;
  const cveIds = (cve?.cve_ids as string[]) ?? [];

  const severityStyle = severity ? SEVERITY_STYLE[severity] : null;
  const categoryStyle = category ? CATEGORY_STYLE[category] : null;

  const timeFormatOptions: Intl.DateTimeFormatOptions = { 
    month: 'short', 
    weekday: "short",
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit', 
  };
  const timeFormat = Intl.DateTimeFormat("nl-NL", timeFormatOptions);


  return (
    <div
      style={{
        background: "var(--si-surface)",
        border: "1px solid var(--si-border)",
        borderRadius: 12,
        padding: "16px 20px",
        display: "flex",
        flexDirection: "row",
        gap: 16,
      }}
    >
      <ItemScreenshot itemId={item.id} />

      <div style={{ display: "flex", flexDirection: "column", gap: 9, minWidth: 0, flexGrow: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {severityStyle && (
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: severityStyle.color,
                background: severityStyle.bg,
                borderRadius: 10,
                padding: "3px 9px",
              }}
            >
              {severity}
            </span>
          )}
          <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--si-text-muted)" }}>
            {item.source?.name} • {item.published_at ? timeFormat.format(new Date(item.published_at)) : ""}
          </span>
        </div>
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="si-display"
          style={{ fontSize: 16, fontWeight: 600, color: "var(--si-text)" }}
        >
          {item.title ?? item.url}
        </a>
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          {item.description && (
            <span
              className="si-mono"
              style={{
                fontSize: 11.5,
                fontWeight: 600,
                borderRadius: 6,
                padding: "3px 8px",
              }}
            >
              {item.description}
            </span>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          {cveIds.map((id) => (
            <span
              key={id}
              className="si-mono"
              style={{ fontSize: 11.5, color: "var(--si-purple)", background: "var(--si-purple-bg)", borderRadius: 6, padding: "3px 8px" }}
            >
              {id}
            </span>
          ))}
          {categoryStyle && (
            <span
              style={{
                fontSize: 11.5,
                fontWeight: 600,
                color: categoryStyle.color,
                background: categoryStyle.bg,
                borderRadius: 6,
                padding: "3px 8px",
              }}
            >
              {categoryStyle.label}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
