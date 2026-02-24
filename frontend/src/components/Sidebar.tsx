import { NavLink } from "react-router-dom"
import { LayoutDashboard, CalendarDays, Clock, Settings, HelpCircle } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/",        label: "Dashboard",     icon: LayoutDashboard, end: true  },
  { to: "/plans",   label: "Plans",         icon: CalendarDays,    end: false },
  { to: "/logs",    label: "Activity Logs", icon: Clock,           end: false },
  { to: "/settings", label: "Settings",    icon: Settings,        end: false },
] as const

export default function Sidebar() {
  return (
    <aside className="w-52 shrink-0 border-r bg-white flex flex-col py-4 hidden sm:flex">
      <nav className="flex-1 px-2 space-y-0.5">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-2 border-t pt-3 mt-3">
        <a
          href="https://github.com/anthropics/claude-code/issues"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <HelpCircle className="h-4 w-4 shrink-0" />
          Help
        </a>
      </div>
    </aside>
  )
}
