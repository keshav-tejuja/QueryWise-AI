import { Eye, Table2 } from "lucide-react";
import type { TableInfo } from "@/lib/api/schema";
import { cn } from "@/lib/utils";

interface TableListProps {
  tables: TableInfo[];
  selected: string | null;
  onSelect: (qualifiedName: string) => void;
}

export function TableList({ tables, selected, onSelect }: TableListProps) {
  if (tables.length === 0) {
    return <p className="px-2 py-6 text-center text-sm text-muted-foreground">No tables match your search.</p>;
  }
  return (
    <ul aria-label="Tables" className="space-y-1">
      {tables.map((table) => {
        const Icon = table.kind === "table" ? Table2 : Eye;
        const isSelected = selected === table.qualified_name;
        return (
          <li key={table.qualified_name}>
            <button
              type="button"
              onClick={() => onSelect(table.qualified_name)}
              aria-current={isSelected ? "true" : undefined}
              className={cn(
                "flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                isSelected ? "bg-primary/10 text-primary" : "hover:bg-accent",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span className="min-w-0 flex-1 truncate">
                {table.schema_name !== "public" && <span className="text-muted-foreground">{table.schema_name}.</span>}
                {table.name}
              </span>
              <span className="text-xs text-muted-foreground">{table.columns.length}</span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}