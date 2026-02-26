import type { ReactNode } from "react"
import Header from "@/components/Header"
import Sidebar from "@/components/Sidebar"
import ActivityPopup  from "@/components/ActivityPopup"
import DailyNotePopup from "@/components/DailyNotePopup"

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
      {/* Global popups — mounted once so they can open from any context */}
      <ActivityPopup />
      <DailyNotePopup />
    </div>
  )
}
