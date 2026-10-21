#!/usr/bin/env python3
"""Project the consultation suite: the system, looked up.

The contract is a set of records — roles, rules, components, states, the
owner's statements, the registers, and the field's standing — and until now
the only way to read one was to open the JSON. That is a way to *check* the
system, not a way to *consult* it.

This projects the records into one page: an index of everything, an entry
for everything, and a search that answers "what is this, what guarantees it,
who uses it, where does it stand". Everything it says comes from the
contract's own files; the page adds no fact of its own, and a gate holds it
to that.

    python3 tools/project_reference.py --write
    python3 tools/project_reference.py --check
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from project_roles import resolve  # noqa: E402

PAGE = ROOT / "site" / "reference.html"
SCRIPT = ROOT / "site" / "reference.js"

ROLES = ROOT / "core" / "ROLES.json"
RULES = ROOT / "core" / "rules.json"
COMPONENTS = ROOT / "core" / "COMPONENTS.json"
TOKENS = ROOT / "core" / "TOKENS.json"
SURFACES = ROOT / "core" / "SURFACES.json"
INTENT = ROOT / "core" / "INTENT.json"
DEVIATIONS = ROOT / "core" / "DEVIATIONS.json"
DERIVATIONS = ROOT / "core" / "DERIVATIONS.json"
RETRACTIONS = ROOT / "core" / "RETRACTIONS.json"
STATES = ROOT / "profiles" / "native" / "states.json"
MATRIX = ROOT / "profiles" / "frontend-audit" / "MATRIX.md"
VERSION = ROOT / "VERSION"
GUIDELINES = ("IDENTITY", "ACCESSIBILITY", "SEMANTICS", "MAPPING", "VISUAL", "ENVELOPE")

# The order the index reads in: the owner's statements first, because they
# are what the system is for; then the vocabulary; then the rules; then the
# things; then the field.
KINDS = ("goal", "invariant", "truth", "capability")
KIND_LABEL = {"goal": "Goal", "invariant": "Invariant", "truth": "Truth",
              "capability": "Capability"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def searchable(text) -> str:
    """The words an entry is found by: its text, without the markup."""
    return esc(re.sub(r"<[^>]+>", " ", str(text)).replace("&amp;", "&")).strip()


def anchor(*parts: str) -> str:
    return "-".join(part.lower().replace("_", "-") for part in parts)


def role_value(reference: str, tokens: dict, surfaces: dict) -> str:
    value = resolve(reference, tokens, surfaces)
    return value or reference


def render_intent(intent: dict) -> tuple[str, list[dict]]:
    """The owner's statements: goals, invariants, truths, capabilities."""
    body = []
    index = []
    statements = sorted(intent.get("statements", []),
                        key=lambda s: (KINDS.index(s["kind"]) if s["kind"] in KINDS else 9,
                                       s["id"]))
    for statement in statements:
        ident = statement["id"]
        kind = statement["kind"]
        index.append({"id": ident, "kind": KIND_LABEL.get(kind, kind),
                      "title": statement["what"][:70], "anchor": f"statement-{ident.lower()}"})
        rows = [f"<p class=\"what\">{esc(statement['what'])}</p>"]
        if statement.get("done_when"):
            rows.append(f"<p class=\"done\"><span>Reached when</span> {esc(statement['done_when'])}</p>")
        if statement.get("held_by"):
            rows.append(f"<p class=\"held\"><span>Held by</span> {esc(statement['held_by'])}</p>")
        if statement.get("evidence"):
            rows.append(f"<p class=\"evidence\"><span>Evidence</span> {esc(statement['evidence'])}</p>")
        if statement.get("where"):
            rows.append(f"<p class=\"evidence\"><span>Where</span> {esc(statement['where'])}</p>")
        rows.append(f"<p class=\"provenance\"><span>Provenance</span> {esc(statement['provenance'])}</p>")
        state = statement.get("state", "stated")
        carried = statement.get("carried_in", "not yet carried into a release")
        rows.append(f"<p class=\"state\"><span>State</span> {esc(state)} — {esc(carried)}</p>")
        body.append(
            f"<article class=\"entry\" data-search=\"{searchable(statement['what'])}\" "
            f"id=\"statement-{ident.lower()}\">"
            f"<h3><span class=\"tag tag-{kind}\">{esc(KIND_LABEL.get(kind, kind))}</span>"
            f"<code>{esc(ident)}</code></h3>" + "".join(rows) + "</article>")
    return "".join(body), index


