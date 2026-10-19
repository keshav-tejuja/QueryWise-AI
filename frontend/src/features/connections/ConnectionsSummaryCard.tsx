import { Database } from "lucide-react";
import { Link } from "react-router-dom";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useConnections } from "./hooks";

export function ConnectionsSummaryCard() {
  const { data, isPending, isError } = useConnections();

  if (isPending) {
    return (
      <Card>
        <CardContent className="space-y-3 p-6">
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-full" />
        </CardContent>
      </Card>
    );
  }
  if (isError) {
    return <Alert variant="destructive">Couldn't load your connections.</Alert>;
  }
  if (data.length === 0) {
    return (
      <EmptyState
        icon={Database}
        title="No databases connected"
        description="Connect a PostgreSQL database to explore its schema and ask questions in plain English."
        action={
          <Link to="/connections" className={buttonVariants()}>
            Connect a database
          </Link>
        }
      />
    );
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle as="h2">Connections</CardTitle>
        <CardDescription>
          {data.length} saved {data.length === 1 ? "connection" : "connections"}.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="divide-y divide-border">
          {data.map((connection) => (
            <li key={connection.id} className="flex items-center justify-between py-2 text-sm">
              <span className="truncate">{connection.name}</span>
              <Badge variant={connection.status === "connected" ? "success" : connection.status === "error" ? "destructive" : "muted"}>
                {connection.status}
              </Badge>
            </li>
          ))}
        </ul>
        <Link to="/connections" className={buttonVariants({ variant: "outline", size: "sm", className: "mt-4" })}>
          Manage connections
        </Link>
      </CardContent>
    </Card>
  );
}