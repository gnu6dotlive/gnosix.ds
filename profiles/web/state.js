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

if (typeof module !== "undefined") module.exports = { projectState };
if (typeof window !== "undefined") window.projectState = projectState;
