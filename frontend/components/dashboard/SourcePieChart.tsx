import type { AlertDashboardSourceCount } from "@/lib/types";
import { CATEGORICAL_PALETTE, OTHER_COLOR } from "@/lib/charts";

const SIZE = 220;
const R = 100;
const CX = SIZE / 2;
const CY = SIZE / 2;

function arcPoint(angle: number): [number, number] {
  return [CX + R * Math.cos(angle), CY + R * Math.sin(angle)];
}

export function SourcePieChart({ data }: { data: AlertDashboardSourceCount[] }) {
  const total = data.reduce((sum, d) => sum + d.count, 0) || 1;

  let angle = -Math.PI / 2; // start at 12 o'clock
  const slices = data.map((d, i) => {
    const fraction = d.count / total;
    const startAngle = angle;
    const endAngle = angle + fraction * Math.PI * 2;
    angle = endAngle;
    const [x1, y1] = arcPoint(startAngle);
    const [x2, y2] = arcPoint(endAngle);
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    const path = `M ${CX} ${CY} L ${x1.toFixed(2)} ${y1.toFixed(2)} A ${R} ${R} 0 ${largeArc} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z`;
    const color = d.source_name === "Overig" ? OTHER_COLOR : CATEGORICAL_PALETTE[i % CATEGORICAL_PALETTE.length];
    return { ...d, path, color, pct: Math.round(fraction * 100) };
  });

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width={SIZE} height={SIZE} role="img" aria-label="Items per bron">
        {slices.map((s) => (
          <path key={s.source_name} d={s.path} fill={s.color} stroke="var(--si-surface)" strokeWidth={2}>
            <title>
              {s.source_name}: {s.count} ({s.pct}%)
            </title>
          </path>
        ))}
      </svg>

      <div style={{ display: "flex", flexDirection: "column", gap: 10, minWidth: 0 }}>
        {slices.map((s) => (
          <div key={s.source_name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 12, height: 12, borderRadius: 3, background: s.color, flexShrink: 0 }} />
            {s.source_favicon ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`data:image/png;base64,${s.source_favicon}`} width={16} height={16} alt="" style={{ flexShrink: 0 }} />
            ) : (
              <span style={{ width: 16, flexShrink: 0 }} />
            )}
            <span style={{ fontSize: 15, color: "var(--si-text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {s.source_name}
            </span>
            <span className="si-mono" style={{ marginLeft: "auto", fontSize: 13, color: "var(--si-text-muted)", paddingLeft: 10 }}>
              {s.count} · {s.pct}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
