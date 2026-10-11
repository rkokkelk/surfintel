"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { apiFetch, getToken } from "@/lib/api";
import type { AlertRule, Item } from "@/lib/types";
import { computeDailyCounts, computeSourceCounts } from "@/lib/dashboard-stats";
import { ItemScreenshot } from "@/components/ItemScreenshot";
import { DailyLineChart } from "@/components/dashboard/DailyLineChart";
import { SourcePieChart } from "@/components/dashboard/SourcePieChart";

const DISPLAY_ITEM_LIMIT = 25;
// Fetched in one go, generous enough that the client-side charts (14-day
// line, per-source pie) have real data to work with — the grid below only
// ever shows the newest DISPLAY_ITEM_LIMIT of these. Backend caps `limit` at
// 100 (GET /alerts/{id}/items), so that's the ceiling here too.
const FETCH_ITEM_LIMIT = 100;
const REFRESH_MS = 2 * 60 * 1000;

function itemDate(item: Item): string {
  return item.published_at ?? item.created_at;
}

function dayLabel(iso: string): string {
  const date = new Date(iso);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  const sameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

  if (sameDay(date, today)) return "Vandaag";
  if (sameDay(date, yesterday)) return "Gisteren";
  return date.toLocaleDateString("nl-NL", { weekday: "long", day: "numeric", month: "long" });
}

function groupByDay(items: Item[]): { label: string; items: Item[] }[] {
  // A real bucket per label, not "merge if the previous item has the same
  // label" — items are ordered by match recency, not by published_at (the
  // only date this endpoint exposes), so the same day's items don't always
  // land next to each other. Grouping only adjacent runs would re-open the
  // same day's group multiple times, giving React duplicate keys.
  const order: string[] = [];
  const buckets = new Map<string, Item[]>();
  for (const item of items) {
    const label = dayLabel(itemDate(item));
    if (!buckets.has(label)) {
      buckets.set(label, []);
      order.push(label);
    }
    buckets.get(label)!.push(item);
  }
  return order.map((label) => ({ label, items: buckets.get(label)! }));
}

export default function AlertDashboardPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const chartsParam = searchParams.get("charts");
  const showCharts = chartsParam !== "false" && chartsParam !== "0";

  const [items, setItems] = useState<Item[] | null>(null);
  const [rule, setRule] = useState<AlertRule | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [now, setNow] = useState(new Date());

  const load = useCallback(() => {
    apiFetch<Item[]>(`/alerts/${params.id}/items?limit=${FETCH_ITEM_LIMIT}`)
      .then((data) => {
        setItems(data);
        setError(null);
        setLastUpdated(new Date());
      })
      .catch(() => setError("Kon het dashboard niet laden."));
  }, [params.id]);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    apiFetch<AlertRule>(`/alerts/${params.id}`)
      .then(setRule)
      .catch(() => {
        /* Non-fatal: admin-only, so a non-admin viewer just gets a generic header. */
      });

    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => clearInterval(interval);
  }, [load, router]);

  // A visible, slowly-ticking clock — a TV wall display is unattended, so
  // "is this thing still alive" has to be answerable at a glance, not by
  // trusting a silent background timer.
  useEffect(() => {
    const clock = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(clock);
  }, []);

  const displayItems = items?.slice(0, DISPLAY_ITEM_LIMIT) ?? [];
  const groups = groupByDay(displayItems);
  const dailyCounts = items ? computeDailyCounts(items) : [];
  const sourceCounts = items ? computeSourceCounts(items) : [];

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--si-bg)",
        padding: "28px 40px 48px",
        display: "flex",
        flexDirection: "column",
        gap: 28,
      }}
    >
      <header style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
        <div className="si-display" style={{ fontSize: 15, fontWeight: 700, color: "var(--si-navy)" }}>
          Surf<span style={{ color: "var(--si-blue)" }}>Intel</span>
        </div>
        <div className="si-display" style={{ fontSize: 34, fontWeight: 700, color: "var(--si-text)" }}>
          {rule?.name ?? "Alert-dashboard"}
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div className="si-mono" style={{ fontSize: 22, fontWeight: 600, color: "var(--si-text)" }}>
            {now.toLocaleTimeString("nl-NL")}
          </div>
          <div style={{ fontSize: 13, color: "var(--si-text-muted)" }}>
            {lastUpdated ? `Bijgewerkt om ${lastUpdated.toLocaleTimeString("nl-NL")}` : "Laden..."}
          </div>
        </div>
      </header>

      {error && <div style={{ color: "var(--si-red)", fontSize: 16 }}>{error}</div>}

      {items && showCharts && (
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
          <div
            style={{
              flex: "2 1 520px",
              background: "var(--si-surface)",
              border: "1px solid var(--si-border)",
              borderRadius: 14,
              padding: "20px 24px",
            }}
          >
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--si-text-secondary)", marginBottom: 10 }}>
              Items per dag (laatste 14 dagen)
            </div>
            <DailyLineChart data={dailyCounts} />
          </div>

          <div
            style={{
              flex: "1 1 360px",
              background: "var(--si-surface)",
              border: "1px solid var(--si-border)",
              borderRadius: 14,
              padding: "20px 24px",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--si-text-secondary)", marginBottom: 10 }}>
              Items per bron
            </div>
            {sourceCounts.length > 0 ? (
              <SourcePieChart data={sourceCounts} />
            ) : (
              <div style={{ color: "var(--si-text-muted)", fontSize: 14 }}>Nog geen hits in deze periode.</div>
            )}
          </div>
        </div>
      )}

      {items && items.length === 0 && (
        <div style={{ fontSize: 18, color: "var(--si-text-muted)" }}>Nog geen items die op deze alert hitten.</div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {groups.map((group) => (
          <div key={group.label} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="si-display" style={{ fontSize: 22, fontWeight: 700, color: "var(--si-navy)", textTransform: "capitalize" }}>
              {group.label}
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
                gap: 20,
              }}
            >
              {group.items.map((item) => (
                <div
                  key={item.id}
                  style={{
                    background: "var(--si-surface)",
                    border: "1px solid var(--si-border)",
                    borderRadius: 12,
                    overflow: "hidden",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <ItemScreenshot itemId={item.id} width="100%" height={210} />
                  <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
                    <div
                      className="si-display"
                      style={{
                        fontSize: 17,
                        fontWeight: 600,
                        color: "var(--si-text)",
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {item.title ?? "(geen titel)"}
                    </div>
                    {item.description && (
                      <div
                        style={{
                          fontSize: 14,
                          color: "var(--si-text-secondary)",
                          lineHeight: 1.45,
                          display: "-webkit-box",
                          WebkitLineClamp: 4,
                          WebkitBoxOrient: "vertical",
                          overflow: "hidden",
                        }}
                      >
                        {item.description}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
