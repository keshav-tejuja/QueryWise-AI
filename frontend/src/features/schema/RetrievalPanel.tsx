import { Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/client";
import { useRetrieve } from "./hooks";

export function RetrievalPanel({ connectionId }: { connectionId: string }) {
  const [question, setQuestion] = useState("");
  const retrieve = useRetrieve();
  const result = retrieve.data;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (question.trim()) retrieve.mutate({ connectionId, question: question.trim() });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle as="h2">Try the relevance engine</CardTitle>
        <CardDescription>
          See which tables and joins QueryWise would send to the model for a question. No AI is involved yet.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            aria-label="Question"
            placeholder="e.g. total order amount per customer"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <Button type="submit" loading={retrieve.isPending} disabled={!question.trim()}>
            <Search className="h-4 w-4" aria-hidden="true" /> Analyse
          </Button>
        </form>

        {retrieve.isError && (
          <Alert variant="destructive">
            {retrieve.error instanceof ApiError ? retrieve.error.message : "Something went wrong."}
          </Alert>
        )}

        {result && (
          <div className="space-y-4 text-sm">
            {result.tables.length === 0 && <Alert variant="warning">No table or column matched this question.</Alert>}
            {result.tables.length > 0 && (
              <ul className="space-y-2">
                {result.tables.map((table) => (
                  <li key={table.qualified_name} className="rounded-md border border-border p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{table.qualified_name}</span>
                      <Badge variant={table.role === "match" ? "success" : "muted"}>
                        {table.role === "match" ? `match · score ${table.score}` : "join bridge"}
                      </Badge>
                    </div>
                    {table.reasons.length > 0 && (
                      <p className="mt-1 text-xs text-muted-foreground">{table.reasons.join(" · ")}</p>
                    )}
                    <p className="mt-1 font-mono text-xs">{table.columns.join(", ")}</p>
                  </li>
                ))}
              </ul>
            )}

            {result.join_paths.length > 0 && (
              <div>
                <h3 className="mb-1 font-medium">Join paths (declared foreign keys)</h3>
                <ul className="space-y-1 font-mono text-xs">
                  {result.join_paths.map((path) => (
                    <li key={path.tables.join(">")}>
                      {path.tables.join(" → ")}
                      {path.ambiguous && <Badge variant="warning" className="ml-2">ambiguous</Badge>}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.warnings.map((warning) => (
              <Alert key={warning} variant="warning">{warning}</Alert>
            ))}

            {result.unmatched_terms.length > 0 && (
              <p className="text-muted-foreground">
                Terms with no match in the schema:{" "}
                {result.unmatched_terms.map((term) => (
                  <Badge key={term} variant="muted" className="mr-1">{term}</Badge>
                ))}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}