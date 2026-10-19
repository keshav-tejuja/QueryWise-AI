import { Database, Plus } from "lucide-react";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Modal } from "@/components/ui/modal";
import { Skeleton } from "@/components/ui/skeleton";
import { ConnectionCard } from "@/features/connections/ConnectionCard";
import { ConnectionForm } from "@/features/connections/ConnectionForm";
import { useConnectionMutations, useConnections } from "@/features/connections/hooks";
import { ApiError } from "@/lib/api/client";
import {
  connectionsApi,
  type CheckResult,
  type Connection,
  type ConnectionInput,
  type ConnectionPatch,
} from "@/lib/api/connections";

export function ConnectionsPage() {
  const { data, isPending, isError, refetch } = useConnections();
  const mutations = useConnectionMutations();
  const [editing, setEditing] = useState<Connection | "new" | null>(null);
  const [deleting, setDeleting] = useState<Connection | null>(null);
  const [checks, setChecks] = useState<Record<string, CheckResult>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function run(id: string, action: () => Promise<void>) {
    setBusyId(id);
    setActionError(null);
    try {
      await action();
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : "Something went wrong. Please try again.");
    } finally {
      setBusyId(null);
    }
  }

  const remember = (id: string, check: CheckResult | null) => {
    if (check) setChecks((prev) => ({ ...prev, [id]: check }));
  };

  async function handleSubmit(payload: ConnectionPatch) {
    if (editing === "new") {
      const result = await mutations.create.mutateAsync(payload as ConnectionInput);
      remember(result.connection.id, result.check);
    } else if (editing) {
      const result = await mutations.update.mutateAsync({ id: editing.id, input: payload });
      remember(result.connection.id, result.check);
    }
    setEditing(null);
  }

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <PageHeader title="Database Connections" description="Connect the PostgreSQL databases you want to analyse." />
        <Button onClick={() => setEditing("new")}>
          <Plus className="h-4 w-4" aria-hidden="true" /> Add connection
        </Button>
      </div>

      {actionError && <Alert variant="destructive" className="mb-4">{actionError}</Alert>}

      {isPending ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      ) : isError ? (
        <Alert variant="destructive">
          Couldn't load your connections.{" "}
          <button className="underline" onClick={() => void refetch()}>
            Try again
          </button>
        </Alert>
      ) : data.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No databases connected yet"
          description="Add a PostgreSQL connection. Passwords are encrypted at rest and never shown again."
          action={<Button onClick={() => setEditing("new")}>Add your first connection</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((connection) => (
            <ConnectionCard
              key={connection.id}
              connection={connection}
              check={checks[connection.id]}
              busy={busyId === connection.id}
              onTest={() =>
                void run(connection.id, async () => {
                  const result = await mutations.test.mutateAsync(connection.id);
                  remember(connection.id, result.check);
                })
              }
              onEdit={() => setEditing(connection)}
              onDisconnect={() => void run(connection.id, async () => void (await mutations.disconnect.mutateAsync(connection.id)))}
              onDelete={() => setDeleting(connection)}
            />
          ))}
        </div>
      )}

      <Modal
        open={editing !== null}
        onClose={() => setEditing(null)}
        title={editing === "new" ? "Add database connection" : "Edit connection"}
      >
        {editing !== null && (
          <ConnectionForm
            key={editing === "new" ? "new" : editing.id}
            initial={editing === "new" ? undefined : editing}
            onSubmit={handleSubmit}
            onTest={connectionsApi.testParams}
            onCancel={() => setEditing(null)}
          />
        )}
      </Modal>

      <Modal open={deleting !== null} onClose={() => setDeleting(null)} title="Delete connection?">
        {deleting && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              This removes <strong className="text-foreground">{deleting.name}</strong> from QueryWise, along with its saved
              schema snapshots, metrics and linked history. Your actual database is not touched.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setDeleting(null)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => {
                  const target = deleting;
                  setDeleting(null);
                  void run(target.id, async () => void (await mutations.remove.mutateAsync(target.id)));
                }}
              >
                Delete
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
}