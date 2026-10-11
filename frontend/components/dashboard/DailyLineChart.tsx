"use client";

import { LineChart } from "@mui/x-charts/LineChart";
import type { AlertDashboardDayCount } from "@/lib/types";

function formatDay(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("nl-NL", { day: "numeric", month: "short" });
}

export function DailyLineChart({ data }: { data: AlertDashboardDayCount[] }) {
  const labels = data.map((d) => formatDay(d.date));
  const counts = data.map((d) => d.count);
  const maxCount = Math.max(1, ...counts);
  // Round the axis ceiling up to a clean number rather than plotting
  // straight to the raw max.
  const niceMax = Math.max(4, Math.ceil(maxCount / 4) * 4);

  return (
    <LineChart
      height={170}
      xAxis={[
        {
          data: labels,
          scaleType: "point",
          tickLabelStyle: { fontSize: 11, fill: "var(--si-text-muted)" },
        },
      ]}
      yAxis={[{ min: 0, max: niceMax, tickLabelStyle: { fontSize: 12, fill: "var(--si-text-muted)" } }]}
      series={[
        {
          data: counts,
          label: "Items per dag",
          color: "var(--si-blue)",
          area: true,
          showMark: true,
          valueFormatter: (value) => `${value ?? 0}`,
        },
      ]}
      grid={{ horizontal: true }}
      hideLegend
      margin={{ left: 0, right: 0, top: 0, bottom: 0 }}
    />
  );
}
