import { cn } from "@/lib/utils"

type Variant = "blue" | "green" | "red" | "yellow"

interface ProgressBarProps {
  value: number          // 0–100
  label?: string
  variant?: Variant
  showPercent?: boolean
  className?: string
}

const TRACK_COLORS: Record<Variant, string> = {
  blue:   "bg-blue-500",
  green:  "bg-green-500",
  red:    "bg-red-500",
  yellow: "bg-yellow-400",
}

export default function ProgressBar({
  value,
  label,
  variant = "blue",
  showPercent = true,
  className,
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, Math.round(value)))

  return (
    <div className={cn("w-full", className)}>
      {(label !== undefined || showPercent) && (
        <div className="flex items-center justify-between mb-1">
          {label !== undefined && (
            <span className="text-xs text-muted-foreground">{label}</span>
          )}
          {showPercent && (
            <span className="text-xs font-medium text-muted-foreground ml-auto">{clamped}%</span>
          )}
        </div>
      )}
      <div className="h-2 rounded-full bg-secondary overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-300 ease-in-out", TRACK_COLORS[variant])}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
