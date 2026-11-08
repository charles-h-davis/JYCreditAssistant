"use client";

import { useMemo } from "react";
import { formatCompact } from "@/lib/format";

export interface BarPoint {
  label: string;
  value: number;
}

/**
 * Daily net-spend bars: spending above the zero line, payments below it. Same
 * palette and typography as the line chart, so the dashboard reads as one set.
 */
export function BarChart({
  points,
  height = 190,
  ariaLabel,
}: {
  points: BarPoint[];
  height?: number;
  ariaLabel: string;
}) {
  const width = 320;
  const padding = { top: 12, right: 8, bottom: 24, left: 44 };

  const model = useMemo(() => {
    if (points.length === 0) return null;

    const values = points.map((point) => point.value);
    const rawMax = Math.max(0, ...values);
    const rawMin = Math.min(0, ...values);
    const span = rawMax - rawMin || 1;
    const pad = span * 0.12;
    const max = rawMax + pad;
    const min = rawMin - pad;

    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;
    const slot = plotWidth / points.length;
    const barWidth = Math.max(3, slot * 0.62);

    const yOf = (value: number) =>
      padding.top + plotHeight * (1 - (value - min) / (max - min || 1));
    const zeroY = yOf(0);

    const bars = points.map((point, index) => {
      const x = padding.left + slot * index + (slot - barWidth) / 2;
      const y = yOf(Math.max(point.value, 0));
      const bottom = yOf(Math.min(point.value, 0));
      return {
        key: `${point.label}-${index}`,
        x,
        y,
        height: Math.max(Math.abs(bottom - y), point.value === 0 ? 0 : 1.5),
        positive: point.value >= 0,
      };
    });

    const ticks = [max, max / 2, 0, min / 2].map((value) => ({ y: yOf(value), value }));

    return { bars, zeroY, ticks, slot, barWidth };
  }, [points, height, padding.bottom, padding.left, padding.right, padding.top]);

  if (!model) {
    return (
      <div className="grid place-items-center rounded-2xl bg-surface/60 text-sm text-muted" style={{ height }}>
        Not enough data yet
      </div>
    );
  }

  const labelEvery = Math.max(1, Math.ceil(points.length / 6));

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      role="img"
      aria-label={ariaLabel}
      className="overflow-visible"
    >
      {model.ticks.map((tick) => (
        <g key={`${tick.value}-${tick.y}`}>
          <line
            x1={padding.left}
            x2={width - padding.right}
            y1={tick.y}
            y2={tick.y}
            stroke="#dbe4f1"
            strokeWidth="1"
            strokeDasharray="2 4"
          />
          <text
            x={padding.left - 8}
            y={tick.y + 3.5}
            textAnchor="end"
            fontSize="9"
            fill="#8798ae"
          >
            {formatCompact(tick.value)}
          </text>
        </g>
      ))}

      {model.bars.map((bar) =>
        bar.height === 0 ? null : (
          <rect
            key={bar.key}
            x={bar.x}
            y={bar.positive ? bar.y : bar.y}
            width={model.barWidth}
            height={bar.height}
            rx={Math.min(3, model.barWidth / 2)}
            fill={bar.positive ? "#4c5bd4" : "#1f8f6b"}
            opacity={bar.positive ? 0.85 : 0.9}
          />
        ),
      )}

      <line
        x1={padding.left}
        x2={width - padding.right}
        y1={model.zeroY}
        y2={model.zeroY}
        stroke="#c9d5ea"
        strokeWidth="1"
      />

      {points.map((point, index) =>
        index % labelEvery === 0 || index === points.length - 1 ? (
          <text
            key={`${point.label}-${index}`}
            x={padding.left + model.slot * index + model.slot / 2}
            y={height - padding.bottom + 15}
            textAnchor="middle"
            fontSize="9"
            fill="#8798ae"
          >
            {point.label}
          </text>
        ) : null,
      )}
    </svg>
  );
}
