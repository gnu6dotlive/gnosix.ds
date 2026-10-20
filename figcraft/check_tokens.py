#!/usr/bin/env python3
"""Check that the FigCraft projection and the web projection agree.

The design system states its colours in two places: `core/TOKENS.json`, which
the package projects into `profiles/web/tokens.css`, and the variables of the
FigCraft projection. Those are two representations of one palette, and the
package's own gate only checks the first against the second.

This checks them against each other, so a colour that was changed in the
token source and not carried into the FigCraft variables is a failure and
not a surprise somebody finds in a rendered page.

The comparison is on **values**, with the names normalised, because the two
representations name the same token differently: the package writes
`--gnosix-neutral-anthracite` and the engine writes `--neutral-anthracite`.
A diff of the text would fail on two systems that agree, and pass on two
that do not.

    python3 figcraft/check_tokens.py
"""

import argparse
import json
import os
import re
import subprocess
import tempfile
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def normalise(name: str) -> str:
    """The name both representations agree on.

    The package prefixes its custom properties with "gnosix-" and writes
    them in kebab case; the engine writes the variable's own name. Stripping
    the prefix and the non-alphanumerics leaves the token itself.
    """
    name = name.lower()
    if name.startswith("gnosix-"):
        name = name[len("gnosix-"):]
    return re.sub(r"[^a-z0-9]", "", name)


def parse_css(text: str) -> dict[str, str]:
    """The custom properties in a stylesheet, keyed by their normalised name."""
    out = {}
    for match in re.finditer(r"--([A-Za-z0-9_-]+)\s*:\s*([^;]+);", text):
        name, value = match.group(1), match.group(2).strip()
        out[normalise(name)] = value
    return out


def run(cli: str, source: Path, project: Path) -> tuple[dict, list[dict], str]:
    """Ask the engine what the projection holds."""
    script = json.dumps({"command": "variable.export", "params": {"format": "css"}}) + "\n" \
        + json.dumps({"command": "style.list", "params": {"type": "text"}}) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as handle:
        handle.write(script)
        query = Path(handle.name)
    try:
        result = subprocess.run([cli, "run", str(query), "--in", str(project)], cwd=source,
                                capture_output=True, text=True, check=False)
    finally:
        query.unlink(missing_ok=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit("the engine refused the query")

    css = ""
    styles: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        step = json.loads(line)
        if not step.get("ok"):
            raise SystemExit(f"the engine refused a query: {step.get('error')}")
        payload = step.get("result", {})
        if isinstance(payload, list):
            # style.list answers with the list itself.
            styles = [item for item in payload if isinstance(item, dict)]
        elif isinstance(payload, dict):
            if isinstance(payload.get("text"), str) and "--" in payload["text"]:
                css = payload["text"]
            elif isinstance(payload.get("styles"), list):
                styles = payload["styles"]
    return parse_css(css), styles, css


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="check the two token projections against each other")
    parser.add_argument("--cli", default=os.environ.get("FIGCRAFT_CLI",
                                                        os.path.expanduser("~/.local/bin/figcraft-cli")))
    parser.add_argument("--project", default=str(REPO_ROOT / "figcraft" / "gnosix-ds.figcraft"))
    args = parser.parse_args(argv)

    package_css = (REPO_ROOT / "profiles/web/tokens.css").read_text(encoding="utf-8")
    package = parse_css(package_css)

    engine_css, text_styles, _ = run(args.cli, REPO_ROOT, Path(args.project))

    # Colours: the hex values on both sides.
    package_colours = {k: v for k, v in package.items() if HEX.match(v)}
    engine_colours = {k: v for k, v in engine_css.items() if HEX.match(v)}

    problems: list[str] = []

    for name, value in sorted(package_colours.items()):
        if name not in engine_colours:
            problems.append(f"{name}: the package has it ({value}), the projection does not")
        elif engine_colours[name].lower() != value.lower():
            problems.append(f"{name}: the package has {value}, the projection has {engine_colours[name]}")
    for name, value in sorted(engine_colours.items()):
        if name not in package_colours:
            problems.append(f"{name}: the projection has it ({value}), the package does not")

    # Weights: the package states them as numbers, and the projection carries
    # them as text styles named by the number.
    package_weights = {v for k, v in package.items() if k.startswith("weight") and v.isdigit()}
    engine_weights = set()
    for style in text_styles:
        match = re.search(r"(\d{3})$", str(style.get("name", "")))
        if match:
            engine_weights.add(match.group(1))
    for weight in sorted(package_weights):
        if weight not in engine_weights:
            problems.append(f"weight {weight}: the package has it, the projection has no text style for it")
    for weight in sorted(engine_weights):
        if weight not in package_weights:
            problems.append(f"weight {weight}: the projection has a text style for it, the package does not")

    if problems:
        print(f"FAIL: {len(problems)} disagreement(s) between the two token projections")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"PASS: the two projections agree on {len(package_colours)} colours "
          f"and {len(package_weights)} weights")
    return 0


if __name__ == "__main__":
    sys.exit(main())
