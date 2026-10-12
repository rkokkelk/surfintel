import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SurfIntel",
  description: "Open cyber threat intelligence platform voor SURF-instellingen",
};

// API_URL (no NEXT_PUBLIC_ prefix) is read here on the server, per request,
// so the same built image can be deployed with a different backend URL
// without rebuilding — NEXT_PUBLIC_* vars get inlined into the client bundle
// at build time instead, which doesn't work for a prebuilt image pushed to a
// registry and reused across environments. Forcing dynamic rendering keeps
// Next.js from freezing this into a statically prerendered page at build time.
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";

  return (
    <html lang="nl">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap"
          rel="stylesheet"
        />
        <script
          dangerouslySetInnerHTML={{ __html: `window.__ENV__=${JSON.stringify({ API_URL: apiUrl })};` }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
