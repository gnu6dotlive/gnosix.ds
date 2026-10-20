import { useState } from "react";
import { projectState } from "./state";
import "./components.css";

/** Example integration: supply observed from the real data source, not from this button. */
export function GnosixStateAction({ observed, onRequest }: {
  observed: string | null;
  onRequest: (next: string) => void;
}) {
  const [requested, setRequested] = useState<string | null>(null);
  const state = projectState(requested, observed);
  return <div>
    <button type="button" className="gnosix-action" onClick={() => {
      setRequested("on");
      onRequest("on");
    }}>Enable</button>
    <p role="status" aria-live="polite" className="gnosix-state" data-status={state.status}>{state.text}</p>
  </div>;
}
