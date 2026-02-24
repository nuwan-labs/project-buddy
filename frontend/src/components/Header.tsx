import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { Settings, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useApp } from "@/context/AppContext"
import { formatDate } from "@/utils/formatting"

export default function Header() {
  const { state } = useApp()
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const plan = state.activePlan

  return (
    <header className="sticky top-0 z-30 border-b bg-white shadow-sm">
      <div className="flex items-center justify-between px-6 h-14">
        {/* Left: logo + active plan */}
        <div className="flex items-center gap-4 min-w-0">
          <Link to="/" className="text-lg font-bold text-blue-600 shrink-0">
            Project Buddy
          </Link>
          {plan && (
            <span className="text-sm text-muted-foreground truncate hidden sm:block">
              {plan.name}
              <span className="mx-1 text-gray-300">|</span>
              {formatDate(plan.start_date)} – {formatDate(plan.end_date)}
            </span>
          )}
        </div>

        {/* Right: clock + settings */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span className="tabular-nums">
              {time.toLocaleTimeString("en-LK", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          </div>
          <Button variant="ghost" size="icon" asChild>
            <Link to="/settings" aria-label="Settings">
              <Settings className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  )
}
