"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError, getToken } from "@/lib/api";
import { isPlatformAdmin } from "@/lib/auth";
import type { Source, SourceType } from "@/lib/types";
import { Shell } from "@/components/Shell";

const TYPE_OPTIONS: { value: SourceType; label: string }[] = [
  { value: "rss", label: "RSS/Atom-feed" },
  { value: "html", label: "HTML-pagina (custom selectors)" },
  { value: "custom_module", label: "Custom module" },
];

interface SourceFormState {
  name: string;
  type: SourceType;
  configText: string;
  poll_interval_seconds: number;
  enabled: boolean;
}

const EMPTY_FORM: SourceFormState = {
  name: "",
  type: "rss",
  configText: '{\n  "feed_url": ""\n}',
  poll_interval_seconds: 3600,
  enabled: true,
};

export default function SourcesPage() {
  const router = useRouter();
  const [authorized, setAuthorized] = useState<boolean | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<SourceFormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function loadSources() {
    setLoading(true);
    apiFetch<Source[]>("/sources")
      .then(setSources)
      .catch(() => setError("Kon de bronnen niet laden."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    if (!isPlatformAdmin()) {
      setAuthorized(false);
      return;
    }
    setAuthorized(true);
    loadSources();
  }, [router]);

  function startCreate() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormError(null);
  }

  function startEdit(source: Source) {
    setEditingId(source.id);
    setForm({
      name: source.name,
      type: source.type,
      configText: JSON.stringify(source.config, null, 2),
      poll_interval_seconds: source.poll_interval_seconds,
      enabled: source.enabled,
    });
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    let config: Record<string, unknown>;
    try {
      config = JSON.parse(form.configText);
    } catch {
      setFormError("Config is geen geldige JSON.");
      return;
    }

    setSaving(true);
    try {
      if (editingId) {
        await apiFetch(`/sources/${editingId}`, {
          method: "PATCH",
          body: JSON.stringify({
            name: form.name,
            type: form.type,
            config,
            enabled: form.enabled,
            poll_interval_seconds: form.poll_interval_seconds,
          }),
        });
      } else {
        await apiFetch("/sources", {
          method: "POST",
          body: JSON.stringify({
            name: form.name,
            type: form.type,
            config,
            poll_interval_seconds: form.poll_interval_seconds,
          }),
        });
      }
      startCreate();
      loadSources();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Opslaan mislukt.");
    } finally {
      setSaving(false);
    }
  }

  if (authorized === false) {
    return (
      <Shell active="sources">
        <div style={{ padding: 32, color: "var(--si-text-muted)" }}>
          Deze pagina is alleen beschikbaar voor platformbeheerders.
        </div>
      </Shell>
    );
  }

  if (authorized === null) {
    return null;
  }

  return (
    <Shell active="sources">
      <div style={{ padding: "22px 24px", display: "flex", gap: 20 }}>
        <div style={{ flex: 1.1, minWidth: 0, display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div className="si-display" style={{ fontSize: 18, fontWeight: 600 }}>
              Bronnen
            </div>
            <div style={{ fontSize: 13, color: "var(--si-text-muted)" }}>{sources.length} bronnen</div>
            <button
              type="button"
              onClick={startCreate}
              style={{
                marginLeft: "auto",
                height: 34,
                padding: "0 16px",
                border: "none",
                borderRadius: 8,
                background: "var(--si-blue)",
                color: "#fff",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              + Nieuwe bron
            </button>
          </div>

          {loading && <div style={{ color: "var(--si-text-muted)" }}>Laden...</div>}
          {error && <div style={{ color: "var(--si-red)" }}>{error}</div>}

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {sources.map((source) => (
              <button
                key={source.id}
                onClick={() => startEdit(source)}
                style={{
                  textAlign: "left",
                  background: editingId === source.id ? "#eaf2fb" : "var(--si-surface)",
                  border: editingId === source.id ? "1px solid var(--si-blue)" : "1px solid var(--si-border)",
                  borderRadius: 10,
                  padding: "14px 16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                  cursor: "pointer",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ display: "flex", alignItems: "left", gap: 20 }}>
                    <img 
                      src={`data:image/png;base64,${source.favicon}`} 
                      height="20px"
                      width="20px"
                      />
                  </div>
                  <span style={{ fontSize: 13.5, fontWeight: 600, color: "var(--si-text)" }}>{source.name}</span>
                  <span
                    className="si-mono"
                    style={{ fontSize: 11, color: "#425066", background: "#eef1f5", borderRadius: 6, padding: "2px 8px" }}
                  >
                    {source.type}
                  </span>
                  <span
                    style={{
                      marginLeft: "auto",
                      fontSize: 11,
                      fontWeight: 600,
                      color: source.enabled ? "var(--si-green)" : "var(--si-text-muted)",
                      background: source.enabled ? "var(--si-green-bg)" : "#f1f3f6",
                      borderRadius: 9,
                      padding: "2px 9px",
                    }}
                  >
                    {source.enabled ? "Actief" : "Gepauzeerd"}
                  </span>
                </div>
                <div style={{ fontSize: 11.5, color: "var(--si-text-muted)" }}>
                  elke {Math.round(source.poll_interval_seconds / 60)} min ·{" "}
                  {source.last_polled_at
                    ? `laatst gepolld ${new Date(source.last_polled_at).toLocaleString("nl-NL")}`
                    : "nog niet gepolld"}
                </div>
              </button>
            ))}
          </div>
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
            gap: 14,
            alignSelf: "flex-start",
          }}
        >
          <div className="si-display" style={{ fontSize: 15, fontWeight: 600 }}>
            {editingId ? "Bron bewerken" : "Nieuwe bron"}
          </div>

          <label style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
            Naam
            <input
              required
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="bv. Security.NL"
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

          <label style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
            Type
            <select
              value={form.type}
              onChange={(e) => setForm((f) => ({ ...f, type: e.target.value as SourceType }))}
              style={{
                display: "block",
                width: "100%",
                height: 36,
                marginTop: 6,
                border: "1px solid #d8dce3",
                borderRadius: 8,
                padding: "0 10px",
                fontSize: 13.5,
              }}
            >
              {TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>

          <label style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
            Config (JSON)
            <textarea
              required
              value={form.configText}
              onChange={(e) => setForm((f) => ({ ...f, configText: e.target.value }))}
              rows={7}
              spellCheck={false}
              className="si-mono"
              style={{
                display: "block",
                width: "100%",
                marginTop: 6,
                border: "1px solid #d8dce3",
                borderRadius: 8,
                padding: "10px 12px",
                fontSize: 12.5,
                resize: "vertical",
              }}
            />
          </label>
          <div style={{ fontSize: 11, color: "var(--si-text-muted)" }}>
            {form.type === "rss" && <>rss verwacht: {`{ "feed_url": "..." }`}</>}
            {form.type === "html" && (
              <>html verwacht: {`{ "feed_url", "row_identifier", "item": { "title", "link", "description" } }`}</>
            )}
            {form.type === "custom_module" && <>vrije vorm, geïnterpreteerd door de geregistreerde module</>}
          </div>

          <label style={{ fontSize: 11.5, fontWeight: 600, color: "var(--si-text-secondary)" }}>
            Poll-interval (seconden)
            <input
              type="number"
              min={60}
              required
              value={form.poll_interval_seconds}
              onChange={(e) => setForm((f) => ({ ...f, poll_interval_seconds: Number(e.target.value) }))}
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

          {editingId && (
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--si-text)" }}>
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))}
              />
              Actief (wordt meegenomen in de ingestion-cyclus)
            </label>
          )}

          {formError && <div style={{ fontSize: 12, color: "var(--si-red)" }}>{formError}</div>}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            {editingId && (
              <button
                type="button"
                onClick={startCreate}
                style={{
                  height: 36,
                  padding: "0 16px",
                  border: "1px solid #d8dce3",
                  borderRadius: 8,
                  background: "#fff",
                  color: "#384152",
                  fontSize: 13,
                  fontWeight: 500,
                }}
              >
                Annuleren
              </button>
            )}
            <button
              type="submit"
              disabled={saving}
              style={{
                marginLeft: "auto",
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
              {saving ? "Opslaan..." : editingId ? "Wijzigingen opslaan" : "Bron aanmaken"}
            </button>
          </div>
        </form>
      </div>
    </Shell>
  );
}
