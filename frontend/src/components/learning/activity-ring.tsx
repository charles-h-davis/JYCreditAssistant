"use client";

/** Segmented progress ring: one arc per lesson, filled as each is completed. */
export function ActivityRing({
  completed,
  total = 3,
  size = 92,
}: {
  completed: number;
  total?: number;
  size?: number;
}) {
  const stroke = 9;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const gap = 9;
  const segment = circumference / total - gap;

  return (
    <svg width={size} height={size} aria-hidden className="-rotate-90">
      {Array.from({ length: total }).map((_, index) => {
        const filled = index < completed;
        return (
          <circle
            key={index}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={filled ? "#33445c" : "#d7e0ee"}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${segment} ${circumference - segment}`}
            strokeDashoffset={-(index * (circumference / total) + gap / 2)}
          />
        );
      })}
    </svg>
  );
}
