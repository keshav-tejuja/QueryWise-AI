import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { ActiveConnectionProvider } from "@/features/connections/ActiveConnectionContext";
import { Header } from "./Header";
import { SidebarContent } from "./Sidebar";

export function AppShell() {
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    if (!navOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setNavOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navOpen]);

  return (
    <ActiveConnectionProvider>
      <div className="min-h-screen bg-background text-foreground">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
        >
          Skip to content
        </a>

        <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-border bg-card lg:block">
          <SidebarContent />
        </aside>

        {navOpen && (
          <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
            <div className="absolute inset-0 bg-black/60" aria-hidden="true" onClick={() => setNavOpen(false)} />
            <aside className="absolute inset-y-0 left-0 w-72 max-w-[85vw] border-r border-border bg-card shadow-xl">
              <SidebarContent onNavigate={() => setNavOpen(false)} />
            </aside>
          </div>
        )}

        <div className="lg:pl-64">
          <Header onOpenNav={() => setNavOpen(true)} />
          <main id="main" className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
            <Outlet />
          </main>
        </div>
      </div>
    </ActiveConnectionProvider>
  );
}