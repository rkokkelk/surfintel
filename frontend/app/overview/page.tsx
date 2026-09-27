"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getToken } from "@/lib/api";
import type { Item } from "@/lib/types";
import { Shell } from "@/components/Shell";
import { FeedCard } from "@/components/FeedCard";
import { ItemDetailPanel } from "@/components/ItemDetailPanel";
import { EMPTY_FILTERS, OverviewFilters, type OverviewFilterState } from "@/components/OverviewFilters";

function buildQuery(filters: OverviewFilterState): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.sourceId) params.set("source_id", filters.sourceId);
  if (filters.cveId) params.set("cve_id", filters.cveId);
  if (filters.from) params.set("published_after", `${filters.from}T00:00:00`);
  if (filters.to) params.set("published_before", `${filters.to}T23:59:59`);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export default function OverviewPage() {
  const router = useRouter();
  const [items, setItems] = useState<Item[]>([]);
  const [filters, setFilters] = useState<OverviewFilterState>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    setLoading(true);
    apiFetch<Item[]>(`/items${buildQuery(filters)}`)
      .then(setItems)
      .catch(() => setError("Kon het nieuwsoverzicht niet laden."))
      .finally(() => setLoading(false));
  }, [filters, router]);

  return (
    <Shell active="overzicht">
      <div style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <div className="si-display" style={{ fontSize: 18, fontWeight: 600 }}>
            Laatste updates
          </div>
          <div style={{ fontSize: 13, color: "var(--si-text-muted)" }}>{items.length} items</div>
        </div>

        <OverviewFilters value={filters} onChange={setFilters} />

        {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
        {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}
        {!loading && !error && items.length === 0 && (
          <div style={{ color: "var(--si-text-muted)" }}>
            {filters.q || filters.sourceId || filters.cveId || filters.from || filters.to
              ? "Geen items gevonden voor deze filters."
              : "Nog geen items. Voeg een bron toe en draai de ingestion-pipeline."}
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 14, maxWidth: 1000 }}>
          {items.map((item) => (
            <FeedCard key={item.id} item={item} onOpenDetail={setSelectedItemId} />
          ))}
        </div>
      </div>
      <ItemDetailPanel itemId={selectedItemId} onClose={() => setSelectedItemId(null)} />
    </Shell>
  );
}
