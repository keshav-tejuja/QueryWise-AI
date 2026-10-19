import { Database, LogOut, Menu } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/features/auth/AuthContext";
import { useActiveConnection } from "@/features/connections/ActiveConnectionContext";
import { StatusIndicator } from "./StatusIndicator";
import { ThemeToggle } from "./ThemeToggle";

function ConnectionSelector() {
  const { connections, isLoading, active, setActiveId } = useActiveConnection();
  const usable = connections.filter((c) => c.status === "connected");

  if (isLoading) return <Skeleton className="hidden h-9 w-48 sm:block" />;

  if (usable.length === 0) {
    return (
      <Link
        to="/connections"
        className="hidden h-9 items-center gap-2 rounded-md border border-dashed border-border px-3 text-sm text-muted-foreground hover:text-foreground sm:flex"
      >
        <Database className="h-4 w-4" aria-hidden="true" />
        {connections.length > 0 ? "No active connection" : "Connect a database"}
      </Link>
    );
  }

  return (
    <div className="hidden items-center gap-2 sm:flex">
      <span className="h-2 w-2 rounded-full bg-success" aria-hidden="true" />
      <Select
        aria-label="Active database connection"
        className="h-9 w-56"
        value={active?.id ?? ""}
        onChange={(event) => setActiveId(event.target.value)}
      >
        {usable.map((connection) => (
          <option key={connection.id} value={connection.id}>
            {connection.name}
          </option>
        ))}
      </Select>
    </div>
  );
}

export function Header({ onOpenNav }: { onOpenNav: () => void }) {
  const { user, logout } = useAuth();
  const initial = user?.display_name.trim().charAt(0).toUpperCase() ?? "?";

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur sm:px-6 lg:px-8">
      <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation" onClick={onOpenNav}>
        <Menu className="h-5 w-5" aria-hidden="true" />
      </Button>

      <ConnectionSelector />

      <div className="ml-auto flex items-center gap-2">
        <StatusIndicator />
        <ThemeToggle />
        <div className="flex items-center gap-2 pl-1">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary"
            aria-hidden="true"
          >
            {initial}
          </div>
          <span className="hidden max-w-[10rem] truncate text-sm md:inline">{user?.display_name}</span>
          <Button variant="ghost" size="icon" aria-label="Sign out" onClick={() => void logout()}>
            <LogOut className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>
    </header>
  );
}