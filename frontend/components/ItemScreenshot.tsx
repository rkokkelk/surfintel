"use client";

import { useEffect, useState } from "react";
import { imgFetch } from "@/lib/api";

export function ItemScreenshot({ itemId, width, height }: { itemId: string; width: number; height: number }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    setSrc(null);
    setFailed(false);

    imgFetch<Blob>(`/items/${itemId}/screenshot`)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [itemId]);

  return (
    <div
      style={{
        width,
        height,
        flexShrink: 0,
        borderRadius: 8,
        overflow: "hidden",
        background: "var(--si-bg)",
        border: "1px solid var(--si-border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element -- object URL from an authenticated blob fetch, not a static/optimizable asset
        <img src={src} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <span style={{ fontSize: 11, color: "var(--si-text-muted)" }}>
          {failed ? "Geen screenshot" : "Laden…"}
        </span>
      )}
    </div>
  );
}
