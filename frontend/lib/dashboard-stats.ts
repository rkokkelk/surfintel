import type { AlertDashboardDayCount, AlertDashboardSourceCount, Item } from "@/lib/types";

const WINDOW_DAYS = 14;
const SOURCE_CAP = 7; // past this, fold the tail into "Overig" — dataviz skill's series-count ladder

// GET /alerts/{id}/items has no concept of "when the alert matched" (that's
// AlertMatch.matched_at, not exposed here) — published_at is the closest
// thing to "when this happened" on a plain Item, falling back to created_at
// for the rare item without one.
function itemDate(item: Item): string {
  return item.published_at ?? item.created_at;
}

function dateKey(iso: string): string {
  return iso.slice(0, 10); // YYYY-MM-DD, UTC
}

/** Daily hit counts for the last WINDOW_DAYS days, zero-filled and sorted
 * oldest-to-newest so the line chart has a continuous, correctly-ordered
 * x-axis even on days without a match. */
export function computeDailyCounts(items: Item[]): AlertDashboardDayCount[] {
  const counts = new Map<string, number>();
  const today = new Date();
  for (let offset = 0; offset < WINDOW_DAYS; offset++) {
    const d = new Date(today);
    d.setDate(d.getDate() - offset);
    counts.set(d.toISOString().slice(0, 10), 0);
  }

  for (const item of items) {
    const key = dateKey(itemDate(item));
    if (counts.has(key)) {
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
  }

  return Array.from(counts.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date, count }));
}

/** Hit counts per source, highest first, capped at SOURCE_CAP with the
 * remainder folded into a single "Overig" entry. */
export function computeSourceCounts(items: Item[]): AlertDashboardSourceCount[] {
  const tally = new Map<string, { favicon: string | null; count: number }>();
  for (const item of items) {
    const entry = tally.get(item.source.name) ?? { favicon: item.source.favicon || null, count: 0 };
    entry.count += 1;
    tally.set(item.source.name, entry);
  }

  const ranked = Array.from(tally.entries()).sort((a, b) => b[1].count - a[1].count);
  const top = ranked.slice(0, SOURCE_CAP).map(([source_name, data]) => ({
    source_name,
    source_favicon: data.favicon,
    count: data.count,
  }));
  const restCount = ranked.slice(SOURCE_CAP).reduce((sum, [, data]) => sum + data.count, 0);
  if (restCount > 0) {
    top.push({ source_name: "Overig", source_favicon: null, count: restCount });
  }
  return top;
}
