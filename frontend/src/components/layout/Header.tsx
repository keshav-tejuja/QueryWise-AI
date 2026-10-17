import { Database, LogOut, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/AuthContext";
import { StatusIndicator } from "./StatusIndicator";
import { ThemeToggle } from "./ThemeToggle";

export function Header({ onOpenNav }: { onOpenNav: () => void }) {
  const { user, logout } = useAuth();
  const initial = user?.display_name.trim().charAt(0).toUpperCase() ?? "?";

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur sm:px-6 lg:px-8">
      <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation" onClick={onOpenNav}>
        <Menu className="h-5 w-5" aria-hidden="true" />
      </Button>

      {/* Becomes a real connection selector once database connections exist. */}
      <button
        type="button"
        disabled
        aria-label="Active database connection: none"
        className="hidden h-9 items-center gap-2 rounded-md border border-border px-3 text-sm text-muted-foreground disabled:cursor-not-allowed sm:flex"
      >
        <Database className="h-4 w-4" aria-hidden="true" />
        No database connected
      </button>

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