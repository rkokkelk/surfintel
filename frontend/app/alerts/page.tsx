"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError, getToken } from "@/lib/api";
import type { AlertField, AlertRule, AlertTestMatch } from "@/lib/types";
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
  { value: "cvss_score", label: "CVSS-score (hoger dan)" },
  { value: "epss_score", label: "EPSS-score % (hoger dan)" },
  { value: "kev", label: "CISA KEV" },
];

// Matched with >= against the item's max CVSS/EPSS across all its CVEs
// (see THRESHOLD_FIELDS in backend/app/alerting/match_view.py) — a single
// number, not an OR-list like the other fields.
const THRESHOLD_FIELDS: AlertField[] = ["cvss_score", "epss_score"];

const TEMPLATE_PLACEHOLDERS = [
  { token: "{title}", desc: "Titel van het item" },
  { token: "{url}", desc: "Link naar het item" },
  { token: "{source}", desc: "Naam van de bron" },
  { token: "{rule_name}", desc: "Naam van deze alert-regel" },
  { token: "{published_at}", desc: "Publicatiedatum" },
  { token: "{description}", desc: "Omschrijving van het item" },
  { token: "{vendor}", desc: "Vendor(s), indien herkend" },
  { token: "{product}", desc: "Product(en), indien herkend" },
  { token: "{severity}", desc: "Severity, indien herkend" },
  { token: "{category}", desc: "Categorie, indien herkend" },
  { token: "{cve_id}", desc: "CVE-ID('s), indien gevonden" },
  { token: "{cvss_score}", desc: "Hoogste CVSS-score onder de gekoppelde CVE's" },
  { token: "{epss_score}", desc: "Hoogste EPSS-score onder de gekoppelde CVE's (fractie 0-1)" },
  { token: "{kev}", desc: "\"true\" als een gekoppelde CVE in de CISA KEV-catalogus staat" },
];

interface ConditionDraft {
  field: AlertField;
  values: string;
}

interface ChannelDraft {
  id: string | null;
  label: string;
  apprise_url: string;
  apprise_url_masked: string | null;
  enabled: boolean;
}

interface FormState {
  name: string;
  status: "active" | "paused";
  conditions: ConditionDraft[];
  channels: ChannelDraft[];
  messageTemplate: string;
}

function emptyForm(): FormState {
  return {
    name: "",
    status: "active",
    conditions: [{ field: "vendor", values: "" }],
    channels: [{ id: null, label: "", apprise_url: "", apprise_url_masked: null, enabled: true }],
    messageTemplate: "",
  };
}

function conditionValuesToDraft(field: AlertField, values: string[]): string {
  if (field === "epss_score") {
    // Stored/matched as a 0-1 fraction; shown to the user as a percentage.
    const fraction = Number(values[0]);
    return Number.isFinite(fraction) ? String(fraction * 100) : "";
  }
  if (THRESHOLD_FIELDS.includes(field) || field === "kev") {
    return values[0] ?? "";
  }
  return values.join(", ");
}

function formFromRule(rule: AlertRule): FormState {
  return {
    name: rule.name,
    status: rule.status,
    conditions: rule.conditions.map((c) => ({ field: c.field, values: conditionValuesToDraft(c.field, c.values) })),
    channels: rule.channels.map((c) => ({
      id: c.id,
      label: c.label,
      apprise_url: "",
      apprise_url_masked: c.apprise_url_masked,
      enabled: c.enabled,
    })),
    messageTemplate: rule.message_template ?? "",
  };
}

function fieldStyle(): React.CSSProperties {
  return {
    height: 32,
    border: "1px solid #d8dce3",
    borderRadius: 7,
    padding: "0 10px",
    fontSize: 12.5,
  };
}

