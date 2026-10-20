const dialog = document.getElementById("scene-dialog");
const dialogImage = dialog ? dialog.querySelector("img") : null;
let dialogOpener = null;

document.querySelectorAll(".scene-open").forEach((button) => {
  button.addEventListener("click", () => {
    if (!dialog || !dialogImage) return;
    const image = button.querySelector("img");
    if (!image) return;
    dialogOpener = button;
    dialogImage.src = image.src;
    dialogImage.alt = image.alt;
    dialog.showModal();
  });
});

if (dialog) {
  const close = dialog.querySelector(".dialog-close");
  close?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener("close", () => {
    dialogOpener?.focus?.();
  });
}

const tabs = [...document.querySelectorAll('[role="tab"]')];
function activateTab(tab) {
  tabs.forEach((candidate) => {
    const selected = candidate === tab;
    candidate.setAttribute("aria-selected", String(selected));
    candidate.tabIndex = selected ? 0 : -1;
    const panel = document.getElementById(candidate.getAttribute("aria-controls"));
    if (panel) panel.hidden = !selected;
  });
}
if (tabs.length) {
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activateTab(tab));
    tab.addEventListener("keydown", (event) => {
      const delta = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
      if (delta) {
        event.preventDefault();
        const next = tabs[(index + delta + tabs.length) % tabs.length];
        activateTab(next);
        next.focus();
      }
    });
  });
  activateTab(tabs.find((tab) => tab.getAttribute("aria-selected") === "true") || tabs[0]);
}

let observationTimer;
const request = document.getElementById("study-request");
const result = document.getElementById("study-result");
if (request && result) {
  request.addEventListener("click", () => {
    clearTimeout(observationTimer);
    const target = document.getElementById("study-target");
    const intent = document.getElementById("study-intent");
    const observedNode = document.getElementById("study-observed");
    const requested = target?.value.trim() || "";
    if (!requested) {
      result.textContent = "Enter a requested state";
      result.dataset.status = "observed";
      return;
    }
    if (intent) intent.textContent = requested;
    if (observedNode) observedNode.textContent = "off";
    const pending = projectState(requested, "off");
    result.textContent = pending.text;
    result.dataset.status = pending.status;
    observationTimer = setTimeout(() => {
      if (observedNode) observedNode.textContent = requested;
      const observed = projectState(requested, requested);
      result.textContent = observed.text;
      result.dataset.status = observed.status;
    }, 950);
  });
}
