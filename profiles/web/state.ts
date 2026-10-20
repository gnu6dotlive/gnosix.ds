export type ProjectedState = { text: string; status: "pending" | "observed" };

/** The badge a status wears.

 * A request that has not been observed is a condition that asks for
 * inspection; one that has been observed is not. The word is always
 * there; the badge only reinforces it.
 */
export function projectBadge(status: "pending" | "observed"): "attention" | "stable" {
  return status === "pending" ? "attention" : "stable";
}

/** A request never becomes an observed success merely because it was sent. */
export function projectState(requested: string | null, observed: string | null): ProjectedState {
  if (requested && observed !== requested) return { text: "Request pending", status: "pending" };
  return { text: observed ? `Observed: ${observed}` : "No observed change", status: "observed" };
}