export default function AlertsPage() {
  const router = useRouter();
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [testResults, setTestResults] = useState<AlertTestMatch[] | null>(null);
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);

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

  function startNewRule() {
    setSelectedRuleId(null);
    setForm(emptyForm());
    setFormError(null);
    setTestResults(null);
    setTestError(null);
  }

  function startEditRule(rule: AlertRule) {
    setSelectedRuleId(rule.id);
    setForm(formFromRule(rule));
    setFormError(null);
    setTestResults(null);
    setTestError(null);
  }

  function updateCondition(index: number, patch: Partial<ConditionDraft>) {
    setForm((prev) => ({
      ...prev,
      conditions: prev.conditions.map((c, i) => (i === index ? { ...c, ...patch } : c)),
    }));
  }

  function removeCondition(index: number) {
    setForm((prev) => ({ ...prev, conditions: prev.conditions.filter((_, i) => i !== index) }));
  }

  function updateChannel(index: number, patch: Partial<ChannelDraft>) {
    setForm((prev) => ({
      ...prev,
      channels: prev.channels.map((c, i) => (i === index ? { ...c, ...patch } : c)),
    }));
  }

  function removeChannel(index: number) {
    setForm((prev) => ({ ...prev, channels: prev.channels.filter((_, i) => i !== index) }));
  }

  function buildConditionsPayload() {
    return form.conditions
      .filter((c) => c.values.trim().length > 0)
      .map((c) => {
        if (c.field === "epss_score") {
          // Entered as a 0-100 percentage; stored/matched as the 0-1 fraction
          // OpenCVE reports (same convention as the Overview EPSS filter).
          return { field: c.field, values: [String(Number(c.values) / 100)] };
        }
        if (THRESHOLD_FIELDS.includes(c.field) || c.field === "kev") {
          return { field: c.field, values: [c.values.trim()] };
        }
        return { field: c.field, values: c.values.split(",").map((v) => v.trim()).filter(Boolean) };
      });
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    setSaving(true);
    try {
      const conditions = buildConditionsPayload();
      const messageTemplate = form.messageTemplate.trim() || null;

      if (selectedRuleId) {
        const channels = form.channels
          .filter((c) => c.label.trim().length > 0)
          .map((c) => ({
            id: c.id,
            label: c.label,
            apprise_url: c.apprise_url.trim() ? c.apprise_url.trim() : undefined,
            enabled: c.enabled,
          }));
        const updated = await apiFetch<AlertRule>(`/alerts/${selectedRuleId}`, {
          method: "PUT",
          body: JSON.stringify({ name: form.name, status: form.status, conditions, channels, message_template: messageTemplate }),
        });
        startEditRule(updated);
      } else {
        const channels = form.channels
          .filter((c) => c.label.trim().length > 0 && c.apprise_url.trim().length > 0)
          .map((c) => ({ label: c.label, apprise_url: c.apprise_url.trim() }));
        await apiFetch("/alerts", {
          method: "POST",
          body: JSON.stringify({ name: form.name, conditions, channels, message_template: messageTemplate }),
        });
        startNewRule();
      }
      loadRules();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Opslaan mislukt.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!selectedRuleId) return;
    if (!window.confirm(`"${form.name}" verwijderen? Dit kan niet ongedaan gemaakt worden.`)) return;
    setDeleting(true);
    setFormError(null);
    try {
      await apiFetch(`/alerts/${selectedRuleId}`, { method: "DELETE" });
      startNewRule();
      loadRules();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Verwijderen mislukt.");
    } finally {
      setDeleting(false);
    }
  }

  async function handleTest() {
    if (!selectedRuleId) return;
    setTesting(true);
    setTestError(null);
    setTestResults(null);
    try {
      const conditions = buildConditionsPayload();
      const results = await apiFetch<AlertTestMatch[]>(`/alerts/${selectedRuleId}/test`, {
        method: "POST",
        body: JSON.stringify({ conditions, message_template: form.messageTemplate.trim() || null }),
      });
      setTestResults(results);
    } catch (err) {
      setTestError(err instanceof ApiError ? err.message : "Testen mislukt.");
    } finally {
      setTesting(false);
    }
  }

  return (
    <Shell active="alerts">
      <div style={{ padding: "22px 24px", display: "flex", gap: 20 }}>
        <div style={{ flex: 1.05, minWidth: 0, display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div className="si-display" style={{ fontSize: 15, fontWeight: 600 }}>
              Bestaande alert-regels
            </div>
            <button
              type="button"
              onClick={startNewRule}
              style={{
                marginLeft: "auto",
                border: "1px solid var(--si-border)",
                background: selectedRuleId === null ? "var(--si-navy)" : "#fff",
                color: selectedRuleId === null ? "#fff" : "var(--si-text)",
                borderRadius: 7,
                fontSize: 12,
                fontWeight: 600,
                padding: "5px 10px",
                cursor: "pointer",
              }}
            >
              + Nieuwe regel
            </button>
          </div>

          {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
          {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}
          {!loading && rules.length === 0 && (
            <div style={{ color: "var(--si-text-muted)" }}>Nog geen alert-regels voor deze instelling.</div>
          )}

          {rules.map((rule) => (
            <button
              key={rule.id}
              type="button"
              onClick={() => startEditRule(rule)}
              style={{
                textAlign: "left",
                cursor: "pointer",
                background: "var(--si-surface)",
                border: `1px solid ${selectedRuleId === rule.id ? "var(--si-blue)" : "var(--si-border)"}`,
                borderRadius: 10,
                padding: "14px 16px",
                display: "flex",
                flexDirection: "column",
                gap: 9,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 13.5, fontWeight: 600, color: "var(--si-text)" }}>{rule.name}</span>
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
                    {c.field === "kev"
                      ? "moet in KEV staan"
                      : c.field === "cvss_score"
                        ? `CVSS ≥ ${c.values[0]}`
                        : c.field === "epss_score"
                          ? `EPSS ≥ ${(Number(c.values[0]) * 100).toFixed(0)}%`
                          : `${c.field}: ${c.values.join(", ")}`}
                  </span>
                ))}
              </div>
              <div style={{ fontSize: 11.5, color: "var(--si-text-muted)" }}>
                {rule.channels.map((ch) => ch.apprise_url_masked).join(", ") || "Geen notificatiekanalen"}
              </div>
            </button>
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
            alignSelf: "flex-start",
          }}
        >
          <div className="si-display" style={{ fontSize: 15, fontWeight: 600 }}>
            {selectedRuleId ? "Alert-regel bewerken" : "Nieuwe alert-regel"}
          </div>

          <label style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
            Naam
            <input
              required
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
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

          {selectedRuleId && (
            <label style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
              Status
              <select
                value={form.status}
                onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value as "active" | "paused" }))}
                style={{ display: "block", marginTop: 6, ...fieldStyle(), height: 34, width: 180 }}
              >
                <option value="active">Actief</option>
                <option value="paused">Gepauzeerd</option>
              </select>
            </label>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
              Voorwaarden (AND; komma-gescheiden waarden = OR)
            </div>
            {form.conditions.map((condition, index) => (
              <div key={index} style={{ display: "flex", gap: 6 }}>
                <select
                  value={condition.field}
                  onChange={(e) => updateCondition(index, { field: e.target.value as AlertField, values: "" })}
                  style={fieldStyle()}
                >
                  {FIELD_OPTIONS.map((f) => (
                    <option key={f.value} value={f.value}>
                      {f.label}
                    </option>
                  ))}
                </select>
                {condition.field === "kev" ? (
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: "var(--si-text)", flexGrow: 1 }}>
                    <input
                      type="checkbox"
                      checked={condition.values === "true"}
                      onChange={(e) => updateCondition(index, { values: e.target.checked ? "true" : "" })}
                    />
                    Moet in KEV staan
                  </label>
                ) : condition.field === "cvss_score" ? (
                  <input
                    type="number"
                    min={0}
                    max={10}
                    step={0.1}
                    value={condition.values}
                    onChange={(e) => updateCondition(index, { values: e.target.value })}
                    placeholder="bv. 7"
                    className="si-mono"
                    style={{ ...fieldStyle(), width: 100 }}
                  />
                ) : condition.field === "epss_score" ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step={1}
                      value={condition.values}
                      onChange={(e) => updateCondition(index, { values: e.target.value })}
                      placeholder="bv. 10"
                      className="si-mono"
                      style={{ ...fieldStyle(), width: 100 }}
                    />
                    <span style={{ fontSize: 12.5, color: "var(--si-text-muted)" }}>%</span>
                  </div>
                ) : (
                  <input
                    value={condition.values}
                    onChange={(e) => updateCondition(index, { values: e.target.value })}
                    placeholder="bv. Ivanti, Fortinet"
                    style={{ ...fieldStyle(), flexGrow: 1 }}
                  />
                )}
                {form.conditions.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeCondition(index)}
                    title="Voorwaarde verwijderen"
                    style={{ border: "none", background: "none", color: "var(--si-text-muted)", fontSize: 15, cursor: "pointer" }}
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => setForm((prev) => ({ ...prev, conditions: [...prev.conditions, { field: "severity", values: "" }] }))}
              style={{ alignSelf: "flex-start", border: "none", background: "none", color: "var(--si-blue)", fontSize: 12.5, fontWeight: 600, cursor: "pointer" }}
            >
              + Voorwaarde toevoegen
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
              Notificatiekanalen (Apprise-URL)
            </div>
            {form.channels.map((channel, index) => (
              <div key={index} style={{ display: "flex", flexDirection: "column", gap: 4, border: "1px solid #eceff3", borderRadius: 8, padding: 8 }}>
                <div style={{ display: "flex", gap: 6 }}>
                  <input
                    value={channel.label}
                    onChange={(e) => updateChannel(index, { label: e.target.value })}
                    placeholder="Label, bv. SOC-team Slack"
                    style={{ ...fieldStyle(), flexGrow: 1 }}
                  />
                  <label style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11.5, color: "var(--si-text-muted)" }}>
                    <input type="checkbox" checked={channel.enabled} onChange={(e) => updateChannel(index, { enabled: e.target.checked })} />
                    Aan
                  </label>
                  {form.channels.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeChannel(index)}
                      title="Kanaal verwijderen"
                      style={{ border: "none", background: "none", color: "var(--si-text-muted)", fontSize: 15, cursor: "pointer" }}
                    >
                      ×
                    </button>
                  )}
                </div>
                <input
                  value={channel.apprise_url}
                  onChange={(e) => updateChannel(index, { apprise_url: e.target.value })}
                  placeholder={
                    channel.apprise_url_masked
                      ? `Laat leeg om te behouden (${channel.apprise_url_masked})`
                      : "bv. slack://TokenA/TokenB/TokenC/kanaal"
                  }
                  style={fieldStyle()}
                />
              </div>
            ))}
            <button
              type="button"
              onClick={() =>
                setForm((prev) => ({
                  ...prev,
                  channels: [...prev.channels, { id: null, label: "", apprise_url: "", apprise_url_masked: null, enabled: true }],
                }))
              }
              style={{ alignSelf: "flex-start", border: "none", background: "none", color: "var(--si-blue)", fontSize: 12.5, fontWeight: 600, cursor: "pointer" }}
            >
              + Kanaal toevoegen
            </button>
          </div>

          <details style={{ border: "1px solid #eceff3", borderRadius: 8, padding: "8px 10px" }}>
            <summary style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)", cursor: "pointer" }}>
              Advanced: berichtsjabloon
            </summary>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 10 }}>
              <div style={{ fontSize: 11.5, color: "var(--si-text-muted)" }}>
                Pas de tekst van de notificatie aan. Leeg = standaardbericht (titel + link).
              </div>
              <textarea
                value={form.messageTemplate}
                onChange={(e) => setForm((prev) => ({ ...prev, messageTemplate: e.target.value }))}
                placeholder={"{title}\n{url}"}
                rows={4}
                style={{ border: "1px solid #d8dce3", borderRadius: 7, padding: "8px 10px", fontSize: 12.5, fontFamily: "var(--si-mono, monospace)", resize: "vertical" }}
              />
              <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                {TEMPLATE_PLACEHOLDERS.map((p) => (
                  <span
                    key={p.token}
                    className="si-mono"
                    title={p.desc}
                    style={{ fontSize: 10.5, color: "#374151", background: "#f5f6f8", borderRadius: 5, padding: "2px 6px" }}
                  >
                    {p.token}
                  </span>
                ))}
              </div>
            </div>
          </details>

          {formError && <div style={{ fontSize: 12, color: "var(--si-red)" }}>{formError}</div>}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            {selectedRuleId && (
              <>
                <button
                  type="button"
                  onClick={handleTest}
                  disabled={testing}
                  style={{
                    height: 36,
                    padding: "0 16px",
                    border: "1px solid var(--si-border)",
                    borderRadius: 8,
                    background: "#fff",
                    color: "var(--si-text)",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {testing ? "Testen..." : "Testen"}
                </button>
                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={deleting}
                  style={{
                    height: 36,
                    padding: "0 16px",
                    border: "1px solid var(--si-red)",
                    borderRadius: 8,
                    background: "#fff",
                    color: "var(--si-red)",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {deleting ? "Verwijderen..." : "Verwijderen"}
                </button>
              </>
            )}
            <button
              type="submit"
              disabled={saving}
              style={{
                height: 36,
                padding: "0 18px",
                border: "none",
                borderRadius: 8,
                background: "var(--si-navy)",
                color: "#fff",
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {saving ? "Opslaan..." : selectedRuleId ? "Wijzigingen opslaan" : "Alert-regel opslaan"}
            </button>
          </div>

          {(testError || testResults) && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, borderTop: "1px solid var(--si-border)", paddingTop: 14 }}>
              <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
                Meest recente hits {testResults ? `(${testResults.length})` : ""}
              </div>
              {testError && <div style={{ fontSize: 12, color: "var(--si-red)" }}>{testError}</div>}
              {testResults && testResults.length === 0 && (
                <div style={{ fontSize: 12.5, color: "var(--si-text-muted)" }}>
                  Geen recente items komen overeen met deze voorwaarden.
                </div>
              )}
              {testResults?.map((match) => (
                <div
                  key={match.item_id}
                  style={{ border: "1px solid #eceff3", borderRadius: 8, padding: "9px 11px", display: "flex", flexDirection: "column", gap: 5 }}
                >
                  <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--si-text)", flexGrow: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {match.title ?? match.url}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--si-text-muted)", flexShrink: 0 }}>{match.source_name}</span>
                  </div>
                  <div style={{ fontSize: 11.5, color: "var(--si-text-muted)", whiteSpace: "pre-wrap" }}>{match.message_preview}</div>
                </div>
              ))}
            </div>
          )}
        </form>
      </div>
    </Shell>
  );
}
