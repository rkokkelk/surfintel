"use client";

import { useState } from "react";
import type { CvssAxis } from "@/lib/cvss";

interface Tooltip {
  x: number;
  y: number;
  label: string;
  value: string;
}

export function CvssRadarChart({ axes, color, size = 260 }: { axes: CvssAxis[]; color: string; size?: number }) {
  const [tooltip, setTooltip] = useState<Tooltip | null>(null);

  const n = axes.length;
  const cx = size / 2;
  const cy = size / 2;
  const labelPad = 26;
  const maxR = size / 2 - labelPad;

  const angleFor = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / n;
  const pointFor = (i: number, r: number) => {
    const a = angleFor(i);
    return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
  };

  const rings = [0.25, 0.5, 0.75, 1];
  const ringPolygon = (frac: number) =>
    Array.from({ length: n }, (_, i) => pointFor(i, maxR * frac))
      .map((p) => `${p.x},${p.y}`)
      .join(" ");

  const dataPolygon = axes.map((a, i) => pointFor(i, maxR * a.score)).map((p) => `${p.x},${p.y}`).join(" ");

  if (n === 0) return null;

  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} role="img" aria-label="CVSS-vector radardiagram">
        {rings.map((frac) => (
          <polygon key={frac} points={ringPolygon(frac)} fill="none" stroke="var(--si-border)" strokeWidth={1} />
        ))}
        {axes.map((_, i) => {
          const p = pointFor(i, maxR);
          return <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="var(--si-border)" strokeWidth={1} />;
        })}

        <polygon points={dataPolygon} fill={color} fillOpacity={0.15} stroke={color} strokeWidth={2} strokeLinejoin="round" />

        {axes.map((a, i) => {
          const p = pointFor(i, maxR * a.score);
          return (
            <circle
              key={a.key}
              cx={p.x}
              cy={p.y}
              r={5}
              fill={color}
              stroke="var(--si-surface)"
              strokeWidth={2}
              style={{ cursor: "default" }}
              tabIndex={0}
              onMouseMove={(e) =>
                setTooltip({ x: e.clientX, y: e.clientY, label: a.label, value: `${a.value} — ${a.valueLabel}` })
              }
              onFocus={() => setTooltip({ x: p.x, y: p.y, label: a.label, value: `${a.value} — ${a.valueLabel}` })}
              onMouseLeave={() => setTooltip(null)}
            />
          );
        })}

        {axes.map((a, i) => {
          const p = pointFor(i, maxR + 14);
          return (
            <text
              key={a.key}
              x={p.x}
              y={p.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={11}
              fontWeight={600}
              fill="var(--si-text-secondary)"
            >
              {a.key}
            </text>
          );
        })}
      </svg>

      {tooltip && (
        <div
          style={{
            position: "fixed",
            left: tooltip.x + 12,
            top: tooltip.y + 12,
            zIndex: 60,
            background: "var(--si-text)",
            color: "#fff",
            borderRadius: 8,
            padding: "6px 10px",
            fontSize: 12,
            pointerEvents: "none",
            boxShadow: "0 4px 12px rgba(15,23,42,0.25)",
          }}
        >
          <strong>{tooltip.label}</strong>: {tooltip.value}
        </div>
      )}
    </div>
  );
}
