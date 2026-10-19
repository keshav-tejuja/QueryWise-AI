import { Database, Pencil, PlugZap, RefreshCw, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { CheckResult, Connection, ConnectionStatus } from "@/lib/api/connections";
import { CheckResultView } from "./CheckResultView";

const STATUS: Record<ConnectionStatus, { label: string; variant: "success" | "destructive" | "muted" }> = {
  connected: { label: "Connected", variant: "success" },
  error: { label: "Error", variant: "destructive" },
  disconnected: { label: "Disconnected", variant: "muted" },
  untested: { label: "Not tested", variant: "muted" },
};

interface ConnectionCardProps {
  connection: Connection;
  check?: CheckResult;
  busy: boolean;
  onTest: () => void;
  onEdit: () => void;
  onDisconnect: () => void;
  onDelete: () => void;
}

export function ConnectionCard({ connection, check, busy, onTest, onEdit, onDisconnect, onDelete }: ConnectionCardProps) {
  const status = STATUS[connection.status];
  return (
    <Card>
      <CardContent className="space-y-4 p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Database className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <h2 className="truncate font-semibold">{connection.name}</h2>
              <p className="truncate text-sm text-muted-foreground">
                {connection.host}:{connection.port} / {connection.database}
              </p>
            </div>
          </div>
          <Badge variant={status.variant}>{status.label}</Badge>
        </div>

        <dl className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <dt className="text-muted-foreground">User</dt>
            <dd className="truncate">{connection.username}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">SSL</dt>
            <dd>{connection.ssl_mode}</dd>
          </div>
          <div className="col-span-2">
            <dt className="text-muted-foreground">Last tested</dt>
            <dd>{connection.last_tested_at ? new Date(connection.last_tested_at).toLocaleString() : "Never"}</dd>
          </div>
        </dl>

        {check && <CheckResultView check={check} />}

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={onTest} loading={busy}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            {connection.status === "disconnected" ? "Reconnect" : "Test"}
          </Button>
          <Button variant="ghost" size="sm" onClick={onEdit} disabled={busy}>
            <Pencil className="h-4 w-4" aria-hidden="true" /> Edit
          </Button>
          {connection.status !== "disconnected" && (
            <Button variant="ghost" size="sm" onClick={onDisconnect} disabled={busy}>
              <PlugZap className="h-4 w-4" aria-hidden="true" /> Disconnect
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onDelete} disabled={busy} className="text-destructive hover:text-destructive">
            <Trash2 className="h-4 w-4" aria-hidden="true" /> Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}