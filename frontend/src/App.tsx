import { useEffect, useState } from "react";
import { getReady } from "./lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; database: string }
  | { kind: "error" };

export default function App() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    getReady()
      .then((r) => setState({ kind: "ok", database: r.database }))
      .catch(() => setState({ kind: "error" }));
  }, []);

  const color =
    state.kind === "ok" ? "#2dd4bf" : state.kind === "error" ? "#f87171" : "#94a3b8";

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        color: "#e2e8f0",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <h1 style={{ marginBottom: 8 }}>QueryWise AI</h1>
        <p style={{ color }}>
          {state.kind === "loading" && "Checking backend…"}
          {state.kind === "ok" && `Backend ready · database ${state.database}`}
          {state.kind === "error" && "Backend unavailable"}
        </p>
      </div>
    </main>
  );
}