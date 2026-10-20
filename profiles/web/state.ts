export type ProjectedState = { text: string; status: "pending" | "observed" };

/** A request never becomes an observed success merely because it was sent. */
export function projectState(requested: string | null, observed: string | null): ProjectedState {
  if (requested && observed !== requested) return { text: "Request pending", status: "pending" };
  return { text: observed ? `Observed: ${observed}` : "No observed change", status: "observed" };
}
