"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";
import { isPlatformAdmin } from "@/lib/auth";
import { ApiInfoModal } from "@/components/ApiInfoModal";
import { ThemeToggle } from "@/components/ThemeToggle";

// Icons
import { GrVulnerability } from "react-icons/gr";
import { GrOverview } from "react-icons/gr";
import { GrResources } from "react-icons/gr";
import { AiFillAlert } from "react-icons/ai";
import { FiMenu } from "react-icons/fi";
import { FiX } from "react-icons/fi";


export function Shell({
  active,
  children,
}: {
  active: "overzicht" | "alerts" | "cve" | "sources";
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [showAdminSection, setShowAdminSection] = useState(false);
  useEffect(() => setShowAdminSection(isPlatformAdmin()), []);
  const [showApiInfo, setShowApiInfo] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  function logout() {
    clearToken();
    router.push("/login");
  }

  function toggleMobileMenu() {
    setMobileMenuOpen(!mobileMenuOpen);
  }

  function closeMobileMenu() {
    setMobileMenuOpen(false);
  }

  // Mobile header component
  const MobileHeader = () => (
    <>
      <div
        style={{
          height: 72,
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          gap: 12,
          position: "relative",
          zIndex: 101,
        }}
      >
        <button
          onClick={toggleMobileMenu}
          style={{
            border: "none",
            background: "none",
            color: "var(--si-text)",
            fontSize: 24,
            cursor: "pointer",
            padding: "8px",
            display: "flex",
            alignItems: "center",
          }}
        >
          {mobileMenuOpen ? <FiX /> : <FiMenu />}
        </button>
        
        <div className="si-display" style={{ fontSize: 20, fontWeight: 700, flex: 1 }}>
          <span style={{ color: "var(--si-navy)" }}>Surf</span>
          <span style={{ color: "var(--si-blue)" }}>Intel</span>
        </div>
        
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <ThemeToggle />
          <button
            onClick={() => setShowApiInfo(true)}
            style={{
              height: 40,
              width: 40,
              padding: "0",
              border: "1px solid var(--si-border)",
              borderRadius: 8,
              background: "var(--si-surface)",
              fontSize: 12,
              fontWeight: 500,
              color: "var(--si-text-secondary)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            API
          </button>
          <button
            onClick={logout}
            style={{
              height: 40,
              width: 40,
              padding: "0",
              border: "1px solid var(--si-border)",
              borderRadius: 8,
              background: "var(--si-surface)",
              fontSize: 12,
              fontWeight: 500,
              color: "var(--si-text-secondary)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            Uit
          </button>
        </div>
      </div>
      
      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div
          style={{
            position: "fixed",
            top: 72,
            left: 0,
            right: 0,
            bottom: 0,
            background: "var(--si-surface)",
            borderTop: "1px solid var(--si-border)",
            padding: "16px",
            overflowY: "auto",
            zIndex: 100,
          }}
        >
          <nav style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
            <MobileNavItem href="/overview" label="Overzicht" activeItem={active === "overzicht"} onClick={closeMobileMenu} icon={<GrOverview />} />
            <MobileNavItem href="/alerts" label="Alerts" activeItem={active === "alerts"} onClick={closeMobileMenu} icon={<AiFillAlert />} />
            <MobileNavItem href="/cve" label="CVE database" activeItem={active === "cve"} onClick={closeMobileMenu} icon={<GrVulnerability />} />
            
            {showAdminSection && (
              <>
                <div style={{ height: 1, background: "var(--si-border)", margin: "8px 0" }} />
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: "var(--si-text-muted)",
                    letterSpacing: "0.06em",
                    padding: "0 0 4px",
                  }}
                >
                  BEHEER
                </div>
                <MobileNavItem href="/sources" label="Bronnen" activeItem={active === "sources"} onClick={closeMobileMenu} icon={<GrResources />} />
              </>
            )}
          </nav>
        </div>
      )}
      
      {showApiInfo && <ApiInfoModal onClose={() => setShowApiInfo(false)} />}
    </>
  );

  // Desktop header with sidebar
  const DesktopLayout = ({ children }: { children: React.ReactNode }) => (
    <>
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
        <div style={{ marginLeft: "auto", display: "flex", gap: 10, alignItems: "center" }}>
          <ThemeToggle />
          <button
            onClick={() => setShowApiInfo(true)}
            style={{
              height: 34,
              padding: "0 14px",
              border: "1px solid var(--si-border)",
              borderRadius: 8,
              background: "var(--si-surface)",
              fontSize: 13,
              fontWeight: 500,
              color: "var(--si-text-secondary)",
            }}
          >
            API
          </button>
          <button
            onClick={logout}
            style={{
              height: 34,
              padding: "0 14px",
              border: "1px solid var(--si-border)",
              borderRadius: 8,
              background: "var(--si-surface)",
              fontSize: 13,
              fontWeight: 500,
              color: "var(--si-text-secondary)",
            }}
          >
            Uitloggen
          </button>
        </div>
      </header>

      {showApiInfo && <ApiInfoModal onClose={() => setShowApiInfo(false)} />}

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
          <NavItem href="/overview" label="Overzicht" activeItem={active === "overzicht"} icon={<GrOverview />} />
          <NavItem href="/alerts" label="Alerts" activeItem={active === "alerts"} icon={<AiFillAlert />} />
          <NavItem href="/cve" label="CVE database" activeItem={active === "cve"} icon={<GrVulnerability />} />

          {showAdminSection && (
            <>
              <div style={{ height: 1, background: "var(--si-border)", margin: "12px 4px" }} />
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: "var(--si-text-muted)",
                  letterSpacing: "0.06em",
                  padding: "0 12px 4px",
                }}
              >
                BEHEER
              </div>
              <NavItem href="/sources" label="Bronnen" activeItem={active === "sources"} icon={<GrResources />} />
            </>
          )}
        </nav>

        <main style={{ flexGrow: 1, minWidth: 0, overflowY: "auto" }}>{children}</main>
      </div>
    </>
  );

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <div className="mobile-only">
        <MobileHeader />
      </div>
      <div className="desktop-only">
        <DesktopLayout children={children} />
      </div>
      
      {/* On mobile, when menu is open, we need to prevent background scrolling */}
      {mobileMenuOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            zIndex: 99,
          }}
          onClick={closeMobileMenu}
        />
      )}
    </div>
  );
}

function NavItem({ href, label, activeItem, icon }: { href: string; label: string; activeItem: boolean; icon?: React.ReactNode }) {
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
        color: activeItem ? "var(--si-navy)" : "var(--si-text-secondary)",
        background: activeItem ? "var(--si-blue-bg)" : "transparent",
        textDecoration: "none",
        gap: 8,
      }}
    >
      {icon && <span style={{ display: "flex", alignItems: "center" }}>{icon}</span>}
      {label}
    </Link>
  );
}

function MobileNavItem({ href, label, activeItem, onClick, icon }: { href: string; label: string; activeItem: boolean; onClick: () => void; icon?: React.ReactNode }) {
  return (
    <Link
      href={href}
      onClick={onClick}
      style={{
        height: 48,
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        padding: "0 16px",
        fontSize: 16,
        fontWeight: 500,
        color: activeItem ? "var(--si-navy)" : "var(--si-text)",
        background: activeItem ? "var(--si-blue-bg)" : "transparent",
        textDecoration: "none",
        gap: 12,
      }}
    >
      {icon && <span style={{ display: "flex", alignItems: "center", fontSize: 20 }}>{icon}</span>}
      {label}
    </Link>
  );
}
