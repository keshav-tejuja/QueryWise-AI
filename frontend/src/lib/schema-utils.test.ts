import type { TableInfo } from "./api/schema";
import { filterTables, formatRows, incomingReferences } from "./schema-utils";

const base: Pick<
  TableInfo,
  "schema_name" | "kind" | "comment" | "estimated_rows" | "primary_key" | "unique_constraints" | "indexes"
> = {
  schema_name: "public",
  kind: "table",
  comment: null,
  estimated_rows: null,
  primary_key: [],
  unique_constraints: [],
  indexes: [],
};

const customers: TableInfo = {
  ...base, name: "customers", qualified_name: "public.customers", comment: "People who buy",
  columns: [{ name: "id", data_type: "integer", nullable: false, position: 1, comment: null, is_primary_key: true, is_foreign_key: false }],
  foreign_keys: [],
};
const orders: TableInfo = {
  ...base, name: "orders", qualified_name: "public.orders",
  columns: [{ name: "customer_id", data_type: "integer", nullable: false, position: 1, comment: null, is_primary_key: false, is_foreign_key: true }],
  foreign_keys: [{ name: "fk", columns: ["customer_id"], referenced_schema: "public", referenced_table: "customers", referenced_columns: ["id"] }],
};

describe("filterTables", () => {
  it("returns everything for a blank query", () => expect(filterTables([customers, orders], "  ")).toHaveLength(2));
  it("matches table names, comments and column names", () => {
    expect(filterTables([customers, orders], "ORDER")).toEqual([orders]);
    expect(filterTables([customers, orders], "buy")).toEqual([customers]);
    expect(filterTables([customers, orders], "customer_id")).toEqual([orders]);
  });
});

describe("incomingReferences", () => {
  it("finds tables whose foreign keys point at the target", () => {
    const refs = incomingReferences([customers, orders], customers);
    expect(refs).toHaveLength(1);
    expect(refs[0].table.name).toBe("orders");
    expect(incomingReferences([customers, orders], orders)).toEqual([]);
  });
});

describe("formatRows", () => {
  it.each([[null, "unknown"], [12, "~12 rows"], [1500, "~1.5k rows"], [2_500_000, "~2.5M rows"]])(
    "formats %s", (input, expected) => expect(formatRows(input)).toBe(expected),
  );
});