def render_roles(roles: dict, tokens: dict, surfaces: dict) -> tuple[str, list[dict]]:
    body = []
    index = []
    for name, spec in roles["roles"].items():
        light = role_value(spec["light"], tokens, surfaces)
        dark = role_value(spec["dark"], tokens, surfaces)
        index.append({"id": name, "kind": "Role", "title": spec["meaning"][:70],
                      "anchor": f"role-{anchor(name)}"})
        rules = " ".join(f"<code>{esc(rule)}</code>" for rule in spec.get("rules", [])) or "—"
        carries = spec.get("carries", "—")
        body.append(
            f"<article class=\"entry\" data-search=\"{searchable(spec['meaning'])}\" "
            f"id=\"role-{anchor(name)}\">"
            f"<h3><code>{esc(name)}</code><span class=\"swatch\" "
            f"style=\"--light: {esc(light)}; --dark: {esc(dark)}\"></span></h3>"
            f"<p class=\"what\">{esc(spec['meaning'])}</p>"
            f"<p class=\"values\"><span>Light</span> <code>{esc(light)}</code>"
            f"<span>Dark</span> <code>{esc(dark)}</code>"
            f"<span>Carries</span> {esc(carries)}</p>"
            f"<p class=\"rules\"><span>Governed by</span> {rules}</p></article>")
    return "".join(body), index


def render_rules(rules: list) -> tuple[str, list[dict]]:
    body = []
    index = []
    for rule in sorted(rules, key=lambda r: r["id"]):
        index.append({"id": rule["id"], "kind": "Rule", "title": rule["statement"][:70],
                      "anchor": f"rule-{rule['id'].lower()}"})
        body.append(
            f"<article class=\"entry\" data-search=\"{searchable(rule['statement'])}\" "
            f"id=\"rule-{rule['id'].lower()}\">"
            f"<h3><code>{esc(rule['id'])}</code><span class=\"level level-{esc(rule['level'].lower().replace(' ', '-'))}\">"
            f"{esc(rule['level'])}</span><span class=\"domain\">{esc(rule.get('domain', ''))}</span></h3>"
            f"<p class=\"what\">{esc(rule['statement'])}</p>"
            f"<p class=\"observable\"><span>Observable</span> {esc(rule.get('observable', '—'))}</p>"
            f"<p class=\"evidence\"><span>Checked by</span> {esc(rule.get('test', '—'))}</p></article>")
    return "".join(body), index


def render_components(components: dict) -> tuple[str, list[dict]]:
    body = []
    index = []
    for name, spec in components.items():
        index.append({"id": name, "kind": "Component", "title": spec.get("description", "")[:70],
                      "anchor": f"component-{anchor(name)}"})
        roles = " ".join(f"<code>{esc(role)}</code>" for role in spec.get("roles", [])) or "—"
        rules = " ".join(f"<code>{esc(rule)}</code>" for rule in spec.get("rules", [])) or "—"
        states = ", ".join(state.get("name", "") for state in spec.get("states", [])) or "—"
        variants = "".join(
            f"<li><strong>{esc(variant['name'])}</strong> — {esc(variant.get('description', ''))}</li>"
            for variant in spec.get("variants", []))
        body.append(
            f"<article class=\"entry\" data-search=\"{searchable(spec.get('description', ''))}\" "
            f"id=\"component-{anchor(name)}\">"
            f"<h3><code>{esc(name)}</code></h3>"
            f"<p class=\"what\">{esc(spec.get('description', ''))}</p>"
            f"<p class=\"values\"><span>Roles</span> {roles}"
            f"<span>States</span> {esc(states)}</p>"
            f"<p class=\"rules\"><span>Governed by</span> {rules}</p>"
            + (f"<ul class=\"variants\">{variants}</ul>" if variants else "")
            + "</article>")
    return "".join(body), index


