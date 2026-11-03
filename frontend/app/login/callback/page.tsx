"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { setToken } from "@/lib/api";

export default function OAuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    // Extract access token from URL hash
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    const accessToken = params.get("access_token");

    if (accessToken) {
      // Store the token
      setToken(accessToken);
      // Redirect to overview page
      router.push("/overview");
    } else {
      // No token found, redirect to login with error
      router.push("/login?error=oauth_failed");
    }
  }, [router]);

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
      <div
        style={{
          width: 360,
          background: "var(--si-surface)",
          border: "1px solid var(--si-border)",
          borderRadius: 12,
          padding: 32,
          textAlign: "center",
        }}
      >
        <div className="si-display" style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>
          <span style={{ color: "var(--si-navy)" }}>Surf</span>
          <span style={{ color: "var(--si-blue)" }}>Intel</span>
        </div>
        <p style={{ color: "var(--si-text-secondary)" }}>Bezig met inloggen...</p>
      </div>
    </div>
  );
}
