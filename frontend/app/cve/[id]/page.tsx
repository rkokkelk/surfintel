"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { apiFetch, getToken } from "@/lib/api";
import type { CveDetail } from "@/lib/types";
import { Shell } from "@/components/Shell";
import { CveDetailContent } from "@/components/CveDetailContent";
import { CveDetailPanel } from "@/components/CveDetailPanel";
import { ItemDetailPanel } from "@/components/ItemDetailPanel";

export default function CveDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [cve, setCve] = useState<CveDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [selectedCveId, setSelectedCveId] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    setLoading(true);
    setError(null);
    apiFetch<CveDetail>(`/cves/${params.id}`)
      .then(setCve)
      .catch(() => setError("Kon deze CVE niet laden."))
      .finally(() => setLoading(false));
  }, [params.id, router]);

  return (
    <Shell active="cve">
      <div style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 18, maxWidth: 920 }}>
        <Link href="/cve" style={{ fontSize: 12.5, color: "var(--si-blue)" }}>
          ← Terug naar CVE database
        </Link>

        {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
        {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}
        {cve && <CveDetailContent cve={cve} onOpenItem={setSelectedItemId} />}
      </div>
      <ItemDetailPanel itemId={selectedItemId} onClose={() => setSelectedItemId(null)} onOpenCve={setSelectedCveId} />
      <CveDetailPanel
        cveId={selectedCveId}
        onClose={() => setSelectedCveId(null)}
        onOpenItem={(id) => {
          setSelectedCveId(null);
          setSelectedItemId(id);
        }}
      />
    </Shell>
  );
}
