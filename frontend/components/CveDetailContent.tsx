import { CVSS_SEVERITY_STYLE, cvssScope, cvssSeverity, parseCvssV3Vector } from "@/lib/cvss";
import type { CveDetail } from "@/lib/types";
import { CvssRadarChart } from "@/components/CvssRadarChart";

function Badge({ color, bg, children }: { color: string; bg: string; children: React.ReactNode }) {
  return (
    <span style={{ fontSize: 12, fontWeight: 600, color, background: bg, borderRadius: 6, padding: "4px 10px" }}>
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

/** The CVE detail view's content, with no page/panel chrome of its own, so
 * both the side panel (opened from an item's CVE chip or the CVE list) and
 * the standalone /cve/[id] page render identically. `onOpenItem`, when
 * given, makes a referenced item open inside SurfIntel (another panel)
 * instead of linking straight out to its original URL.
 */
export function CveDetailContent({ cve, onOpenItem }: { cve: CveDetail; onOpenItem?: (itemId: string) => void }) {
  const severity = cvssSeverity(cve.cvss_v3_score);
  const severityStyle = severity ? CVSS_SEVERITY_STYLE[severity] : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span className="si-mono si-display" style={{ fontSize: 18, fontWeight: 700, color: "var(--si-navy)" }}>
            {cve.cve_id}
          </span>
          {severityStyle && cve.cvss_v3_score !== null && (
            <Badge color={severityStyle.color} bg={severityStyle.bg}>
              CVSS v3: {cve.cvss_v3_score.toFixed(1)} · {severityStyle.label}
            </Badge>
          )}
          {cve.cvss_v4_score !== null && (
            <Badge color="var(--si-blue)" bg="var(--si-blue-bg)">
              CVSS v4: {cve.cvss_v4_score.toFixed(1)}
            </Badge>
          )}
          {cve.epss_score !== null && (
            <Badge color="var(--si-teal)" bg="var(--si-teal-bg)">
              EPSS {(cve.epss_score * 100).toFixed(1)}%
            </Badge>
          )}
          {cve.in_kev && (
            <Badge color="var(--si-red)" bg="var(--si-red-bg)">
              In CISA KEV{cve.kev_date_added ? ` · sinds ${new Date(cve.kev_date_added).toLocaleDateString("nl-NL")}` : ""}
            </Badge>
          )}
        </div>
        {cve.title && (
          <div className="si-display" style={{ fontSize: 16, fontWeight: 600 }}>
            {cve.title}
          </div>
        )}
        <a href={`https://app.opencve.io/cve/${cve.cve_id}`} target="_blank" rel="noreferrer" style={{ fontSize: 12.5 }}>
          Bekijk op opencve.io ↗
        </a>
      </div>

      {cve.description && (
        <Section title="Beschrijving">
          <div style={{ fontSize: 13.5, color: "var(--si-text-secondary)", lineHeight: 1.55, whiteSpace: "pre-line" }}>
            {cve.description}
          </div>
        </Section>
      )}

      {cve.cvss_v3_vector && (
        <Section title="CVSS v3-vector">
          <div style={{ display: "flex", alignItems: "center", gap: 20, flexWrap: "wrap" }}>
            <CvssRadarChart axes={parseCvssV3Vector(cve.cvss_v3_vector)} color={severityStyle?.color ?? "var(--si-navy)"} size={220} />
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span className="si-mono" style={{ fontSize: 11.5, color: "var(--si-text-muted)" }}>
                {cve.cvss_v3_vector}
              </span>
              {cvssScope(cve.cvss_v3_vector) && (
                <span style={{ fontSize: 12.5, color: "var(--si-text-secondary)" }}>
                  Scope: {cvssScope(cve.cvss_v3_vector) === "Changed" ? "Gewijzigd" : "Ongewijzigd"}
                </span>
              )}
            </div>
          </div>
        </Section>
      )}

      {cve.weaknesses.length > 0 && (
        <Section title="Zwaktes (CWE)">
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {cve.weaknesses.map((w) => (
              <span key={w} className="si-mono" style={{ fontSize: 12, color: "var(--si-purple)", background: "var(--si-purple-bg)", borderRadius: 6, padding: "4px 9px" }}>
                {w}
              </span>
            ))}
          </div>
        </Section>
      )}

      {cve.cpes.length > 0 && (
        <Section title={`CPE's (${cve.cpes.length})`}>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 4,
              maxHeight: 200,
              overflowY: "auto",
              background: "var(--si-bg)",
              border: "1px solid var(--si-border)",
              borderRadius: 8,
              padding: 10,
            }}
          >
            {cve.cpes.map((cpe) => (
              <span key={cpe} className="si-mono" style={{ fontSize: 11.5, color: "var(--si-text-secondary)" }}>
                {cpe}
              </span>
            ))}
          </div>
        </Section>
      )}

      {cve.references.length > 0 && (
        <Section title="Referenties">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {cve.references.map((ref) => (
              <div key={ref.url} style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <a href={ref.url} target="_blank" rel="noreferrer" style={{ fontSize: 12.5, wordBreak: "break-all" }}>
                  {ref.url}
                </a>
                {ref.tags.map((tag) => (
                  <span key={tag} style={{ fontSize: 10.5, color: "var(--si-text-muted)", background: "var(--si-neutral-bg)", borderRadius: 5, padding: "2px 6px" }}>
                    {tag}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </Section>
      )}

      {cve.items.length > 0 && (
        <Section title={`Items die deze CVE noemen (${cve.items.length})`}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {cve.items.map((item) =>
              onOpenItem ? (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onOpenItem(item.id)}
                  style={{
                    fontSize: 13,
                    textAlign: "left",
                    color: "var(--si-text)",
                    background: "var(--si-surface)",
                    border: "1px solid var(--si-border)",
                    borderRadius: 8,
                    padding: "8px 12px",
                    cursor: "pointer",
                  }}
                >
                  {item.title ?? item.url}
                  {item.published_at && (
                    <span style={{ marginLeft: 8, fontSize: 11.5, color: "var(--si-text-muted)" }}>
                      {new Date(item.published_at).toLocaleDateString("nl-NL")}
                    </span>
                  )}
                </button>
              ) : (
                <a
                  key={item.id}
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    fontSize: 13,
                    color: "var(--si-text)",
                    background: "var(--si-surface)",
                    border: "1px solid var(--si-border)",
                    borderRadius: 8,
                    padding: "8px 12px",
                  }}
                >
                  {item.title ?? item.url}
                  {item.published_at && (
                    <span style={{ marginLeft: 8, fontSize: 11.5, color: "var(--si-text-muted)" }}>
                      {new Date(item.published_at).toLocaleDateString("nl-NL")}
                    </span>
                  )}
                </a>
              ),
            )}
          </div>
        </Section>
      )}
    </div>
  );
}
