import type { Item } from "@/lib/types";
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
    <span
      style={{
        fontSize: 11.5,
        fontWeight: 600,
        color,
        background: bg,
        borderRadius: 6,
        padding: "3px 8px",
      }}
    >
      {children}
    </span>
  );
}

export function FeedCard({
  item,
  onOpenDetail,
  onOpenCve,
}: {
  item: Item;
  onOpenDetail: (itemId: string) => void;
  onOpenCve: (cveId: string) => void;
}) {
  const classification = enrichmentData(item, "ai_categorizer") as AiClassification | undefined;
  const cve = enrichmentData(item, "cve_extractor");
  const cveIds = (cve?.cve_ids as string[]) ?? [];

  const severity = classification?.severity ?? null;
  const severityStyle = severity ? SEVERITY_STYLE[severity] : null;
  const entities = classification?.entity ?? [];
  const actor = classification?.actor ?? null;

  const timeFormat = Intl.DateTimeFormat("nl-NL", {
    month: "short",
    weekday: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      onClick={() => onOpenDetail(item.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onOpenDetail(item.id)}
      style={{
        background: "var(--si-surface)",
        border: "1px solid var(--si-border)",
        borderRadius: 12,
        padding: "16px 20px",
        display: "flex",
        flexDirection: "row",
        gap: 16,
        cursor: "pointer",
      }}
    >
      <ItemScreenshot itemId={item.id} width={260} height={200} />

      <div style={{ display: "flex", flexDirection: "column", gap: 9, minWidth: 0, flexGrow: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {severityStyle && <Badge color={severityStyle.color} bg={severityStyle.bg}>{severityStyle.label}</Badge>}
          <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--si-text-muted)" }}>
            {item.source?.name} • {item.published_at ? timeFormat.format(new Date(item.published_at)) : ""}
          </span>
        </div>
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="si-display"
          style={{ fontSize: 16, fontWeight: 600, color: "var(--si-text)" }}
        >
          {item.title ?? item.url}
        </a>
        {item.description && (
          <div style={{ fontSize: 13, color: "var(--si-text-secondary)", lineHeight: 1.4 }}>{item.description}</div>
        )}

        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          {cveIds.map((id) => (
            <button
              key={id}
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onOpenCve(id);
              }}
              className="si-mono"
              style={{ fontSize: 11.5, color: "var(--si-purple)", background: "var(--si-purple-bg)", border: "none", borderRadius: 6, padding: "3px 8px", cursor: "pointer" }}
            >
              {id}
            </button>
          ))}
          {actor && <Badge color={ACTOR_STYLE.color} bg={ACTOR_STYLE.bg}>{actor}</Badge>}
          {entities.map((name) => (
            <Badge key={name} color={ENTITY_STYLE.color} bg={ENTITY_STYLE.bg}>
              {name}
            </Badge>
          ))}
          {classification?.victim_country && (
            <Badge color={VICTIM_STYLE.color} bg={VICTIM_STYLE.bg}>
              {countryLabel(classification.victim_country)}
            </Badge>
          )}
          {classification?.victim_industry && (
            <Badge color={VICTIM_STYLE.color} bg={VICTIM_STYLE.bg}>
              {industryLabel(classification.victim_industry)}
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}
