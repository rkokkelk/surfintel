import type { Item } from "@/lib/types";

/** Shape of app/enrichment/ai_categorizer.py's ItemClassification.model_dump(). */
export interface AiClassification {
  victim_country: string | null;
  victim_industry: string | null;
  actor: string | null;
  severity: "critical" | "high" | "medium" | "low";
  entity: string[] | null;
  impact: number;
  chance: number;
}

/** Shape of app/enrichment/mitre_categorizer.py's ItemMitreClassificaiton.model_dump(). */
export interface MitreTtp {
  tactic_id: string;
  tactic_name: string;
  technique_id: string;
  technique_name: string;
  quote: string;
}

export interface MitreClassification {
  ttps: MitreTtp[] | null;
}

export function enrichmentData(item: Item, moduleName: string): Record<string, unknown> | undefined {
  return item.enrichments?.find((e) => e.module_name === moduleName)?.data;
}

/** https://attack.mitre.org/techniques/T1090/003/ for sub-technique T1090.003,
 * .../T1090/ for a top-level technique without a sub-technique. */
export function mitreTechniqueUrl(techniqueId: string): string {
  const [base, sub] = techniqueId.split(".");
  return sub ? `https://attack.mitre.org/techniques/${base}/${sub}/` : `https://attack.mitre.org/techniques/${base}/`;
}

// The same 8-hue categorical theme as frontend/lib/charts.ts (dataviz
// skill's validated reference palette, references/palette.md), resolved via
// the CSS custom properties app/globals.css defines for it so these badges
// stay accessible in both themes. There are far more MITRE technique IDs
// than 8, so this is a hash, not a 1:1 assignment — collisions are possible,
// but the ID text is always shown alongside the color, so color is never the
// sole identity cue (the one case this skill's "never cycle for an
// open-ended category count" rule doesn't forbid: a tag chip with its own
// text label, not an unlabeled chart series).
const MITRE_PALETTE = [
  "var(--si-cat-1)", // blue
  "var(--si-cat-2)", // orange
  "var(--si-cat-3)", // aqua
  "var(--si-cat-4)", // yellow
  "var(--si-cat-5)", // magenta
  "var(--si-cat-6)", // green
  "var(--si-cat-7)", // violet
  "var(--si-cat-8)", // red
];

export function mitreTechniqueColor(techniqueId: string): { color: string; bg: string } {
  let hash = 0;
  for (let i = 0; i < techniqueId.length; i++) {
    hash = (hash * 31 + techniqueId.charCodeAt(i)) >>> 0;
  }
  const hue = MITRE_PALETTE[hash % MITRE_PALETTE.length];
  // Mixed toward the current surface (not a literal "white") so the tint
  // lands as a light pastel in light mode and a dark, muted tint in dark
  // mode, without needing separate per-theme bg values.
  return { color: hue, bg: `color-mix(in srgb, ${hue} 14%, var(--si-surface))` };
}

export const SEVERITY_STYLE: Record<string, { color: string; bg: string; label: string }> = {
  critical: { color: "var(--si-red)", bg: "var(--si-red-bg)", label: "Kritiek" },
  high: { color: "var(--si-amber)", bg: "var(--si-amber-bg)", label: "Hoog" },
  medium: { color: "var(--si-indigo)", bg: "var(--si-indigo-bg)", label: "Midden" },
  low: { color: "var(--si-neutral)", bg: "var(--si-neutral-bg)", label: "Laag" },
};

// One color per badge group, used consistently in both the feed cards and the
// item detail panel: victim context (teal), vendors/entities (blue), actor (navy).
export const VICTIM_STYLE = { color: "var(--si-teal)", bg: "var(--si-teal-bg)" };
export const ENTITY_STYLE = { color: "var(--si-blue)", bg: "var(--si-blue-bg)" };
export const ACTOR_STYLE = { color: "var(--si-yellow)", bg: "var(--si-yellow-bg)" };

let regionNames: Intl.DisplayNames | null = null;
try {
  regionNames = new Intl.DisplayNames(["nl"], { type: "region" });
} catch {
  regionNames = null;
}

export function countryLabel(code: string): string {
  try {
    return regionNames?.of(code) ?? code;
  } catch {
    return code;
  }
}

export function industryLabel(value: string): string {
  return value.length ? value[0].toUpperCase() + value.slice(1) : value;
}
