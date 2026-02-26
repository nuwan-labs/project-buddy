import { useState, useEffect } from "react"
import Layout from "@/components/Layout"
import { deepseekApi } from "@/services/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/components/Notifications"
import { todayISO } from "@/utils/formatting"
import { CheckCircle2, XCircle, RefreshCw, Cpu, Calendar } from "lucide-react"

interface OllamaStatus {
  reachable: boolean
  model: string | null
  message: string | null
}

export default function Settings() {
  const [status, setStatus]         = useState<OllamaStatus | null>(null)
  const [statusLoading, setStatusLoading] = useState(false)

  const [analysisDate, setAnalysisDate] = useState(todayISO())
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisResult, setAnalysisResult]   = useState<string | null>(null)
  const [analysisError, setAnalysisError]     = useState<string | null>(null)

  async function checkStatus() {
    setStatusLoading(true)
    try {
      const { data: res } = await deepseekApi.status()
      setStatus(res.data)
    } catch {
      setStatus({ reachable: false, model: null, message: "Cannot reach Ollama server." })
    } finally {
      setStatusLoading(false)
    }
  }

  // Check status on mount
  useEffect(() => { void checkStatus() }, [])

  async function handleTriggerAnalysis() {
    setAnalysisLoading(true)
    setAnalysisResult(null)
    setAnalysisError(null)
    try {
      const { data: res } = await deepseekApi.triggerAnalysis(analysisDate)
      setAnalysisResult(res.data.summary_text || "Analysis completed.")
      toast({ title: "Analysis completed." })
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? "Analysis failed. Check that Ollama is running and logs exist for this date."
      setAnalysisError(msg)
      toast({ title: "Analysis failed.", variant: "destructive" })
    } finally {
      setAnalysisLoading(false)
    }
  }

  return (
    <Layout>
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground">Configure Project Buddy</p>
        </div>

        {/* ─── Ollama status card ─────────────────────────────────────────── */}
        <div className="border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-blue-600" />
            <h2 className="font-semibold">DeepSeek / Ollama Status</h2>
          </div>

          {statusLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Checking connection…</span>
            </div>
          ) : status ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                {status.reachable
                  ? <CheckCircle2 className="h-5 w-5 text-green-500" />
                  : <XCircle className="h-5 w-5 text-red-500" />}
                <span className={`text-sm font-medium ${status.reachable ? "text-green-700" : "text-red-700"}`}>
                  {status.reachable ? "Connected" : "Unreachable"}
                </span>
              </div>
              {status.model && (
                <p className="text-sm text-muted-foreground">
                  Model: <span className="font-mono text-foreground">{status.model}</span>
                </p>
              )}
              {status.message && (
                <p className="text-sm text-muted-foreground">{status.message}</p>
              )}
            </div>
          ) : null}

          <Button
            size="sm"
            variant="outline"
            disabled={statusLoading}
            onClick={() => void checkStatus()}
          >
            <RefreshCw className={`h-4 w-4 mr-1.5 ${statusLoading ? "animate-spin" : ""}`} />
            Refresh Status
          </Button>

          <p className="text-xs text-muted-foreground border-t pt-3">
            Ollama must be running at the configured host (default <code className="font-mono">192.168.200.5:11434</code>)
            with the DeepSeek R1 model loaded. AI analysis is optional — Project Buddy works fully without it.
          </p>
        </div>

        {/* ─── Manual analysis trigger ────────────────────────────────────── */}
        <div className="border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-600" />
            <h2 className="font-semibold">Trigger Daily Analysis</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Manually run the end-of-day AI analysis for a specific date.
            Activity logs must exist for that date. The analysis runs automatically at 5:00 PM on workdays.
          </p>
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <Label htmlFor="analysis-date">Date</Label>
              <Input
                id="analysis-date"
                type="date"
                value={analysisDate}
                onChange={e => {
                  setAnalysisDate(e.target.value)
                  setAnalysisResult(null)
                  setAnalysisError(null)
                }}
              />
            </div>
            <Button
              disabled={analysisLoading || !status?.reachable}
              onClick={() => void handleTriggerAnalysis()}
              title={!status?.reachable ? "Ollama is not reachable" : undefined}
            >
              {analysisLoading ? (
                <><RefreshCw className="h-4 w-4 mr-1.5 animate-spin" /> Running…</>
              ) : (
                "Run Analysis"
              )}
            </Button>
          </div>

          {analysisResult && (
            <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-800 whitespace-pre-wrap">
              {analysisResult}
            </div>
          )}
          {analysisError && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-800">
              {analysisError}
            </div>
          )}
        </div>

        {/* ─── App info ──────────────────────────────────────────────────── */}
        <div className="border rounded-xl p-5 space-y-2">
          <h2 className="font-semibold text-sm">About</h2>
          <dl className="text-sm space-y-1">
            <div className="flex gap-2">
              <dt className="text-muted-foreground w-32 shrink-0">App</dt>
              <dd className="font-medium">Project Buddy</dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-muted-foreground w-32 shrink-0">Backend</dt>
              <dd className="font-mono text-xs">http://localhost:5000</dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-muted-foreground w-32 shrink-0">WebSocket</dt>
              <dd className="font-mono text-xs">ws://localhost:5000/ws/notifications</dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-muted-foreground w-32 shrink-0">AI Model</dt>
              <dd className="font-mono text-xs">deepseek-r1:7b (Ollama)</dd>
            </div>
          </dl>
        </div>
      </div>
    </Layout>
  )
}
