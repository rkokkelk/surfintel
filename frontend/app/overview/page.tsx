"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getToken, imgFetch } from "@/lib/api";
import type { Item } from "@/lib/types";
import { Shell } from "@/components/Shell";
import { FeedCard } from "@/components/FeedCard";

const CATEGORIES = [
  { value: null, label: "Alles" },
  { value: "advisory", label: "Advisories" },
  { value: "malware", label: "Malware" },
  { value: "patch", label: "Patches" },
];

export default function OverviewPage() {
  const router = useRouter();
  const [items, setItems] = useState<Item[]>([]);
  const [category, setCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    setLoading(true);
    const query = category ? `?category=${category}` : "";
    apiFetch<Item[]>(`/items${query}`)
      .then(setItems)
      .catch(() => setError("Kon het nieuwsoverzicht niet laden."))
      .finally(() => setLoading(false));
  }, [category, router]);

  return (
    <Shell active="overzicht">
      <div style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <div className="si-display" style={{ fontSize: 18, fontWeight: 600 }}>
            Laatste updates
          </div>
          <div style={{ fontSize: 13, color: "var(--si-text-muted)" }}>{items.length} items</div>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          {CATEGORIES.map((c) => (
            <button
              key={c.label}
              onClick={() => setCategory(c.value)}
              style={{
                height: 30,
                padding: "0 14px",
                borderRadius: 15,
                border: category === c.value ? "none" : "1px solid #d8dce3",
                background: category === c.value ? "var(--si-navy)" : "#fff",
                color: category === c.value ? "#fff" : "#384152",
                fontSize: 13,
                fontWeight: 500,
              }}
            >
              {c.label}
            </button>
          ))}
        </div>

        {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
        {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}
        {!loading && !error && items.length === 0 && (
          <div style={{ color: "var(--si-text-muted)" }}>
            Nog geen items. Voeg een bron toe en draai de ingestion-pipeline.
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 14, maxWidth: 800 }}>
          {items.map((item) => (
            <FeedCard key={item.id} item={item} />
          ))}
        </div>
      </div>
    </Shell>
  );
}