def render_states(states: list) -> tuple[str, list[dict]]:
    body = []
    index = []
    for state in states:
        index.append({"id": state["id"], "kind": "State", "title": state.get("meaning", "")[:70],
                      "anchor": f"state-{anchor(state['id'])}"})
        body.append(
            f"<article class=\"entry\" data-search=\"{searchable(state.get('meaning', ''))}\" "
            f"id=\"state-{anchor(state['id'])}\">"
            f"<h3><code>{esc(state['id'])}</code></h3>"
            f"<p class=\"what\">{esc(state.get('meaning', ''))}</p>"
            f"<p class=\"values\"><span>Role</span> {esc(state.get('role') or '—')}</p>"
            f"<p class=\"observable\"><span>Treatment</span> {esc(state.get('treatment', '—'))}</p>"
            f"<p class=\"evidence\"><span>Evidence</span> {esc(state.get('evidence', '—'))}</p></article>")
    return "".join(body), index


def render_guidelines() -> tuple[str, list[dict]]:
    body = []
    index = []
    for name in GUIDELINES:
        path = ROOT / "core" / f"{name}.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        title = ""
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        headings = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
        index.append({"id": name, "kind": "Guideline", "title": title[:70],
                      "anchor": f"guideline-{name.lower()}"})
        listed = "".join(f"<li>{esc(heading)}</li>" for heading in headings)
        body.append(
            f"<article class=\"entry\" data-search=\"{searchable(title)}\" "
            f"id=\"guideline-{name.lower()}\">"
            f"<h3><code>{esc(name)}</code></h3>"
            f"<p class=\"what\">{esc(title)}</p>"
            + (f"<ul class=\"variants\">{listed}</ul>" if listed else "")
            + f"<p class=\"evidence\"><span>Document</span> <a href=\"../core/{esc(name)}.md\">core/{esc(name)}.md</a></p>"
            + "</article>")
    return "".join(body), index


