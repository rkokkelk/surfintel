"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "si-theme";

function applyTheme(theme: "light" | "dark") {
  if (theme === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

export function ThemeToggle() {
  // Dark is the default (see app/layout.tsx's inline script, which already
  // applied any stored "light" choice before this mounts) — start in sync
  // with that rather than re-deriving it, to avoid a mount-time flicker.
  const [theme, setTheme] = useState<"light" | "dark">("dark");

  useEffect(() => {
    setTheme(document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark");
  }, []);

  function toggle() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    applyTheme(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* private browsing / blocked storage — theme just won't persist */
    }
  }

  return (
    <button
      onClick={toggle}
      aria-label={theme === "dark" ? "Schakel naar lichte modus" : "Schakel naar donkere modus"}
      title={theme === "dark" ? "Lichte modus" : "Donkere modus"}
      style={{
        height: 34,
        width: 34,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: "1px solid var(--si-border)",
        borderRadius: 8,
        background: "var(--si-surface)",
        color: "var(--si-text-secondary)",
        fontSize: 15,
      }}
    >
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}
