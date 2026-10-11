import React from "react";
import { cn } from "@/lib/utils";
import { Info } from "lucide-react";

/**
 * TwoLeavesIcon - Exact botanical two-leaf sprout matching the reference design.
 * Features two symmetrical pointed leaves spreading outwards with central veins
 * and a small root/stem at the base.
 */
function TwoLeavesIcon({ className = "size-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      {/* Left Leaf */}
      <path
        d="M12 14.2C11.3 9.8 7.2 6.8 3.8 7.4C4.2 11.8 7.6 15 12 14.2Z"
        fill="currentColor"
      />
      {/* Left Leaf subtle center vein */}
      <path
        d="M5.4 8.6C7.3 10.3 9.3 12 11.2 13.5"
        stroke="white"
        strokeWidth="0.85"
        strokeLinecap="round"
        opacity="0.75"
      />
      {/* Right Leaf */}
      <path
        d="M12 14.2C12.7 9.8 16.8 6.8 20.2 7.4C19.8 11.8 16.4 15 12 14.2Z"
        fill="currentColor"
      />
      {/* Right Leaf subtle center vein */}
      <path
        d="M18.6 8.6C16.7 10.3 14.7 12 12.8 13.5"
        stroke="white"
        strokeWidth="0.85"
        strokeLinecap="round"
        opacity="0.75"
      />
      {/* Center Stem */}
      <path
        d="M12 13.2V18.2"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function HealthRing({
  value,
  size = 124,
  label,
  conditionText = "Good Condition",
  subtext = "Based on latest leaf scan",
}: {
  value: number;
  size?: number;
  label?: string;
  conditionText?: string;
  subtext?: string;
}) {
  const gradId = React.useId();
  const clamped = Math.max(0, Math.min(100, value));
  const r = 43;
  const c = 2 * Math.PI * r;
  const offset = c - (clamped / 100) * c;

  const isGood = clamped >= 80;
  const isWarning = clamped >= 60 && clamped < 80;

  const numColor = isGood
    ? "text-[#003816]"
    : isWarning
      ? "text-amber-950"
      : "text-rose-950";

  const leafColor = isGood
    ? "text-[#007a33]"
    : isWarning
      ? "text-amber-600"
      : "text-rose-600";

  const badgeStyles = isGood
    ? "bg-[#dcfce7] text-[#005a24] border border-[#bbf7d0]/70"
    : isWarning
      ? "bg-amber-100 text-amber-900 border border-amber-200"
      : "bg-rose-100 text-rose-900 border border-rose-200";

  const dropShadowFilter = isGood
    ? "drop-shadow(0 2px 8px rgba(34, 197, 94, 0.28))"
    : isWarning
      ? "drop-shadow(0 2px 8px rgba(245, 158, 11, 0.28))"
      : "drop-shadow(0 2px 8px rgba(244, 63, 94, 0.28))";

  return (
    <div className="flex flex-col items-center shrink-0">
      <div className="relative grid place-items-center" style={{ width: size, height: size }}>
        <svg viewBox="0 0 104 104" className="size-full">
          <defs>
            {/* Smooth lush green gradient matching the reference: deep forest on bottom-left to bright vibrant grass green on top-right */}
            <linearGradient id={`${gradId}-good`} x1="30%" y1="0%" x2="70%" y2="100%">
              <stop offset="0%" stopColor="#006b2b" />
              <stop offset="40%" stopColor="#0a8f3c" />
              <stop offset="70%" stopColor="#16a34a" />
              <stop offset="100%" stopColor="#22c55e" />
            </linearGradient>
            <linearGradient id={`${gradId}-warn`} x1="30%" y1="0%" x2="70%" y2="100%">
              <stop offset="0%" stopColor="#b45309" />
              <stop offset="100%" stopColor="#fbbf24" />
            </linearGradient>
            <linearGradient id={`${gradId}-danger`} x1="30%" y1="0%" x2="70%" y2="100%">
              <stop offset="0%" stopColor="#be123c" />
              <stop offset="100%" stopColor="#fb7185" />
            </linearGradient>
          </defs>

          {/* Background track */}
          <circle
            cx="52"
            cy="52"
            r={r}
            className="stroke-[#ebf2ed]"
            strokeWidth={8.5}
            fill="none"
          />

          {/* Progress stroke with smooth gradient and soft glow */}
          <circle
            cx="52"
            cy="52"
            r={r}
            strokeWidth={8.5}
            fill="none"
            strokeLinecap="round"
            stroke={`url(#${gradId}-${isGood ? "good" : isWarning ? "warn" : "danger"})`}
            strokeDasharray={c}
            strokeDashoffset={offset}
            transform="rotate(-90 52 52)"
            className="transition-[stroke-dashoffset] duration-1000 ease-out"
            style={{
              filter: dropShadowFilter,
            }}
          />
        </svg>

        {/* Center content: Two Leaves Icon + Big Bold Score + / 100 */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <TwoLeavesIcon className={cn("size-5 mb-0.5", leafColor)} />
          <div className={cn("text-3xl font-black tracking-tight leading-none", numColor)}>
            {clamped}
          </div>
          <div className="text-[11px] font-semibold text-[#475569] mt-0.5">/ 100</div>
          {label && (
            <div className="text-[9px] font-bold text-stone-400 uppercase tracking-widest mt-0.5">
              {label}
            </div>
          )}
        </div>
      </div>

      {conditionText && (
        <span className={cn("px-3.5 py-1 rounded-full text-xs font-extrabold mt-2 shadow-2xs", badgeStyles)}>
          {conditionText}
        </span>
      )}

      {subtext && (
        <p className="text-[10px] text-[#475569] font-medium mt-1.5 flex items-center justify-center gap-1 text-center">
          <span>{subtext}</span>
          <Info className="size-3 text-[#475569] shrink-0" />
        </p>
      )}
    </div>
  );
}
