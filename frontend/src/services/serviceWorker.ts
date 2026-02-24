/**
 * Service Worker registration and message bridge.
 *
 * The SW runs in public/service-worker.js.
 * When the WS receives a "notification" / SHOW_ACTIVITY_POPUP message,
 * we tell the SW to show an OS notification. If the user clicks it,
 * the SW posts SHOW_ACTIVITY_POPUP back to this client.
 */

type SwReadyCallback = () => void
let _onPopupCallbacks: SwReadyCallback[] = []

export function onActivityPopup(cb: SwReadyCallback): () => void {
  _onPopupCallbacks.push(cb)
  return () => {
    _onPopupCallbacks = _onPopupCallbacks.filter((f) => f !== cb)
  }
}

export async function registerServiceWorker(): Promise<void> {
  if (!("serviceWorker" in navigator)) return

  try {
    const reg = await navigator.serviceWorker.register("/service-worker.js", {
      scope: "/",
    })
    console.debug("[SW] registered:", reg.scope)

    // Listen for messages from the SW (e.g. notification click → open popup)
    navigator.serviceWorker.addEventListener("message", (event: MessageEvent) => {
      const data = event.data as { type?: string }
      if (data?.type === "SHOW_ACTIVITY_POPUP") {
        _onPopupCallbacks.forEach((cb) => cb())
      }
    })
  } catch (err) {
    console.warn("[SW] registration failed:", err)
  }
}

/** Ask the SW to show a native OS notification */
export async function showSwNotification(message: string): Promise<void> {
  const reg = await navigator.serviceWorker.ready
  reg.active?.postMessage({
    type:    "SHOW_NOTIFICATION",
    title:   "Project Buddy",
    message,
  })
}
