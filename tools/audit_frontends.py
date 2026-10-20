#!/usr/bin/env python3
"""Audit the frontends that consume the design system.

The contract is a set of approved colours, one family, a spacing scale and
a layer of surfaces. Every frontend that uses the system is a place where
those can be honoured or not, and a place where a second palette can grow
next to the first.

This walks the frontends named in profiles/frontend-audit.json and reports
two things:

  the matrix     one row per frontend, one column per criterion: does it
                  load the tokens, does it use the family, does it stay
                  inside the palette, does it use the spacing scale, does
                  it use the components, and is its palette its own
  the inventory  every colour, family and length each frontend uses that
                  the contract does not sanction

The inventory is the point. The matrix says how far along a frontend is;
the inventory says exactly what it would have to change.

    python3 tools/audit_frontends.py --write
    python3 tools/audit_frontends.py --check
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "profiles/frontend-audit.json"
OUT = ROOT / "profiles/frontend-audit"

HEX = re.compile(r"(?<![#0-9A-Fa-f])#[0-9A-Fa-f]{6}\b")
# A native frontend writes its palette as 0xRRGGBB, or as the three bytes
# it is made of: Color32::from_rgb(0x0d, 0x12, 0x18).
HEX_RUST = re.compile(r"0x([0-9A-Fa-f]{6})\b")
HEX_BYTES = re.compile(
    r"(?:from_rgb|from_rgba_unmultiplied|from_rgb_premultiplied|rgb)\s*\(\s*"
    r"0x([0-9A-Fa-f]{2})\s*,\s*0x([0-9A-Fa-f]{2})\s*,\s*0x([0-9A-Fa-f]{2})")
HEX_SHORT = re.compile(r"(?<![#0-9A-Fa-f])#[0-9A-Fa-f]{3}\b")
GNOSIX_VAR = re.compile(r"--gnosix-[A-Za-z0-9-]+")
FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;}\n]+)", re.I)
FONT_NAME = re.compile(r"font-family\s*:\s*[\"']?([A-Za-z0-9 ]+)")
LENGTH = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)(px|rem|em)\b")
# Declarations whose lengths are not spacing: border widths, outline widths
# and radii. The spacing scale governs the space between things, and a
# one-pixel hairline is not a failure to use it.
NOT_SPACING = re.compile(r"(?:^|[;{])\s*(?:border|outline)[a-z-]*\s*:[^;}]*", re.I)
RADIUS = re.compile(r"(?:^|[;{])\s*[a-z-]*radius[a-z-]*\s*:[^;}]*", re.I)
# The families a declaration may name that are not a family.
NOT_A_FAMILY = {"var", "inherit", "initial", "unset", "revert", "none",
                 "system-ui", "sans-serif", "serif", "monospace", "ui-sans-serif"}

# The files worth reading for a frontend: its styles and its markup.
SOURCE_SUFFIXES = {".css", ".scss", ".html", ".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte",
                   ".rs", ".json", ".svg"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", "vendor", ".next", "out"}

# The criterion columns of the matrix.
CRITERIA = [
    ("tokens", "loads the token file"),
    ("family", "sets Space Grotesk"),
    ("palette", "stays inside the approved palette"),
    ("spacing", "uses the spacing scale"),
    ("components", "uses the declared components"),
]


def approved() -> dict:
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    colours = {value.upper() for ramp in tokens["color"].values() for value in ramp.values()}
    surfaces = json.loads((ROOT / "core/SURFACES.json").read_text(encoding="utf-8"))
    for spec in surfaces.get("families", {}).values():
        for step in spec["steps"]:
            colours.add(step["value"].upper())
    for accent in surfaces.get("accents", []):
        colours.add(accent["value"].upper())
    # typography holds family *stacks*; the contract family is the head of
    # each stack, and the generic fallbacks are not families of their own.
    generic = {"system-ui", "sans-serif", "serif", "monospace", "ui-sans-serif",
               "ui-serif", "ui-monospace", "inherit", "initial", "unset", "revert"}
    families = set()
    for key, value in tokens["typography"].items():
        if isinstance(value, list) and value and isinstance(value[0], str):
            head = value[0].strip()
            if head and head.lower() not in generic:
                families.add(head)
    spacing = set(tokens.get("spacing", {}).values())
    components = set(json.loads((ROOT / "core/COMPONENTS.json").read_text(encoding="utf-8"))["components"])
    return {"colours": colours, "families": families, "spacing": spacing,
            "components": components, "tokens": tokens}


def published_names() -> set[str]:
    """The names the design system actually publishes.

    Read from the published artefact rather than recomputed, because the
    point is what a consumer would find. A frontend that writes
    --gnosix-signalOrange-base is not using the system when the system
    publishes --gnosix-signal-orange-base, however similar they look.
    """
    path = ROOT / "profiles/web/tokens.css"
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    return set(GNOSIX_VAR.findall(text))


def source_files(root: Path, exclude: list[str] | None = None):
    """The files a frontend ships.

    A frontend that archives an earlier design keeps it in the repository,
    and an audit that reads the archive measures the wrong thing: it counts
    a corpus that no longer ships as if it were live. The excluded paths are
    named per frontend in the configuration.
    """
    excluded = set(exclude or [])
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if set(path.parts) & SKIP_DIRS:
            continue
        relative = path.relative_to(root)
        if any(str(relative).startswith(prefix) for prefix in excluded):
            continue
        yield path


def audit(entry: dict, contract: dict) -> dict:
    root = Path(entry["path"]).expanduser()
    result = {"name": entry["name"], "path": str(root), "present": root.is_dir(),
              "colours": {}, "families": {}, "lengths": {}, "token_vars": 0,
              "components": set(), "family_hits": {}, "files": 0, "gnosix_names": set()}
    if not result["present"]:
        return result

    for path in source_files(root, entry.get("exclude")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        result["files"] += 1
        found = [v.upper() for v in HEX.findall(text)]
        found += [("#" + h.upper()) for h in HEX_SHORT.findall(text)]
        found += ["#" + h.upper() for h in HEX_RUST.findall(text)]
        found += ["#" + "".join(h.upper() for h in triple)
                  for triple in HEX_BYTES.findall(text)]
        for value in found:
            result["colours"][value] = result["colours"].get(value, 0) + 1
        for match in FONT_NAME.finditer(text):
            name = match.group(1).strip()
            if name and name.lower() not in NOT_A_FAMILY:
                result["families"][name] = result["families"].get(name, 0) + 1
        spacing_text = RADIUS.sub(" ", NOT_SPACING.sub(" ", text))
        for match in LENGTH.finditer(spacing_text):
            value = float(match.group(1))
            unit = match.group(2)
            if unit in ("rem", "em"):
                value *= 16
            value = round(value, 2)
            result["lengths"][value] = result["lengths"].get(value, 0) + 1
        found = GNOSIX_VAR.findall(text)
        result["token_vars"] += len(found)
        result["gnosix_names"].update(found)
        # The family is counted by occurrence, not by the declaration: a
        # frontend may declare it behind its own custom property, and a
        # declaration-based count would miss it.
        for family in contract["families"]:
            result["family_hits"][family] = result["family_hits"].get(family, 0) + \
                text.count(family)
        for component in contract["components"]:
            if f"gnosix-{component}" in text:
                result["components"].add(component)
    return result


def outside(result: dict, contract: dict) -> dict:
    """What each frontend uses that the contract does not sanction."""
    colours = {c: n for c, n in result["colours"].items() if c not in contract["colours"]}
    families = {f: n for f, n in result["families"].items()
                if f not in contract["families"] and f.lower() not in
                {c.lower() for c in contract["families"]}}
    lengths = {v: n for v, n in result["lengths"].items() if v not in contract["spacing"]}
    return {"colours": colours, "families": families, "lengths": lengths}


def render_matrix(audits: list[dict], contract: dict) -> str:
    """One row per frontend, and the columns are the work list.

    The counts are the point: a frontend that uses 1258 colours the
    contract does not have has 1258 things to change, and a yes/no would
    have hidden the size of the job.
    """
    published = published_names()
    rows = []
    for result in audits:
        if not result["present"]:
            rows.append(f"| {result['name']} | *absent* | | | | | | |")
            continue
        extra = outside(result, contract)
        uses_family = any(n for n in result.get("family_hits", {}).values())
        total_lengths = sum(result["lengths"].values())
        in_scale = total_lengths - sum(extra["lengths"].values())
        share = f"{round(100 * in_scale / total_lengths)}%" if total_lengths else "—"
        names = result.get("gnosix_names", set())
        known = len(names & published)
        renamed = len(names) - known
        rows.append(
            f"| {result['name']} | "
            f"{len(names)} ({known} known, {renamed} unknown) | "
            f"{'yes' if uses_family else 'no'} | "
            f"**{len(extra['colours'])}** | "
            f"**{len(extra['families'])}** | "
            f"**{len(extra['lengths'])}** | "
            f"{share} | "
            f"{len(result['components'])}/{len(contract['components'])} |")
    head = ("| frontend | gnosix names | family | colours out | families out | "
            "lengths out | in scale | components |")
    rule = "|---|---|---|---|---|---|---|---|"
    return "\n".join([head, rule] + rows)


def render_inventory(audits: list[dict], contract: dict) -> str:
    out = ["# The inventory", "",
           "What each frontend uses that the contract does not sanction. This is the",
           "work list: a colour here is a colour the system does not have.", ""]
    for result in audits:
        if not result["present"]:
            out.append(f"## {result['name']}")
            out.append("")
            out.append(f"Not present at `{result['path']}`.")
            out.append("")
            continue
        extra = outside(result, contract)
        out.append(f"## {result['name']}")
        out.append("")
        out.append(f"Source at `{result['path']}` — {result['files']} files read.")
        out.append("")
        if extra["colours"]:
            listed = ", ".join(f"`{c}` ×{n}" for c, n in
                               sorted(extra["colours"].items(), key=lambda kv: -kv[1]))
            out.append(f"- **Colours outside the palette ({len(extra['colours'])}):** {listed}")
        else:
            out.append("- **Colours outside the palette:** none")
        unknown = sorted(result.get("gnosix_names", set()) - published_names())
        if unknown:
            listed = ", ".join(f"`{n}`" for n in unknown[:12])
            more = f" (+{len(unknown) - 12} more)" if len(unknown) > 12 else ""
            out.append(f"- **Names the system does not publish ({len(unknown)}):** {listed}{more}")
        else:
            out.append("- **Names the system does not publish:** none")
        if extra["families"]:
            listed = ", ".join(f"`{f}` ×{n}" for f, n in
                               sorted(extra["families"].items(), key=lambda kv: -kv[1])[:12])
            out.append(f"- **Font families outside the contract ({len(extra['families'])}):** {listed}")
        else:
            out.append("- **Font families outside the contract:** none")
        if extra["lengths"]:
            listed = ", ".join(f"{v:g}px ×{n}" for v, n in
                               sorted(extra["lengths"].items(), key=lambda kv: -kv[1])[:12])
            out.append(f"- **Lengths outside the spacing scale ({len(extra['lengths'])}):** {listed}")
        else:
            out.append("- **Lengths outside the spacing scale:** none")
        out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="audit the frontends")
    parser.add_argument("--write", action="store_true", help="write the matrix and the inventory")
    parser.add_argument("--check", action="store_true", help="verify they are current")
    args = parser.parse_args(argv)

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    contract = approved()
    audits = [audit(entry, contract) for entry in config["frontends"]]

    matrix = ("# The matrix\n\n"
              "One row per frontend, one column per criterion. The inventory that\n"
              "follows says what each one would have to change. The counts are the\n"
              "work list: a colour out is a colour the system does not have.\n\n"
              + render_matrix(audits, contract) + "\n")
    inventory = render_inventory(audits, contract)
    files = {OUT / "MATRIX.md": matrix, OUT / "INVENTORY.md": inventory}

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
    print(f"PASS: the matrix and the inventory are current ({len(audits)} frontends)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
