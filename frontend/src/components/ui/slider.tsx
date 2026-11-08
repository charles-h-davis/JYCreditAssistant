"use client";

/**
 * Range input styled to match the "Adjust monthly repayments" control in the
 * design refs: track on the surface colour, oversized thumb, value labels under
 * each end. Native input keeps keyboard and screen-reader behaviour for free.
 */
export function RangeSlider({
  min,
  max,
  step = 1,
  value,
  onChange,
  label,
  minLabel,
  maxLabel,
  disabled = false,
}: {
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (value: number) => void;
  label: string;
  minLabel: string;
  maxLabel: string;
  disabled?: boolean;
}) {
  return (
    <div className="w-full">
      <input
        type="range"
        className="range"
        aria-label={label}
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <div className="mt-2 flex justify-between text-xs text-muted">
        <span>{minLabel}</span>
        <span>{maxLabel}</span>
      </div>
    </div>
  );
}
