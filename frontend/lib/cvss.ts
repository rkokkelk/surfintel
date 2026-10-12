// Official CVSS v3 severity bands (score -> rating), used to color both the
// list badges and the radar chart fill — the same score always reads the
// same color everywhere in the app.
export function cvssSeverity(score: number | null): "critical" | "high" | "medium" | "low" | null {
  if (score === null) return null;
  if (score >= 9) return "critical";
  if (score >= 7) return "high";
  if (score >= 4) return "medium";
  return "low";
}

export const CVSS_SEVERITY_STYLE: Record<string, { color: string; bg: string; label: string }> = {
  critical: { color: "var(--si-red)", bg: "var(--si-red-bg)", label: "Kritiek" },
  high: { color: "var(--si-amber)", bg: "var(--si-amber-bg)", label: "Hoog" },
  medium: { color: "var(--si-indigo)", bg: "var(--si-indigo-bg)", label: "Midden" },
  low: { color: "var(--si-neutral)", bg: "var(--si-neutral-bg)", label: "Laag" },
};

export interface CvssAxis {
  key: string;
  label: string;
  value: string;
  valueLabel: string;
  score: number; // 0..1, higher = more severe
}

const AV: Record<string, [string, number]> = {
  N: ["Netwerk", 1], A: ["Aangrenzend netwerk", 0.66], L: ["Lokaal", 0.33], P: ["Fysiek", 0],
};
const AC: Record<string, [string, number]> = { L: ["Laag", 1], H: ["Hoog", 0] };
const PR: Record<string, [string, number]> = { N: ["Geen", 1], L: ["Laag", 0.5], H: ["Hoog", 0] };
const UI: Record<string, [string, number]> = { N: ["Geen", 1], R: ["Vereist", 0] };
const CIA: Record<string, [string, number]> = { H: ["Hoog", 1], L: ["Laag", 0.5], N: ["Geen", 0] };

/** Parses a CVSS v3.x vector string into radar-chart axes. Scope (S) is a
 * blast-radius flag, not a "how severe" magnitude, so it's left off the
 * radar and shown as a separate badge instead. v4 vectors use a different
 * metric set entirely and aren't parsed here — v4 is shown as score/vector
 * text only for now.
 */
export function parseCvssV3Vector(vector: string): CvssAxis[] {
  const parts = Object.fromEntries(
    vector.split("/").filter((p) => p.includes(":")).map((p) => p.split(":") as [string, string]),
  );

  const axis = (key: string, label: string, table: Record<string, [string, number]>): CvssAxis | null => {
    const raw = parts[key];
    const entry = raw ? table[raw] : undefined;
    if (!entry) return null;
    return { key, label, value: raw, valueLabel: entry[0], score: entry[1] };
  };

  return [
    axis("AV", "Attack Vector", AV),
    axis("AC", "Attack Complexity", AC),
    axis("PR", "Privileges Required", PR),
    axis("UI", "User Interaction", UI),
    axis("C", "Confidentiality", CIA),
    axis("I", "Integrity", CIA),
    axis("A", "Availability", CIA),
  ].filter((a): a is CvssAxis => a !== null);
}

export function cvssScope(vector: string): "Changed" | "Unchanged" | null {
  const match = vector.match(/\/S:([UC])/);
  if (!match) return null;
  return match[1] === "C" ? "Changed" : "Unchanged";
}
