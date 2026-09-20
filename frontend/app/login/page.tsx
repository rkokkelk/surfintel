"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/overview");
    } catch {
      setError("Ongeldige inloggegevens.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--si-bg)",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: 360,
          background: "var(--si-surface)",
          border: "1px solid var(--si-border)",
          borderRadius: 12,
          padding: 32,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <div className="si-display" style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
          <span style={{ color: "var(--si-navy)" }}>Surf</span>
          <span style={{ color: "var(--si-blue)" }}>Intel</span>
        </div>

        <label style={{ fontSize: 12, fontWeight: 600, color: "var(--si-text-secondary)" }}>
          E-mailadres
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{
              display: "block",
              width: "100%",
              height: 38,
              marginTop: 6,
              border: "1px solid #d8dce3",
              borderRadius: 8,
              padding: "0 12px",
              fontSize: 14,
            }}
          />
        </label>

        <label style={{ fontSize: 12, fontWeight: 600, color: "var(--si-text-secondary)" }}>
          Wachtwoord
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              display: "block",
              width: "100%",
              height: 38,
              marginTop: 6,
              border: "1px solid #d8dce3",
              borderRadius: 8,
              padding: "0 12px",
              fontSize: 14,
            }}
          />
        </label>

        {error && <div style={{ fontSize: 13, color: "var(--si-red)" }}>{error}</div>}

        <button
          type="submit"
          disabled={loading}
          style={{
            height: 40,
            border: "none",
            borderRadius: 8,
            background: "var(--si-blue)",
            color: "#fff",
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          {loading ? "Bezig..." : "Inloggen"}
        </button>

        <div style={{ fontSize: 11, color: "var(--si-text-muted)", textAlign: "center" }}>
          SURFconext-inloggen volgt in een latere fase.
        </div>
      </form>
    </div>
  );
}
