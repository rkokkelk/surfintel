"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";
import { isPlatformAdmin } from "@/lib/auth";

export function Shell({
  active,
  children,
}: {
  active: "overzicht" | "alerts" | "cve" | "sources";
  children: React.ReactNode;
}) {
  const router = useRouter();
  // isPlatformAdmin() reads localStorage, which the server can't see — start
  // false (matching the server-rendered HTML) and flip after mount, rather
  // than reading it directly during render, which produced a hydration
  // mismatch (server always renders false, client could render true before
  // hydration reconciles).
  const [showAdminSection, setShowAdminSection] = useState(false);
  useEffect(() => setShowAdminSection(isPlatformAdmin()), []);

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          height: 72,
          flexShrink: 0,
          background: "var(--si-surface)",
          borderBottom: "1px solid var(--si-border)",
          display: "flex",
          alignItems: "center",
          padding: "0 32px",
          gap: 24,
        }}
      >
        <div className="si-display" style={{ fontSize: 22, fontWeight: 700 }}>
          <span style={{ color: "var(--si-navy)" }}>Surf</span>
          <span style={{ color: "var(--si-blue)" }}>Intel</span>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <button
            onClick={logout}
            style={{
              height: 34,
              padding: "0 14px",
              border: "1px solid #d8dce3",
              borderRadius: 8,
              background: "#fff",
              fontSize: 13,
              fontWeight: 500,
              color: "#384152",
            }}
          >
            Uitloggen
          </button>
        </div>
      </header>

      <div style={{ flexGrow: 1, display: "flex" }}>
        <nav
          style={{
            width: 240,
            flexShrink: 0,
            background: "var(--si-surface)",
            borderRight: "1px solid var(--si-border)",
            padding: "20px 12px",
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          <NavItem href="/overview" label="Overzicht" activeItem={active === "overzicht"} />
          <NavItem href="/alerts" label="Alerts" activeItem={active === "alerts"} />
          <NavItem href="/cve" label="CVE database" activeItem={active === "cve"} />

          {showAdminSection && (
            <>
              <div style={{ height: 1, background: "#eef0f3", margin: "12px 4px" }} />
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: "#9aa3b2",
                  letterSpacing: "0.06em",
                  padding: "0 12px 4px",
                }}
              >
                BEHEER
              </div>
              <NavItem href="/sources" label="Bronnen" activeItem={active === "sources"} />
            </>
          )}
        </nav>

        <main style={{ flexGrow: 1, minWidth: 0 }}>{children}</main>
      </div>
    </div>
  );
}

function NavItem({ href, label, activeItem }: { href: string; label: string; activeItem: boolean }) {
  return (
    <Link
      href={href}
      style={{
        height: 38,
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        padding: "0 12px",
        fontSize: 14,
        fontWeight: 500,
        color: activeItem ? "var(--si-navy)" : "#384152",
        background: activeItem ? "#eaf2fb" : "transparent",
        textDecoration: "none",
      }}
    >
      {label}
    </Link>
  );
}
