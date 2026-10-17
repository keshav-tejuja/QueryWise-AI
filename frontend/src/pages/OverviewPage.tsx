import { Database } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/features/auth/AuthContext";
import { useBackendStatus } from "@/features/system/useBackendStatus";

type Tone = "success" | "warning" | "destructive" | "muted";

function StatusRow({ label, value, tone }: { label: string; value: string; tone: Tone }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}

export function OverviewPage() {
  const { user } = useAuth();
  const status = useBackendStatus();
  const firstName = user?.display_name.split(" ")[0] ?? "there";
  const data = status.data;

  const api: { value: string; tone: Tone } =
    data?.status === "unreachable" ? { value: "Unreachable", tone: "destructive" } : { value: "Operational", tone: "success" };
  const database: { value: string; tone: Tone } =
    data?.status === "ready"
      ? { value: "Connected", tone: "success" }
      : data?.status === "degraded"
        ? { value: "Unavailable", tone: "warning" }
        : { value: "Unknown", tone: "muted" };

  return (
    <>
      <PageHeader title={`Welcome back, ${firstName}`} description="The current state of your QueryWise workspace." />

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle as="h2">System status</CardTitle>
            <CardDescription>Live checks against the backend, refreshed every 15 seconds.</CardDescription>
          </CardHeader>
          <CardContent>
            {status.isPending ? (
              <div className="space-y-3">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-full" />
              </div>
            ) : (
              <>
                {data?.status === "unreachable" && (
                  <Alert variant="destructive" className="mb-3">
                    The backend can't be reached. Check that the services are running.
                  </Alert>
                )}
                <div className="divide-y divide-border">
                  <StatusRow label="API" value={api.value} tone={api.tone} />
                  <StatusRow label="Application database" value={database.value} tone={database.tone} />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  loading={status.isFetching}
                  onClick={() => void status.refetch()}
                >
                  Check again
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <EmptyState
          icon={Database}
          title="No databases connected"
          description="Connect a PostgreSQL database to explore its schema and ask questions in plain English."
          action={
            <div className="flex flex-col items-center gap-2">
              <Button disabled>Connect a database</Button>
              <Badge variant="muted">Coming soon</Badge>
            </div>
          }
        />
      </div>
    </>
  );
}