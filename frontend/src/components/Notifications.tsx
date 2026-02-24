/**
 * Notifications helper — wraps shadcn's useToast with typed convenience methods.
 *
 * Usage:
 *   const notify = useNotification()
 *   notify.success("Activity logged!")
 *   notify.error("Failed to save")
 *   notify.info("Tip: you can snooze the popup for 15 minutes")
 */
import { toast } from "@/components/ui/use-toast"

export function useNotification() {
  return {
    success: (title: string, description?: string) =>
      toast({ title, description }),

    error: (title: string, description?: string) =>
      toast({ title, description, variant: "destructive" }),

    info: (description: string) =>
      toast({ description }),
  }
}

// Re-export toast for direct imperative use
export { toast }
