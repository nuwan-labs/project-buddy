import { Star, AlertTriangle, Lightbulb, TrendingUp } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { DailySummary } from "@/types"
import { formatDate } from "@/utils/formatting"

interface DailySummaryCardProps {
  summary: DailySummary
}

interface Section {
  key:   keyof Pick<DailySummary, "highlights" | "blockers" | "suggestions" | "patterns">
  label: string
  icon:  typeof Star
  color: string
}

const SECTIONS: Section[] = [
  { key: "highlights",  label: "Highlights",   icon: Star,          color: "text-green-700" },
  { key: "blockers",    label: "Blockers",      icon: AlertTriangle, color: "text-red-700"   },
  { key: "suggestions", label: "Suggestions",   icon: Lightbulb,     color: "text-blue-700"  },
  { key: "patterns",    label: "Patterns",      icon: TrendingUp,    color: "text-purple-700" },
]

const BULLET_COLORS: Record<string, string> = {
  highlights:  "text-green-500",
  blockers:    "text-red-500",
  suggestions: "text-blue-500",
  patterns:    "text-purple-500",
}

function itemToString(item: unknown): string {
  if (typeof item === "string") return item
  if (item && typeof item === "object") {
    const o = item as Record<string, unknown>
    if (o.issue)     return `${o.issue}${o.suggestion ? ` — ${o.suggestion}` : ""}`
    if (o.next_step) return `${o.project ? `[${o.project}] ` : ""}${o.next_step}${o.rationale ? ` (${o.rationale})` : ""}`
    return Object.values(o).filter(Boolean).join(" — ")
  }
  return String(item)
}

export default function DailySummaryCard({ summary }: DailySummaryCardProps) {
  const hasAnySection = SECTIONS.some((s) => Array.isArray(summary[s.key]) && summary[s.key].length > 0)

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-gray-700">
          AI Daily Summary — {formatDate(summary.date)}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {summary.summary_text && (
          <p className="text-sm leading-relaxed text-gray-800">{summary.summary_text}</p>
        )}

        {hasAnySection && <Separator />}

        {SECTIONS.map(({ key, label, icon: Icon, color }, idx) => {
          const items = Array.isArray(summary[key]) ? summary[key] : []
          if (items.length === 0) return null
          return (
            <div key={key}>
              {idx > 0 && <Separator className="mb-4" />}
              <div className={`flex items-center gap-1.5 font-medium text-sm mb-2 ${color}`}>
                <Icon className="h-4 w-4" />
                {label}
              </div>
              <ul className="space-y-1">
                {items.map((item, i) => (
                  <li key={i} className="text-sm flex gap-2 items-start">
                    <span className={`${BULLET_COLORS[key]} mt-0.5`}>•</span>
                    <span>{itemToString(item)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
