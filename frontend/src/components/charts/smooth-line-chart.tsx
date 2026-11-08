"use client";

import { useMemo } from "react";
import { formatCompact } from "@/lib/format";

export interface ChartPoint {
  label: string;
  value: number;
}

/**
 * Indices of the points that get an x-axis label. Shared with the callers so a
 * label (e.g. a year marker) can be attached knowing which ticks actually render.
 */
export function tickIndices(count: number): Set<number> {
  const every = Math.max(1, Math.ceil(count / 6));
  const indices = new Set<number>();
  for (let index = 0; index < count; index += 1) {
    if (index % every === 0 || index === count - 1) indices.add(index);
  }
  return indices;
}

/**
 * Smooth cumulative line chart, hand-rolled as an SVG so it matches the design
 * refs exactly (nodotted grid, indigo line, soft gradient fill, no chrome).
 *
 * The curve is a monotone cubic: tangents are clamped so the line never
 * overshoots between points, which keeps a cumulative series honest.
 */
export function SmoothLineChart({
  points,
  height = 190,
  ariaLabel,
  showAxis = true,
}: {
  points: ChartPoint[];
  height?: number;
  ariaLabel: string;
  showAxis?: boolean;
}) {
  const width = 320;
  const padding = { top: 12, right: 8, bottom: showAxis ? 24 : 8, left: 44 };

  const model = useMemo(() => {
    if (points.length === 0) return null;

    const values = points.map((point) => point.value);
    const rawMin = Math.min(...values);
    const rawMax = Math.max(...values);
    const span = rawMax - rawMin;
    // Give a flat-ish series some breathing room so the line isn't glued to an edge.
    const pad = span === 0 ? Math.max(Math.abs(rawMax) * 0.15, 1) : span * 0.12;
    // Never dip below zero for a non-negative series (balance, cumulative spend).
    const min = rawMin >= 0 ? Math.max(0, rawMin - pad) : rawMin - pad;
    const max = rawMax + pad;

    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;
    const stepX = points.length > 1 ? plotWidth / (points.length - 1) : 0;

    const coords = points.map((point, index) => ({
      x: padding.left + index * stepX,
      y: padding.top + plotHeight * (1 - (point.value - min) / (max - min || 1)),
    }));

    // Monotone cubic tangents (Fritsch–Carlson style clamping).
    const tangents = coords.map((coord, index) => {
      const previous = coords[index - 1];
      const next = coords[index + 1];
      if (!previous && !next) return 0;
      if (!previous) return (next.y - coord.y) / (next.x - coord.x);
      if (!next) return (coord.y - previous.y) / (coord.x - previous.x);
      const slope = (next.y - previous.y) / (next.x - previous.x);
      const before = (coord.y - previous.y) / (coord.x - previous.x);
      const after = (next.y - coord.y) / (next.x - coord.x);
      return before * after <= 0 ? 0 : (before + after) / 2 || slope;
    });

    let path = `M ${coords[0].x} ${coords[0].y}`;
    for (let index = 0; index < coords.length - 1; index += 1) {
      const current = coords[index];
      const next = coords[index + 1];
      const dx = (next.x - current.x) / 3;
      path += ` C ${current.x + dx} ${current.y + tangents[index] * dx}, ${
        next.x - dx
      } ${next.y - tangents[index + 1] * dx}, ${next.x} ${next.y}`;
    }

    const last = coords[coords.length - 1];
    const first = coords[0];
    const area = `${path} L ${last.x} ${padding.top + plotHeight} L ${first.x} ${
      padding.top + plotHeight
    } Z`;

    const ticks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
      y: padding.top + plotHeight * ratio,
      value: max - (max - min) * ratio,
    }));

    return { coords, path, area, ticks, min, max, plotWidth, plotHeight };
  }, [points, height, padding.bottom, padding.left, padding.right, padding.top]);

  if (!model) {
    return (
      <div className="grid place-items-center rounded-2xl bg-surface/60 text-sm text-muted" style={{ height }}>
        Not enough data yet
      </div>
    );
  }

  const baseline = padding.top + model.plotHeight;
  const labelled = tickIndices(points.length);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      role="img"
      aria-label={ariaLabel}
      className="overflow-visible"
    >
      <defs>
        <linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.22" />
          <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0" />
        </linearGradient>
      </defs>

      {model.ticks.map((tick) => (
        <g key={tick.y}>
          <line
            x1={padding.left}
            x2={width - padding.right}
            y1={tick.y}
            y2={tick.y}
            stroke="var(--color-grid)"
            strokeWidth="1"
            strokeDasharray="2 4"
          />
          <text
            x={padding.left - 8}
            y={tick.y + 3.5}
            textAnchor="end"
            fontSize="9"
            fill="var(--color-chart-label)"
          >
            {formatCompact(tick.value)}
          </text>
        </g>
      ))}

      <path d={model.area} fill="url(#chart-fill)" />
      <path
        d={model.path}
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <circle
        cx={model.coords[model.coords.length - 1].x}
        cy={model.coords[model.coords.length - 1].y}
        r="3.4"
        fill="var(--color-accent)"
        stroke="var(--color-elevated)"
        strokeWidth="2"
      />

      {showAxis
        ? points.map((point, index) =>
            labelled.has(index) ? (
              <text
                key={`${point.label}-${index}`}
                x={model.coords[index].x}
                y={baseline + 15}
                textAnchor="middle"
                fontSize="9"
                fill="var(--color-chart-label)"
              >
                {point.label}
              </text>
            ) : null,
          )
        : null}
    </svg>
  );
}
