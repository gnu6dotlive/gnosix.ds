#!/usr/bin/env python3
"""Which components the field actually converges on.

The system declares four components and the ten frontends that use it
declare none of them, while each of them carries its own vocabulary: a
dozen widgets in one, thirty-nine in another, sixty classes in a third.
The system cannot absorb that by opinion. It has to find the components
that more than one independent frontend already agrees on, because those
are the ones a shared layer can actually carry, and it has to be able to
show the evidence for every one of them.

So this walks the frontends, collects the component names each one
declares, normalises them, and counts how many *independent repositories*
use each. A name used by one repository is that repository's own
vocabulary. A name used by three is a candidate for the shared layer, and
the count is the evidence.

    python3 tools/component_convergence.py --write
    python3 tools/component_convergence.py --check
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "profiles/frontend-audit.json"
OUT = ROOT / "profiles/frontend-audit"

SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".css", ".rs", ".astro", ".svelte", ".vue"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", "vendor", ".next", "out",
             "evidence", "legacy", "_ds", "uploads", "port-data", "vendor", "figcraft"}

# A component name, as the sources declare it.
REACT_EXPORT = re.compile(
    r"export\s+(?:default\s+)?(?:function|const|class|interface|type|enum)\s+([A-Z][A-Za-z0-9]*)")
REACT_DECL = re.compile(r"^\s*(?:export\s+)?(?:function|const|class)\s+([A-Z][A-Za-z0-9]*)", re.M)
RUST_TYPE = re.compile(r"pub\s+(?:struct|enum|trait)\s+([A-Z][A-Za-z0-9]*)")
CSS_CLASS = re.compile(r"\.([a-z][A-Za-z0-9]*(?:-[a-z0-9]+)+)")
Astro_FILE = re.compile(r"^.*?/([A-Z][A-Za-z0-9]*)\.astro$")

# The directories a component lives in. A name found in a global stylesheet
# or a utility file is a utility, not a component: the field's utility
# vocabulary is as large as its component vocabulary, and mixing the two
# would make the measurement meaningless.
COMPONENT_DIR = re.compile(
    r"(?:^|[-_])(components?|ui|widgets?|atoms?|molecules?|primitives?|"
    r"design-?system|shadcn)(?:[-_]|$)", re.I)

# A state modifier, not a component: the field writes these as classes and
# they are the same idea everywhere.
STATE_MODIFIER = re.compile(
    r"^(is|has|js)-|-(active|open|closed|disabled|enabled|selected|hover|focus|focus-visible|"
    r"active|expanded|collapsed|loading|visible|hidden|checked|invalid|valid|empty|error)$")

# Names that are not components: the vocabulary of the web platform, of the
# build, and of the design system itself.
NOT_COMPONENTS = {
    "import", "export", "default", "from", "require", "module", "function", "class",
    "const", "let", "var", "return", "if", "else", "for", "while", "switch", "case",
    "break", "continue", "new", "this", "super", "typeof", "instanceof", "void",
    "null", "undefined", "true", "false", "async", "await", "yield", "try", "catch",
    "finally", "throw", "type", "interface", "enum", "namespace", "declare",
    "component", "components", "main", "index", "app", "utils", "helpers", "config",
    "types", "constants", "styles", "test", "tests", "spec", "setup", "readme",
    "package", "public", "private", "protected", "static", "readonly", "abstract",
    "get", "set", "map", "filter", "reduce", "forEach", "push", "pop", "shift", "join",
    "split", "slice", "replace", "match", "test", "expect", "describe", "before",
    "after", "beforeeach", "aftereach", "it", "assert", "equals", "not", "throws",
    "error", "warning", "info", "debug", "trace", "log", "string", "number", "boolean",
    "object", "array", "json", "date", "math", "promise", "symbol", "bigint",
    "fn", "dyn", "impl", "use", "mod", "pub", "crate", "self", "super", "where",
    "async", "await", "move", "ref", "mut", "let", "const", "static", "unsafe",
    "extern", "match", "loop", "break", "continue", "macro_rules", "derive",
    "readme", "changelog", "license", "licence", "contributing", "codeowners",
    "html", "body", "head", "div", "span", "a", "img", "svg", "button", "input",
    "label", "form", "ul", "ol", "li", "p", "h1", "h2", "h3", "h4", "h5", "h6",
}


def words(name: str) -> list[str]:
    """A name, split into its words, whether it is camelCase or kebab-case."""
    if "-" in name:
        return [part for part in name.split("-") if part]
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).split()


def canonical(name: str) -> str:
    """The same name, in one spelling, so two repositories can be compared."""
    return "-".join(word.lower() for word in words(name))


def collect(root: Path, exclude: list[str] | None = None) -> set[str]:
    """The component names a frontend declares."""
    excluded = set(exclude or [])
    found: set[str] = set()

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if set(path.parts) & SKIP_DIRS:
            continue
        relative = path.relative_to(root)
        if any(str(relative).startswith(prefix) for prefix in excluded):
            continue

        # A component lives in a component's directory, or in a module
        # stylesheet, or in a file named after itself.
        in_component_dir = any(COMPONENT_DIR.search(part) for part in relative.parts[:-1])
        is_module = path.name.endswith(".module.css")
        stem = path.stem
        named_after_itself = stem and stem[0].isupper()

        text = ""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if path.suffix.lower() in (".ts", ".tsx", ".js", ".jsx", ".mjs"):
            if not (in_component_dir or named_after_itself):
                continue
            for match in REACT_EXPORT.finditer(text):
                found.add(match.group(1))
            for match in REACT_DECL.finditer(text):
                found.add(match.group(1))
        elif path.suffix.lower() == ".rs":
            if not in_component_dir:
                continue
            for match in RUST_TYPE.finditer(text):
                found.add(match.group(1))
        elif path.suffix.lower() == ".astro":
            match = Astro_FILE.match(str(relative))
            if match:
                found.add(match.group(1))

        # A stylesheet's class names are components only when they carry a
        # dash: a single word is a utility or an element, and the field's
        # utilities are as numerous as its components. And a stylesheet
        # counts only when it is a module or lives with the components.
        if path.suffix.lower() == ".css":
            if not (is_module or in_component_dir):
                continue
            for match in CSS_CLASS.finditer(text):
                found.add(match.group(1))

    out = set()
    for name in found:
        if name in NOT_COMPONENTS or len(name) < 3:
            continue
        key = canonical(name)
        if not key or key in NOT_COMPONENTS:
            continue
        if STATE_MODIFIER.search(key):
            continue
        out.add(key)
    return out


def convergence(entries: list[dict]) -> dict:
    """How many independent lineages use each name.

    A repository is not an opinion. gnu6-live and gnu6.live are two
    checkouts of one lineage, and the sheet they share is one artefact
    written once, so counting them twice would make one opinion look
    like an agreement. The count is over lineages.
    """
    by_name: dict[str, dict[str, list[str]]] = {}
    for entry in entries:
        root = Path(entry["path"]).expanduser()
        if not root.is_dir():
            continue
        lineage = entry.get("lineage", entry["name"])
        for name in collect(root, entry.get("exclude")):
            by_name.setdefault(name, {}).setdefault(lineage, []).append(entry["name"])
    return {name: {lineage: sorted(repos) for lineage, repos in lineages.items()}
            for name, lineages in sorted(by_name.items())}


def render_matrix(entries: list[dict], table: dict) -> str:
    out = ["# The convergence", "",
           "Which components more than one independent frontend already agrees on.",
           "A name one repository uses is that repository's vocabulary. A name three",
           "repositories use is a candidate for the shared layer, and the count is the",
           "evidence for it.", ""]
    for entry in entries:
        root = Path(entry["path"]).expanduser()
        if not root.is_dir():
            continue
        names = collect(root, entry.get("exclude"))
        out.append(f"## {entry['name']}")
        out.append("")
        out.append(f"{len(names)} distinct component names.")
        out.append("")
    return "\n".join(out)


def render_convergent(table: dict, minimum: int) -> str:
    rows = [(name, lineages) for name, lineages in table.items()
            if len(lineages) >= minimum]
    out = ["# The convergent components", "",
           f"Names used by at least {minimum} *independent lineages*, with the "
           "repositories that use them.", "",
           "A repository is not an opinion. gnu6-live and gnu6.live are two "
           "checkouts of one lineage, and the design sheet they share is one "
           "artefact written once, so both are excluded from the count and the "
           "count is over lineages.", "",
           "| component | lineages | repositories | count |",
           "|---|---|---|---|"]
    for name, lineages in sorted(rows, key=lambda kv: (-len(kv[1]), kv[0])):
        repos = sorted({r for rs in lineages.values() for r in rs})
        where = "; ".join(f"{lineage} ({', '.join(rs)})" for lineage, rs in sorted(lineages.items()))
        out.append(f"| `{name}` | {where} | {', '.join(repos)} | {len(lineages)} |")
    out.append("")
    out.append(f"{len(rows)} name(s) at or above the threshold, out of {len(table)} "
               "distinct names across the field.")
    out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="find the components the field converges on")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--minimum", type=int, default=2,
                        help="how many independent frontends a name must appear in")
    args = parser.parse_args(argv)

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    entries = config["frontends"]
    table = convergence(entries)

    files = {
        OUT / "CONVERGENCE.md": render_convergent(table, args.minimum),
    }

    if args.write:
        OUT.mkdir(parents=True, exist_ok=True)
        for path, text in files.items():
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
        return 0

    problems = []
    for path, text in files.items():
        if not path.is_file():
            problems.append(f"{path.relative_to(ROOT)} does not exist")
        elif path.read_text(encoding="utf-8") != text:
            problems.append(f"{path.relative_to(ROOT)} is out of date")
    if problems:
        print(f"FAIL: {len(problems)} report(s) out of date")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"PASS: the convergence report is current "
          f"({len(table)} distinct names)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
