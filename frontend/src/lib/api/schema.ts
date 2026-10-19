import { request } from "./client";

export interface ColumnInfo {
  name: string;
  data_type: string;
  nullable: boolean;
  position: number;
  comment: string | null;
  is_primary_key: boolean;
  is_foreign_key: boolean;
}
export interface ForeignKey {
  name: string;
  columns: string[];
  referenced_schema: string;
  referenced_table: string;
  referenced_columns: string[];
}
export interface IndexInfo {
  name: string;
  columns: string[];
  unique: boolean;
  primary: boolean;
}
export interface TableInfo {
  schema_name: string;
  name: string;
  qualified_name: string;
  kind: "table" | "view" | "materialized_view";
  comment: string | null;
  estimated_rows: number | null;
  columns: ColumnInfo[];
  primary_key: string[];
  unique_constraints: string[][];
  foreign_keys: ForeignKey[];
  indexes: IndexInfo[];
}
export interface SchemaSnapshot {
  connection_id: string;
  schema_hash: string;
  captured_at: string;
  truncated: boolean;
  tables: TableInfo[];
}
export interface SchemaDiff {
  added_tables: string[];
  removed_tables: string[];
  changed_tables: string[];
}
export interface RefreshResult {
  snapshot: SchemaSnapshot;
  changed: boolean;
  diff: SchemaDiff | null;
}

export interface RetrievedTable {
  qualified_name: string;
  role: "match" | "bridge";
  score: number;
  reasons: string[];
  columns: string[];
}
export interface JoinEdge {
  from_table: string;
  from_columns: string[];
  to_table: string;
  to_columns: string[];
  constraint: string;
}
export interface JoinStep {
  from_table: string;
  to_table: string;
  edges: JoinEdge[];
}
export interface JoinPath {
  tables: string[];
  steps: JoinStep[];
  ambiguous: boolean;
}
export interface RetrievalResult {
  question: string;
  terms: string[];
  tables: RetrievedTable[];
  join_paths: JoinPath[];
  unconnected_pairs: string[][];
  unmatched_terms: string[];
  warnings: string[];
}

export const schemaApi = {
  get: (id: string) => request<SchemaSnapshot>(`/connections/${id}/schema`),
  refresh: (id: string) => request<RefreshResult>(`/connections/${id}/schema/refresh`, { method: "POST" }),
  retrieve: (id: string, question: string, maxTables = 8) =>
    request<RetrievalResult>(`/connections/${id}/schema/retrieve`, {
      method: "POST",
      body: { question, max_tables: maxTables },
    }),
};