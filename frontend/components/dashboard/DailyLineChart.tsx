import type { AlertDashboardDayCount } from "@/lib/types";

const WIDTH = 760;
const HEIGHT = 150;
const PAD_LEFT = 36;
const PAD_RIGHT = 56;
const PAD_TOP = 16;
const PAD_BOTTOM = 28;

function formatDay(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("nl-NL", { day: "numeric", month: "short" });
}

export function DailyLineChart({ data }: { data: AlertDashboardDayCount[] }) {
  const plotW = WIDTH - PAD_LEFT - PAD_RIGHT;
  const plotH = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const maxCount = Math.max(1, ...data.map((d) => d.count));
  // Round the axis ceiling up to a clean number (skill: "Y-axis ticks: round
  // to clean numbers") rather than plotting straight to the raw max.
  const niceMax = Math.max(4, Math.ceil(maxCount / 4) * 4);

  const x = (i: number) => PAD_LEFT + (data.length <= 1 ? 0 : (i / (data.length - 1)) * plotW);
  const y = (v: number) => PAD_TOP + plotH - (v / niceMax) * plotH;

  const linePath = data.map((d, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(d.count).toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L ${x(data.length - 1).toFixed(1)} ${y(0).toFixed(1)} L ${x(0).toFixed(1)} ${y(0).toFixed(1)} Z`;

  const gridTicks = [0, niceMax / 2, niceMax];
  const last = data[data.length - 1];

  // Thin out x-axis date labels so they never crowd — show every 2nd/3rd
  // depending on point count, always including the first and last.
  const labelEvery = data.length > 10 ? 3 : data.length > 6 ? 2 : 1;

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} width="100%" role="img" aria-label="Items per dag">
      {gridTicks.map((t) => (
        <g key={t}>
          <line
            x1={PAD_LEFT}
            x2={WIDTH - PAD_RIGHT}
            y1={y(t)}
            y2={y(t)}
            stroke="var(--si-border)"
            strokeWidth={1}
          />
          <text x={PAD_LEFT - 8} y={y(t) + 4} textAnchor="end" fontSize={12} fill="var(--si-text-muted)">
            {t}
          </text>
        </g>
      ))}

      <path d={areaPath} fill="var(--si-blue)" opacity={0.1} stroke="none" />
      <path d={linePath} fill="none" stroke="var(--si-blue)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

      {data.map((d, i) => (
        <g key={d.date}>
          <circle cx={x(i)} cy={y(d.count)} r={i === data.length - 1 ? 5 : 3} fill="var(--si-blue)" stroke="var(--si-surface)" strokeWidth={2} />
          <title>
            {formatDay(d.date)}: {d.count}
          </title>
          {i % labelEvery === 0 && (
            <text x={x(i)} y={HEIGHT - 6} textAnchor="middle" fontSize={11} fill="var(--si-text-muted)">
              {formatDay(d.date)}
            </text>
          )}
        </g>
      ))}

      {last && (
        <text
          x={x(data.length - 1) + 10}
          y={y(last.count) + 4}
          textAnchor="start"
          fontSize={14}
          fontWeight={700}
          fill="var(--si-text)"
        >
          {last.count}
        </text>
      )}
    </svg>
  );
}
