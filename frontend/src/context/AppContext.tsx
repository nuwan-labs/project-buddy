import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useCallback,
  type ReactNode,
} from "react"
import type { BiweeklyPlan, Project, DailySummary, WebSocketMessage } from "@/types"
import { dashboardApi } from "@/services/api"
import { getWsClient } from "@/services/websocket"
import { registerServiceWorker, showSwNotification, onActivityPopup } from "@/services/serviceWorker"
import { WS_URL } from "@/utils/constants"

// ─── State shape ──────────────────────────────────────────────────────────────

interface AppState {
  activePlan:           BiweeklyPlan | null
  projects:             Project[]
  dailySummary:         DailySummary | null
  showActivityPopup:    boolean
  preselectedProjectId: number | null
  dashboardLoading:     boolean
  dashboardError:       string | null
  snoozedUntil:         number | null
}

const initialState: AppState = {
  activePlan:           null,
  projects:             [],
  dailySummary:         null,
  showActivityPopup:    false,
  preselectedProjectId: null,
  dashboardLoading:     false,
  dashboardError:       null,
  snoozedUntil:         null,
}

// ─── Actions ──────────────────────────────────────────────────────────────────

type Action =
  | { type: "SET_DASHBOARD_LOADING" }
  | { type: "SET_DASHBOARD_ERROR"; payload: string }
  | { type: "SET_DASHBOARD"; payload: { plan: BiweeklyPlan | null; projects: Project[]; summary: DailySummary | null } }
  | { type: "SHOW_POPUP";    payload?: number }   // optional pre-selected project id
  | { type: "HIDE_POPUP" }
  | { type: "SNOOZE_POPUP"; payload: number }
  | { type: "SET_SUMMARY";   payload: DailySummary }

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "SET_DASHBOARD_LOADING":
      return { ...state, dashboardLoading: true, dashboardError: null }

    case "SET_DASHBOARD_ERROR":
      return { ...state, dashboardLoading: false, dashboardError: action.payload }

    case "SET_DASHBOARD":
      return {
        ...state,
        dashboardLoading: false,
        dashboardError:   null,
        activePlan:       action.payload.plan,
        projects:         action.payload.projects,
        dailySummary:     action.payload.summary,
      }

    case "SHOW_POPUP": {
      const now = Date.now()
      if (state.snoozedUntil && now < state.snoozedUntil) return state
      return {
        ...state,
        showActivityPopup:    true,
        preselectedProjectId: action.payload ?? null,
      }
    }

    case "HIDE_POPUP":
      return { ...state, showActivityPopup: false, preselectedProjectId: null }

    case "SNOOZE_POPUP":
      return { ...state, showActivityPopup: false, snoozedUntil: action.payload }

    case "SET_SUMMARY":
      return { ...state, dailySummary: action.payload }

    default:
      return state
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────

interface AppContextValue {
  state:              AppState
  dispatch:           React.Dispatch<Action>
  refreshDashboard:   () => Promise<void>
  openActivityPopup:  (projectId?: number) => void
  closeActivityPopup: () => void
  snoozePopup:        (minutes: number) => void
}

const AppContext = createContext<AppContextValue | null>(null)

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error("useApp must be used inside AppProvider")
  return ctx
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const refreshDashboard = useCallback(async () => {
    dispatch({ type: "SET_DASHBOARD_LOADING" })
    try {
      const { data: res } = await dashboardApi.get()
      dispatch({
        type:    "SET_DASHBOARD",
        payload: {
          plan:     res.data.active_plan,
          projects: res.data.projects,
          summary:  res.data.daily_summary,
        },
      })
    } catch {
      dispatch({ type: "SET_DASHBOARD_ERROR", payload: "Failed to load dashboard." })
    }
  }, [])

  const openActivityPopup = useCallback(
    (projectId?: number) => dispatch({ type: "SHOW_POPUP", payload: projectId }),
    []
  )
  const closeActivityPopup = useCallback(() => dispatch({ type: "HIDE_POPUP" }), [])
  const snoozePopup = useCallback((minutes: number) => {
    dispatch({ type: "SNOOZE_POPUP", payload: Date.now() + minutes * 60 * 1000 })
    setTimeout(() => dispatch({ type: "SHOW_POPUP" }), minutes * 60 * 1000)
  }, [])

  // Initial dashboard load
  useEffect(() => { void refreshDashboard() }, [refreshDashboard])

  // WebSocket listener
  useEffect(() => {
    const ws = getWsClient(WS_URL)
    ws.connect()

    const unsub = ws.onMessage((msg: WebSocketMessage) => {
      if (msg.type === "notification" && msg.action === "SHOW_ACTIVITY_POPUP") {
        void showSwNotification(msg.message ?? "What are you working on right now?")
        dispatch({ type: "SHOW_POPUP" })
      }
      if (msg.type === "activity_logged" || msg.type === "plan_updated" || msg.type === "summary_ready") {
        void refreshDashboard()
      }
    })

    return () => { unsub(); ws.disconnect() }
  }, [refreshDashboard])

  // Service Worker registration
  useEffect(() => {
    void registerServiceWorker()
    const unsub = onActivityPopup(() => dispatch({ type: "SHOW_POPUP" }))
    return unsub
  }, [])

  return (
    <AppContext.Provider value={{ state, dispatch, refreshDashboard, openActivityPopup, closeActivityPopup, snoozePopup }}>
      {children}
    </AppContext.Provider>
  )
}
