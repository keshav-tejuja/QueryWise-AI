import { Database, RefreshCw, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useActiveConnection } from "@/features/connections/ActiveConnectionContext";
import { useRefreshSchema, useSchema } from "@/features/schema/hooks";
import { RetrievalPanel } from "@/features/schema/RetrievalPanel";
import { TableDetail } from "@/features/schema/TableDetail";
import { TableList } from "@/features/schema/TableList";
import { ApiError } from "@/lib/api/client";
import { filterTables } from "@/lib/schema-utils";

export function SchemaExplorerPage() {
  const { active, isLoading: connectionsLoading } = useActiveConnection();
  const schema = useSchema(active?.id);
  const refresh = useRefreshSchema();
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  if (connectionsLoading) return <Skeleton className="h-64" />;

  if (!active) {
    return (
      <>
        <PageHeader title="Schema Explorer" description="Browse tables, columns and relationships." />
        <EmptyState
          icon={Database}
          title="No active connection"
          description="Connect a database first, then its schema appears here."
          action={<Link to="/connections" className={buttonVariants()}>Go to connections</Link>}
        />
      </>
    );
  }

  const notLoaded = schema.error instanceof ApiError && schema.error.code === "schema_not_loaded";

  async function handleRefresh() {
    if (!active) return;
    setNotice(null);
    try {
      const result = await refresh.mutateAsync(active.id);
      if (!result.changed) setNotice("Schema is up to date.");
      else if (result.diff) {
        const { added_tables, removed_tables, changed_tables } = result.diff;
        setNotice(`Schema updated: ${added_tables.length} added, ${removed_tables.length} removed, ${changed_tables.length} changed.`);
      } else setNotice("Schema discovered.");
    } catch {
      /* the error alert below shows the message */
    }
  }

  const refreshButton = (
    <Button variant="outline" onClick={() => void handleRefresh()} loading={refresh.isPending}>
      <RefreshCw className="h-4 w-4" aria-hidden="true" /> {notLoaded ? "Discover schema" : "Refresh schema"}
    </Button>
  );

  const tables = schema.data?.tables ?? [];
  const visible = filterTables(tables, search);
  const current = tables.find((t) => t.qualified_name === selected) ?? visible[0] ?? null;
  const relationshipCount = tables.reduce((sum, t) => sum + t.foreign_keys.length, 0);

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader title="Schema Explorer" description={`Structure of ${active.name}.`} />
        {!notLoaded && refreshButton}
      </div>

      {notice && <Alert variant="success" className="mb-4">{notice}</Alert>}
      {refresh.isError && (
        <Alert variant="destructive" className="mb-4">
          {refresh.error instanceof ApiError ? refresh.error.message : "Couldn't refresh the schema."}
        </Alert>
      )}

      {schema.isPending ? (
        <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      ) : notLoaded ? (
        <EmptyState
          icon={Database}
          title="Schema not discovered yet"
          description="QueryWise reads table and column metadata only, never your rows."
          action={refreshButton}
        />
      ) : schema.isError ? (
        <Alert variant="destructive">Couldn't load the schema. Try refreshing the page.</Alert>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <Badge variant="success">{tables.length} tables</Badge>
            <Badge variant="muted">{relationshipCount} relationships</Badge>
            <span className="text-muted-foreground">
              Captured {new Date(schema.data.captured_at).toLocaleString()} · version {schema.data.schema_hash.slice(0, 8)}
            </span>
            {schema.data.truncated && <Badge variant="warning">Showing the first 500 tables</Badge>}
          </div>

          {tables.length === 0 ? (
            <Alert variant="warning">
              No accessible tables were found. Check that the database role has SELECT privileges.
            </Alert>
          ) : (
            <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
              <Card>
                <CardContent className="space-y-3 p-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" aria-hidden="true" />
                    <Input
                      aria-label="Search tables"
                      placeholder="Search tables or columns"
                      className="pl-9"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </div>
                  <TableList tables={visible} selected={current?.qualified_name ?? null} onSelect={setSelected} />
                </CardContent>
              </Card>
              {current ? (
                <TableDetail table={current} allTables={tables} onSelectTable={setSelected} />
              ) : (
                <Alert>Select a table to see its details.</Alert>
              )}
            </div>
          )}

          <RetrievalPanel connectionId={active.id} />
        </div>
      )}
    </>
  );
}