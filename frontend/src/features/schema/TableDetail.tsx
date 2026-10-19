import { ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { TableInfo } from "@/lib/api/schema";
import { formatRows, incomingReferences } from "@/lib/schema-utils";

interface TableDetailProps {
  table: TableInfo;
  allTables: TableInfo[];
  onSelectTable: (qualifiedName: string) => void;
}

function LinkButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className="font-medium text-primary hover:underline">
      {label}
    </button>
  );
}

export function TableDetail({ table, allTables, onSelectTable }: TableDetailProps) {
  const incoming = incomingReferences(allTables, table);
  const known = new Set(allTables.map((t) => t.qualified_name));

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle as="h2">{table.qualified_name}</CardTitle>
            {table.kind !== "table" && <Badge variant="muted">{table.kind.replace("_", " ")}</Badge>}
            {table.estimated_rows !== null && <Badge variant="muted">{formatRows(table.estimated_rows)}</Badge>}
          </div>
          {table.comment && <CardDescription>{table.comment}</CardDescription>}
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Columns of {table.qualified_name}</caption>
            <thead className="text-xs uppercase text-muted-foreground">
              <tr>
                <th scope="col" className="py-2 pr-4 font-medium">Column</th>
                <th scope="col" className="py-2 pr-4 font-medium">Type</th>
                <th scope="col" className="py-2 pr-4 font-medium">Null</th>
                <th scope="col" className="py-2 font-medium">Comment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {table.columns.map((column) => (
                <tr key={column.name}>
                  <td className="py-2 pr-4">
                    <span className="font-medium">{column.name}</span>{" "}
                    {column.is_primary_key && <Badge>PK</Badge>}{" "}
                    {column.is_foreign_key && <Badge variant="muted">FK</Badge>}
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs">{column.data_type}</td>
                  <td className="py-2 pr-4">{column.nullable ? "yes" : "no"}</td>
                  <td className="py-2 text-muted-foreground">{column.comment ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle as="h3">Relationships</CardTitle>
          <CardDescription>Only declared foreign keys are treated as joins.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {table.foreign_keys.length === 0 && incoming.length === 0 && (
            <p className="text-muted-foreground">No declared relationships.</p>
          )}
          {table.foreign_keys.map((fk) => {
            const target = `${fk.referenced_schema}.${fk.referenced_table}`;
            return (
              <p key={fk.name} className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs">{fk.columns.join(", ")}</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" aria-label="references" />
                {known.has(target) ? <LinkButton label={target} onClick={() => onSelectTable(target)} /> : target}
                <span className="font-mono text-xs text-muted-foreground">({fk.referenced_columns.join(", ")})</span>
              </p>
            );
          })}
          {incoming.map(({ table: source, foreignKey }) => (
            <p key={`${source.qualified_name}-${foreignKey.name}`} className="flex flex-wrap items-center gap-2">
              <span className="text-muted-foreground">Referenced by</span>
              <LinkButton label={source.qualified_name} onClick={() => onSelectTable(source.qualified_name)} />
              <span className="font-mono text-xs text-muted-foreground">via {foreignKey.columns.join(", ")}</span>
            </p>
          ))}
        </CardContent>
      </Card>

      {table.indexes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle as="h3">Indexes</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {table.indexes.map((index) => (
                <li key={index.name} className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs">{index.name}</span>
                  <span className="text-muted-foreground">({index.columns.join(", ") || "expression"})</span>
                  {index.primary ? <Badge>primary</Badge> : index.unique ? <Badge variant="muted">unique</Badge> : null}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}