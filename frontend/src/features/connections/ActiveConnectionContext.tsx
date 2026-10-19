import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { Connection } from "@/lib/api/connections";
import { useConnections } from "./hooks";

const STORAGE_KEY = "qw-active-connection"; // an id only, never a credential

function readStoredId(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

interface ActiveConnectionValue {
  connections: Connection[];
  isLoading: boolean;
  active: Connection | null;
  setActiveId: (id: string) => void;
}

const ActiveConnectionContext = createContext<ActiveConnectionValue | null>(null);

export function ActiveConnectionProvider({ children }: { children: ReactNode }) {
  const { data, isPending } = useConnections();
  const [storedId, setStoredId] = useState<string | null>(readStoredId);

  const value = useMemo<ActiveConnectionValue>(() => {
    const connections = data ?? [];
    const usable = connections.filter((c) => c.status === "connected");
    const active = usable.find((c) => c.id === storedId) ?? usable[0] ?? null;
    return {
      connections,
      isLoading: isPending,
      active,
      setActiveId: (id: string) => {
        setStoredId(id);
        try {
          localStorage.setItem(STORAGE_KEY, id);
        } catch {
          // storage unavailable: the choice still applies for this session
        }
      },
    };
  }, [data, isPending, storedId]);

  return <ActiveConnectionContext.Provider value={value}>{children}</ActiveConnectionContext.Provider>;
}

export function useActiveConnection(): ActiveConnectionValue {
  const ctx = useContext(ActiveConnectionContext);
  if (!ctx) throw new Error("useActiveConnection must be used within ActiveConnectionProvider");
  return ctx;
}