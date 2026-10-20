/** The badge a status wears; the word is always there and the badge reinforces it. */
function projectBadge(status) {
  return status === "pending" ? "attention" : "stable";
}

/** Pure semantic state projection; no backend is contacted. */
function projectState(requested, observed) {
  if (requested && observed !== requested) {
    return { text: "Request pending", status: "pending" };
  }
  return {
    text: observed ? `Observed: ${observed}` : "No observed change",
    status: "observed",
  };
}

if (typeof module !== "undefined") module.exports = { projectState, projectBadge };
if (typeof window !== "undefined") {
  window.projectState = projectState;
  window.projectBadge = projectBadge;
}
