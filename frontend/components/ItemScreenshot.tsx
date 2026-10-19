"use client";

import { useEffect, useState, useRef } from "react";
import { imgFetch } from "@/lib/api";

// Global cache for screenshots to prevent re-fetching
const screenshotCache = new Map<string, string>();

export function ItemScreenshot({
  itemId,
  width,
  height,
}: {
  itemId: string;
  width: number | string;
  height: number;
}) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  useEffect(() => {
    let cancelled = false;
    
    // Check if we already have this screenshot in cache
    if (screenshotCache.has(itemId)) {
      setSrc(screenshotCache.get(itemId)!);
      setFailed(false);
      return;
    }

    // Clear previous object URL if exists
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }

    setSrc(null);
    setFailed(false);
    setIsLoading(true);
    setOpen(false);

    imgFetch<Blob>(`/items/${itemId}/screenshot`)
      .then((blob) => {
        if (cancelled) return;
        const objectUrl = URL.createObjectURL(blob);
        objectUrlRef.current = objectUrl;
        // Cache the object URL
        screenshotCache.set(itemId, objectUrl);
        setSrc(objectUrl);
        setIsLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          setFailed(true);
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
      // Don't revoke the object URL here if it's cached, as other instances might be using it
      if (objectUrlRef.current && !screenshotCache.has(itemId)) {
        URL.revokeObjectURL(objectUrlRef.current);
      }
    };
  }, [itemId]);

  return (
    <>
      <div
        onClick={
          src
            ? (e) => {
                e.stopPropagation();
                setOpen(true);
              }
            : undefined
        }
        role={src ? "button" : undefined}
        tabIndex={src ? 0 : undefined}
        onKeyDown={src ? (e) => e.key === "Enter" && (e.stopPropagation(), setOpen(true)) : undefined}
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
          cursor: src ? "zoom-in" : "default",
        }}
      >
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element -- object URL from an authenticated blob fetch, not a static/optimizable asset
          <img src={src} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <span style={{ fontSize: 11, color: "var(--si-text-muted)" }}>
            {isLoading ? "Laden…" : failed ? "Geen screenshot" : "Laden…"}
          </span>
        )}
      </div>

      {open && src && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 200,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 32,
          }}
        >
          <div
            onClick={(e) => {
              e.stopPropagation();
              setOpen(false);
            }}
            style={{ position: "absolute", inset: 0, background: "rgba(15, 23, 42, 0.75)" }}
            aria-hidden
          />
          <button
            type="button"
            aria-label="Sluiten"
            onClick={(e) => {
              e.stopPropagation();
              setOpen(false);
            }}
            style={{
              position: "absolute",
              top: 20,
              right: 24,
              width: 36,
              height: 36,
              border: "none",
              borderRadius: 8,
              background: "rgba(255, 255, 255, 0.12)",
              color: "#fff",
              fontSize: 18,
              cursor: "pointer",
              zIndex: 1,
            }}
          >
            ×
          </button>
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: "relative",
              maxWidth: "calc(100vw - 64px)",
              maxHeight: "calc(100vh - 64px)",
              overflow: "auto",
              borderRadius: 4,
              boxShadow: "0 12px 40px rgba(0, 0, 0, 0.4)",
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- same object URL as the thumbnail, just shown full-size */}
            <img
              src={src}
              alt=""
              style={{
                display: "block",
                // Never upscaled, but a screenshot taller than the viewport
                // (full_page captures can run to thousands of px) keeps its
                // natural height and scrolls within the box above instead of
                // being squeezed down to illegibility by objectFit: contain.
                maxWidth: "100%",
                height: "auto",
              }}
            />
          </div>
        </div>
      )}
    </>
  );
}
