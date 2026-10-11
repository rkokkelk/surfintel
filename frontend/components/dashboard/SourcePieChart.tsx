"use client";

import { PieChart } from "@mui/x-charts/PieChart";
import type { AlertDashboardSourceCount } from "@/lib/types";
import { CATEGORICAL_PALETTE, OTHER_COLOR } from "@/lib/charts";

const SIZE = 150;

export function SourcePieChart({ data }: { data: AlertDashboardSourceCount[] }) {
  const total = data.reduce((sum, d) => sum + d.count, 0) || 1;

  const slices = data.map((d, i) => ({
    ...d,
    color: d.source_name === "Overig" ? OTHER_COLOR : CATEGORICAL_PALETTE[i % CATEGORICAL_PALETTE.length],
    pct: Math.round((d.count / total) * 100),
  }));

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
      <PieChart
        series={[
          {
            data: slices.map((s) => ({ id: s.source_name, value: s.count, label: s.source_name, color: s.color })),
            innerRadius: 30,
            paddingAngle: 2,
            cornerRadius: 3,
            arcLabel: "value",
            arcLabelMinAngle: 20,
            valueFormatter: (item) => `${item.value} (${Math.round((item.value / total) * 100)}%)`,
          },
        ]}
        width={SIZE}
        height={SIZE}
        hideLegend
        sx={{
          "& .MuiPieArcLabel-root": {
            fill: "#fff",
            fontSize: 12,
            fontWeight: 600,
          },
        }}
      />

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