def render_field(matrix: str) -> tuple[str, list[dict]]:
    """The field's standing, as the audit measured it."""
    body = []
    index = []
    rows = [line for line in matrix.splitlines() if line.startswith("| ")]
    if len(rows) < 3:
        return "", index
    for line in rows[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 8:
            continue
        name = cells[0]
        index.append({"id": name, "kind": "Field", "title": f"{cells[3]} colours outside the contract",
                      "anchor": f"field-{anchor(name)}"})
        body.append(
            f"<article class=\"entry\" data-search=\"{searchable(name)}\" "
            f"id=\"field-{anchor(name)}\">"
            f"<h3><code>{esc(name)}</code></h3>"
            f"<p class=\"values\"><span>Colours out</span> {esc(cells[3])}"
            f"<span>Lengths out</span> {esc(cells[5])}"
            f"<span>In scale</span> {esc(cells[6])}"
            f"<span>Components</span> {esc(cells[7])}</p>"
            f"<p class=\"evidence\"><span>Inventory</span> "
            f"<a href=\"../profiles/frontend-audit/INVENTORY.md#{esc(anchor(name))}\">INVENTORY.md</a></p>"
            + "</article>")
    return "".join(body), index


def render_register(title: str, entries, kind: str) -> tuple[str, list[dict]]:
    body = []
    index = []
    if isinstance(entries, dict):
        # A register held as a map: the name is the identifier.
        entries = [dict(spec, id=name) for name, spec in entries.items()]
    for entry in entries:
        ident = entry.get("id", "")
        index.append({"id": ident, "kind": kind, "title": entry.get("what", "")[:70],
                      "anchor": f"{kind.lower()}-{ident.lower()}"})
        meta = []
        if entry.get("severity"):
            meta.append(f"<span>Severity</span> {esc(entry['severity'])}")
        if entry.get("state"):
            meta.append(f"<span>State</span> {esc(entry['state'])}")
        if entry.get("owner"):
            meta.append(f"<span>Owner</span> {esc(entry['owner'])}")
        if entry.get("closed_by"):
            meta.append(f"<span>Closed in</span> {esc(entry['closed_by'])}")
        if entry.get("floor"):
            meta.append(f"<span>Floor</span> {esc(entry['floor'])}")
        if entry.get("statement"):
            body_statement = entry["statement"]
        else:
            body_statement = entry.get("what", "")
        body.append(
            f"<article class=\"entry\" data-search=\"{searchable(body_statement)}\" "
            f"id=\"{kind.lower()}-{ident.lower()}\">"
            f"<h3><code>{esc(ident)}</code></h3>"
            f"<p class=\"what\">{esc(body_statement)}</p>"
            + (f"<p class=\"values\">{''.join(meta)}</p>" if meta else "")
            + "</article>")
    return f"<h3>{esc(title)}</h3>" + "".join(body), index


def render_page(sections: list[tuple[str, str, str]], index: list[dict], version: str) -> str:
    """The page: a header, a search, the index, and the sections."""
    rows = []
    for kind in sorted({entry["kind"] for entry in index}):
        entries = [entry for entry in index if entry["kind"] == kind]
        links = "".join(
            f"<li><a href=\"#{esc(entry['anchor'])}\"><code>{esc(entry['id'])}</code> "
            f"{esc(entry['title'])}</a></li>" for entry in entries)
        rows.append(f"<section class=\"index-group\"><h2>{esc(kind)}</h2><ul>{links}</ul></section>")

    body = []
    for ident, title, content in sections:
        body.append(f"<section class=\"block\" id=\"{esc(ident)}\"><h2>{esc(title)}</h2>{content}</section>")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="gnosix-contract-version" content="{esc(version)}">
  <title>gnosix_DS {esc(version)} — Consultation</title>
  <meta name="description" content="The gnosix design system, looked up: the owner's statements, the roles, the rules, the components, the states, the guidelines and the field's standing.">
  <link rel="stylesheet" href="../profiles/web/tokens.css">
  <link rel="stylesheet" href="../profiles/web/icons.css">
  <link rel="stylesheet" href="style.css">
  <link rel="stylesheet" href="reference.css">
  <script src="reference.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to the reference</a>
  <header class="site-head">
    <a class="brand" href="../site/index.html">
      <span class="brand-mark" aria-hidden="true"><img src="../assets/identity/gnosix-ds-mark.svg" alt=""></span>
      <span>gnosix<span class="brand-under">_DS</span></span>
    </a>
    <nav aria-label="Main sections">
      <a href="#intent">The owner</a>
      <a href="#roles">Roles</a>
      <a href="#rules">Rules</a>
      <a href="#components">Components</a>
      <a href="#states">States</a>
      <a href="#guidelines">Guidelines</a>
      <a href="#field">The field</a>
      <a href="#registers">Registers</a>
    </nav>
    <span class="version">{esc(version)} / CONSULTATION</span>
  </header>

  <main id="main">
    <section class="block" id="top">
      <div class="section-intro">
        <div><p class="ref-eyebrow">00 / LOOK IT UP</p><h1>The system, looked up.</h1></div>
        <p>Everything below is projected from the contract's own records. Nothing here is written
        by hand: the roles, the rules, the components, the states, the owner's statements and
        the field's standing are read from the files that hold them.</p>
      </div>
      <form class="search" role="search" onsubmit="return false;">
        <label for="q">Search the system</label>
        <input type="search" id="q" name="q" placeholder="a role, a rule, a component, a statement…"
               autocomplete="off" aria-describedby="q-count">
        <p id="q-count" class="q-count" role="status"></p>
      </form>
      <div class="index" id="index">
{chr(10).join(rows)}
      </div>
    </section>
{chr(10).join(body)}
  </main>

  <footer class="site-foot">
    <p>Projected from <code>core/</code> by <code>tools/project_reference.py</code>.
    The contract's own gate holds this page to the contract.</p>
  </footer>
</body>
</html>
"""


def render_script(index: list[dict]) -> str:
    payload = json.dumps(index, ensure_ascii=False, indent=1)
    return f"""// Generated from the contract's records by tools/project_reference.py.
const GNOSIX_INDEX = {payload};

const field = document.getElementById("q");
const count = document.getElementById("q-count");
const groups = Array.from(document.querySelectorAll(".index-group"));

const articles = Array.from(document.querySelectorAll("article.entry"));
const blocks = Array.from(document.querySelectorAll("section.block"));

function apply() {{
  const needle = (field?.value || "").trim().toLowerCase();
  let visible = 0;
  for (const group of groups) {{
    let shown = 0;
    for (const item of group.querySelectorAll("li")) {{
      const hit = !needle || item.textContent.toLowerCase().includes(needle);
      item.hidden = !hit;
      if (hit) shown += 1;
    }}
    group.hidden = shown === 0;
    visible += shown;
  }}
  // The entries themselves answer the search too: a lookup shows the
  // entries that carry the word, not only a list of them.
  for (const article of articles) {{
    const haystack = (article.dataset.search || article.textContent).toLowerCase();
    article.hidden = Boolean(needle) && !haystack.includes(needle);
  }}
  for (const block of blocks) {{
    if (block.id === "top" || block.id === "field") continue;
    const entries = block.querySelectorAll("article.entry");
    const shown = Array.from(entries).filter((entry) => !entry.hidden).length;
    block.hidden = Boolean(needle) && shown === 0;
  }}
  if (count) {{
    count.textContent = needle
      ? `${{visible}} of ${{GNOSIX_INDEX.length}} entries match "${{needle}}"`
      : `${{GNOSIX_INDEX.length}} entries`;
  }}
}}

field?.addEventListener("input", apply);
apply();
"""


def build() -> tuple[str, str]:
    roles = load(ROLES)
    rules = load(RULES)["rules"]
    components = load(COMPONENTS)["components"]
    tokens = load(TOKENS)
    surfaces = load(SURFACES)
    intent = load(INTENT)
    deviations = load(DEVIATIONS)["deviations"]
    derivations = load(DERIVATIONS).get("derivations", {})
    retractions = load(RETRACTIONS)["retractions"]
    states = load(STATES)["states"]
    matrix = MATRIX.read_text(encoding="utf-8")
    version = VERSION.read_text(encoding="utf-8").strip()

    index: list[dict] = []
    sections: list[tuple[str, str, str]] = []

    body, entries = render_intent(intent)
    index += entries
    sections.append(("intent", "What the owner stated", body))

    body, entries = render_roles(roles, tokens, surfaces)
    index += entries
    sections.append(("roles", "The roles", body))

    body, entries = render_rules(rules)
    index += entries
    sections.append(("rules", "The rules", body))

    body, entries = render_components(components)
    index += entries
    sections.append(("components", "The components", body))

    body, entries = render_states(states)
    index += entries
    sections.append(("states", "The states", body))

    body, entries = render_guidelines()
    index += entries
    sections.append(("guidelines", "The guidelines", body))

    body, entries = render_field(matrix)
    index += entries
    sections.append(("field", "Where the field stands", body))

    registers = []
    body, entries = render_register("The deviations", deviations, "Deviation")
    registers.append(body)
    index += entries
    body, entries = render_register("The derivations", derivations, "Derivation")
    registers.append(body)
    index += entries
    body, entries = render_register("The retractions", retractions, "Retraction")
    registers.append(body)
    index += entries
    sections.append(("registers", "The registers", "".join(registers)))

    return render_page(sections, index, version), render_script(index)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="project the consultation suite")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    page, script = build()
    outputs = {PAGE: page, SCRIPT: script}

    if args.write:
        for path, text in outputs.items():
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
        return 0

    for path, text in outputs.items():
        if not path.is_file():
            print(f"FAIL: {path.relative_to(ROOT)} does not exist")
            return 1
        if path.read_text(encoding="utf-8") != text:
            print(f"FAIL: {path.relative_to(ROOT)} is not what the contract projects")
            return 1

    print("PASS: the consultation suite is what the contract says")
    return 0


if __name__ == "__main__":
    sys.exit(main())
