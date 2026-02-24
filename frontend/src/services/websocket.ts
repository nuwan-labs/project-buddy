import type { WebSocketMessage } from "@/types"

type MessageHandler = (msg: WebSocketMessage) => void

const RECONNECT_DELAY_MS = 3000
const MAX_RECONNECT      = 10

export class WebSocketClient {
  private url: string
  private ws: WebSocket | null = null
  private handlers: MessageHandler[] = []
  private reconnectCount = 0
  private shouldReconnect = true
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  constructor(url: string) {
    this.url = url
  }

  connect(): void {
    this.shouldReconnect = true
    this._open()
  }

  disconnect(): void {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.push(handler)
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler)
    }
  }

  private _open(): void {
    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this.reconnectCount = 0
        console.debug("[WS] connected to", this.url)
      }

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const msg = JSON.parse(event.data as string) as WebSocketMessage
          this.handlers.forEach((h) => h(msg))
        } catch {
          // ignore malformed messages
        }
      }

      this.ws.onclose = () => {
        console.debug("[WS] connection closed")
        this._scheduleReconnect()
      }

      this.ws.onerror = () => {
        this.ws?.close()
      }
    } catch (err) {
      console.warn("[WS] open error", err)
      this._scheduleReconnect()
    }
  }

  private _scheduleReconnect(): void {
    if (!this.shouldReconnect || this.reconnectCount >= MAX_RECONNECT) return
    this.reconnectCount++
    this.reconnectTimer = setTimeout(() => {
      console.debug(`[WS] reconnecting (attempt ${this.reconnectCount})`)
      this._open()
    }, RECONNECT_DELAY_MS)
  }
}

// Singleton instance — initialized lazily in AppContext
let _client: WebSocketClient | null = null

export function getWsClient(url: string): WebSocketClient {
  if (!_client) _client = new WebSocketClient(url)
  return _client
}
