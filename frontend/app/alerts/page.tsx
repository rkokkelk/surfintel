"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError, getToken } from "@/lib/api";
import type { AlertField, AlertRule } from "@/lib/types";
import { Shell } from "@/components/Shell";

const FIELD_OPTIONS: { value: AlertField; label: string }[] = [
  { value: "vendor", label: "Vendor" },
  { value: "product", label: "Product" },
  { value: "severity", label: "Severity" },
  { value: "category", label: "Categorie" },
  { value: "cve_id", label: "CVE-ID" },
  { value: "source", label: "Bron" },
  { value: "tag", label: "Tag" },
  { value: "keyword", label: "Zoekterm" },
];

interface ConditionDraft {
  field: AlertField;
  values: string;
}

export default function AlertsPage() {
  const router = useRouter();
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [conditions, setConditions] = useState<ConditionDraft[]>([{ field: "vendor", values: "" }]);
  const [channelLabel, setChannelLabel] = useState("");
  const [appriseUrl, setAppriseUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function loadRules() {
    setLoading(true);
    apiFetch<AlertRule[]>("/alerts")
      .then(setRules)
      .catch(() => setError("Kon de alert-regels niet laden."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    loadRules();
  }, [router]);

  function updateCondition(index: number, patch: Partial<ConditionDraft>) {
    setConditions((prev) => prev.map((c, i) => (i === index ? { ...c, ...patch } : c)));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    setSaving(true);
    try {
      await apiFetch("/alerts", {
        method: "POST",
        body: JSON.stringify({
          name,
          conditions: conditions
            .filter((c) => c.values.trim().length > 0)
            .map((c) => ({ field: c.field, values: c.values.split(",").map((v) => v.trim()) })),
          channels: appriseUrl
            ? [{ label: channelLabel || "Kanaal", apprise_url: appriseUrl }]
            : [],
        }),
      });
      setName("");
      setConditions([{ field: "vendor", values: "" }]);
      setChannelLabel("");
      setAppriseUrl("");
      loadRules();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Opslaan mislukt.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Shell active="alerts">
      <div style={{ padding: "22px 24px", display: "flex", gap: 20 }}>
        <div style={{ flex: 1.05, minWidth: 0, display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="si-display" style={{ fontSize: 15, fontWeight: 600 }}>
            Bestaande alert-regels
          </div>

          {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
          {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}
          {!loading && rules.length === 0 && (
            <div style={{ color: "var(--si-text-muted)" }}>Nog geen alert-regels voor deze instelling.</div>
          )}

          {rules.map((rule) => (
            <div
              key={rule.id}
              style={{
                background: "var(--si-surface)",
                border: "1px solid var(--si-border)",
                borderRadius: 10,
                padding: "14px 16px",
                display: "flex",
                flexDirection: "column",
                gap: 9,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 13.5, fontWeight: 600 }}>{rule.name}</span>
                <span
                  style={{
                    marginLeft: "auto",
                    fontSize: 11,
                    fontWeight: 600,
                    color: rule.status === "active" ? "var(--si-green)" : "var(--si-text-muted)",
                    background: rule.status === "active" ? "var(--si-green-bg)" : "#f1f3f6",
                    borderRadius: 9,
                    padding: "2px 9px",
                  }}
                >
                  {rule.status === "active" ? "Actief" : "Gepauzeerd"}
                </span>
              </div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {rule.conditions.map((c) => (
                  <span
                    key={c.id}
                    className="si-mono"
                    style={{ fontSize: 11.5, color: "#374151", background: "#f5f6f8", borderRadius: 6, padding: "2px 8px" }}
                  >
                    {c.field}: {c.values.join(", ")}
                  </span>
                ))}
              </div>
              <div style={{ fontSize: 11.5, color: "var(--si-text-muted)" }}>
                {rule.channels.map((ch) => ch.apprise_url_masked).join(", ") || "Geen notificatiekanalen"}
              </div>
            </div>
          ))}
        </div>

        <form
          onSubmit={handleSubmit}
          style={{
            flex: 1,
            minWidth: 0,
            background: "var(--si-surface)",
            border: "1px solid var(--si-border)",
            borderRadius: 12,
            padding: "20px 22px",
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <div className="si-display" style={{ fontSize: 15, fontWeight: 600 }}>
            Nieuwe alert-regel
          </div>

          <label style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
            Naam
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="bv. Kritieke kwetsbaarheden in VPN-appliances"
              style={{
                display: "block",
                width: "100%",
                height: 36,
                marginTop: 6,
                border: "1px solid #d8dce3",
                borderRadius: 8,
                padding: "0 12px",
                fontSize: 13.5,
              }}
            />
          </label>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
              Voorwaarden (AND; komma-gescheiden waarden = OR)
            </div>
            {conditions.map((condition, index) => (
              <div key={index} style={{ display: "flex", gap: 6 }}>
                <select
                  value={condition.field}
                  onChange={(e) => updateCondition(index, { field: e.target.value as AlertField })}
                  style={{ height: 32, border: "1px solid #d8dce3", borderRadius: 7, fontSize: 12.5 }}
                >
                  {FIELD_OPTIONS.map((f) => (
                    <option key={f.value} value={f.value}>
                      {f.label}
                    </option>
                  ))}
                </select>
                <input
                  value={condition.values}
                  onChange={(e) => updateCondition(index, { values: e.target.value })}
                  placeholder="bv. Ivanti, Fortinet"
                  style={{ flexGrow: 1, height: 32, border: "1px solid #d8dce3", borderRadius: 7, padding: "0 10px", fontSize: 12.5 }}
                />
              </div>
            ))}
            <button
              type="button"
              onClick={() => setConditions((prev) => [...prev, { field: "severity", values: "" }])}
              style={{ alignSelf: "flex-start", border: "none", background: "none", color: "var(--si-blue)", fontSize: 12.5, fontWeight: 600 }}
            >
              + Voorwaarde toevoegen
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
              Notificatiekanaal (Apprise-URL)
            </div>
            <input
              value={channelLabel}
              onChange={(e) => setChannelLabel(e.target.value)}
              placeholder="Label, bv. SOC-team Slack"
              style={{ height: 32, border: "1px solid #d8dce3", borderRadius: 7, padding: "0 10px", fontSize: 12.5 }}
            />
            <input
              value={appriseUrl}
              onChange={(e) => setAppriseUrl(e.target.value)}
              placeholder="bv. slack://TokenA/TokenB/TokenC/kanaal"
              style={{ height: 32, border: "1px solid #d8dce3", borderRadius: 7, padding: "0 10px", fontSize: 12.5 }}
            />
          </div>

          {formError && <div style={{ fontSize: 12, color: "var(--si-red)" }}>{formError}</div>}

          <button
            type="submit"
            disabled={saving}
            style={{
              alignSelf: "flex-end",
              height: 36,
              padding: "0 18px",
              border: "none",
              borderRadius: 8,
              background: "var(--si-navy)",
              color: "#fff",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            {saving ? "Opslaan..." : "Alert-regel opslaan"}
          </button>
        </form>
      </div>
    </Shell>
  );
}
