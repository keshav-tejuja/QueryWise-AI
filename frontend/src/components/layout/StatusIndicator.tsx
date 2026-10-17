import { useBackendStatus } from "@/features/system/useBackendStatus";
import { cn } from "@/lib/utils";

export function StatusIndicator() {
  const { data, isPending } = useBackendStatus();

  const state = isPending
    ? { label: "Checking…", dot: "bg-muted-foreground" }
    : data?.status === "ready"
      ? { label: "API ready", dot: "bg-success" }
      : data?.status === "degraded"
        ? { label: "Degraded", dot: "bg-warning" }
        : { label: "Offline", dot: "bg-destructive" };

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-2 rounded-full border border-border px-3 py-1 text-xs text-muted-foreground"
    >
      <span className={cn("h-2 w-2 rounded-full", state.dot)} aria-hidden="true" />
      <span className="hidden sm:inline">{state.label}</span>
      <span className="sr-only sm:hidden">{state.label}</span>
    </div>
  );
}