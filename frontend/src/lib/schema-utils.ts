import type { ForeignKey, TableInfo } from "./api/schema";

export function filterTables(tables: TableInfo[], query: string): TableInfo[] {
  const q = query.trim().toLowerCase();
  if (!q) return tables;
  return tables.filter(
    (t) =>
      t.qualified_name.toLowerCase().includes(q) ||
      (t.comment ?? "").toLowerCase().includes(q) ||
      t.columns.some((c) => c.name.toLowerCase().includes(q)),
  );
}

export interface IncomingReference {
  table: TableInfo;
  foreignKey: ForeignKey;
}

/** Foreign keys in OTHER tables (or this one) that point at `target`. */
export function incomingReferences(tables: TableInfo[], target: TableInfo): IncomingReference[] {
  const refs: IncomingReference[] = [];
  for (const table of tables) {
    for (const foreignKey of table.foreign_keys) {
      if (`${foreignKey.referenced_schema}.${foreignKey.referenced_table}` === target.qualified_name) {
        refs.push({ table, foreignKey });
      }
    }
  }
  return refs;
}

export function formatRows(count: number | null): string {
  if (count === null) return "unknown";
  if (count >= 1_000_000) return `~${(count / 1_000_000).toFixed(1)}M rows`;
  if (count >= 1_000) return `~${(count / 1_000).toFixed(1)}k rows`;
  return `~${count} rows`;
}