#!/usr/bin/env python3
"""Specify the arrangements the field uses, measured from the sheet.

The gnu6-design package carries thirty-six arrangements that the field
uses and the system did not describe: twenty-nine patterns and seven
primitives. Until now the contract held their names and a sentence each.
That is a classification, not a specification, and a classification
cannot be wrong: it says only that a name is of a kind.

This tool reads the sheet and writes down what each arrangement *is* —
the parts it has, the tokens it consumes, the geometry it establishes,
the type it sets, the behaviour it has — so the contract holds an
account of the field's vocabulary instead of a list of names.

Nothing here is invented. Every declaration in the account is a
declaration in the sheet, and the tool checks both ways: a part the
contract names that the sheet does not have is a failure, and a
declaration in the sheet that the contract does not name is a failure.

    python3 tools/specify_components.py --write
    python3 tools/specify_components.py --check
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SHEET = ROOT / "packaging/gnu6-design/gnu6.css"
SPEC = ROOT / "core/COMPONENTS.json"
TOKENS = ROOT / "core/TOKENS.json"
SURFACES = ROOT / "core/SURFACES.json"

# The shape: how the arrangement is laid out and how big it is. These are
# the facts a reader can see.
GEOMETRY = {
    "display", "position", "top", "right", "bottom", "left", "inset",
    "inset-block", "inset-inline", "z-index",
    "width", "min-width", "max-width", "height", "min-height", "max-height",
    "inline-size", "min-inline-size", "max-inline-size", "block-size",
    "aspect-ratio", "box-sizing", "overflow", "overflow-x", "overflow-y",
    "overscroll-behavior", "padding", "padding-top", "padding-right",
    "padding-bottom", "padding-left", "padding-block", "padding-inline",
    "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "margin-block", "margin-inline",
    "border", "border-width", "border-style", "border-color", "border-radius",
    "border-top", "border-right", "border-bottom", "border-left",
    "border-top-width", "border-right-width", "border-bottom-width",
    "border-left-width", "border-top-style", "border-right-style",
    "border-bottom-style", "border-left-style",
    "border-collapse", "border-spacing",
    "flex", "flex-direction", "flex-wrap", "flex-grow", "flex-shrink",
    "flex-basis", "order", "gap", "row-gap", "column-gap",
    "grid", "grid-template", "grid-template-columns", "grid-template-rows",
    "grid-template-areas", "grid-area", "grid-column", "grid-row",
    "align-items", "align-content", "align-self", "justify-items",
    "justify-content", "justify-self", "place-items", "place-content",
    "place-self",
    "float", "clear", "object-fit", "object-position",
    "list-style", "list-style-type", "list-style-position",
    "table-layout", "vertical-align", "text-align", "text-indent",
    "transform", "transform-origin", "filter", "backdrop-filter",
    "mask-image", "box-shadow", "opacity", "mix-blend-mode",
    "clip", "clip-path", "container", "container-type", "container-name",
    "scrollbar-width", "scrollbar-color", "scroll-behavior",
    "cursor", "pointer-events", "user-select", "appearance", "outline",
    "outline-offset", "outline-width", "outline-style", "outline-color",
    "tab-size", "white-space", "word-break", "overflow-wrap", "hyphens",
    "text-wrap", "text-transform", "text-decoration", "text-decoration-color",
    "text-decoration-style", "text-decoration-thickness",
    "text-underline-offset", "text-underline-position",
    "text-shadow", "content", "counter-reset", "counter-increment",
    "animation", "animation-delay", "animation-duration",
    "animation-timing-function", "transition", "transition-delay",
    "transition-duration", "transition-property", "transition-timing-function",
    "forced-color-adjust", "print-color-adjust",
    "color", "background", "background-color", "background-image",
    "background-repeat", "background-position", "background-size",
    "background-clip", "background-origin",
    "font", "font-family", "font-size", "font-weight", "font-style",
    "font-variant", "font-variant-numeric", "font-feature-settings",
    "font-optical-sizing", "font-synthesis", "font-kerning",
    "font-size-adjust", "line-height", "letter-spacing", "text-rendering",
}

# Everything a declaration can be, when it is not a reference to a token
# and not a shape. The four buckets are: a reference (tokens), a shape
# (geometry), a type (type), and the rest (behaviour — motion, layers,
# effects, the form, and the accessibility rules).
TYPE = {
    "font", "font-family", "font-size", "font-weight", "font-style",
    "font-variant", "font-variant-numeric", "font-feature-settings",
    "font-optical-sizing", "font-synthesis", "font-kerning",
    "font-size-adjust", "line-height", "letter-spacing", "text-rendering",
    "text-transform", "text-decoration", "text-decoration-color",
    "text-decoration-style", "text-decoration-thickness",
    "text-underline-offset", "text-underline-position", "text-shadow",
    "vertical-align", "text-align", "text-indent", "tab-size",
    "white-space", "word-break", "overflow-wrap", "hyphens", "text-wrap",
    "text-size-adjust", "-webkit-font-smoothing",
}

COMMENT = re.compile(r"/\*.*?\*/", re.S)
CLASS_TOKEN = re.compile(r"\.([A-Za-z0-9_-]+)")
STATE_MARKER = re.compile(r"::?[a-zA-Z-]+|\[[a-zA-Z-]+")
VAR = re.compile(r"var\((--[a-z0-9-]+)\)")


def strip_comments(text: str) -> str:
    return COMMENT.sub("", text)


def parse_declarations(body: str) -> list[tuple[str, str]]:
    """The declarations of a block, in order, without their semicolons."""
    out = []
    for part in body.split(";"):
        if ":" not in part:
            continue
        prop, value = part.split(":", 1)
        prop = prop.strip()
        value = " ".join(value.split())
        if prop and value:
            out.append((prop, value))
    return out


def parse(text: str, at: tuple[str, ...] = ()) -> list[dict]:
    """The sheet as a list of rules, each with the at-rules it sits in."""
    out = []
    index = 0
    length = len(text)
    while index < length:
        brace = text.find("{", index)
        if brace == -1:
            break
        semi = text.find(";", index)
        if semi != -1 and semi < brace:
            index = semi + 1
            continue
        prelude = " ".join(text[index:brace].split())
        depth = 1
        cursor = brace + 1
        while cursor < length and depth:
            if text[cursor] == "{":
                depth += 1
            elif text[cursor] == "}":
                depth -= 1
            cursor += 1
        body = text[brace + 1:cursor - 1]
        if prelude.startswith("@"):
            out.extend(parse(body, at + (prelude,)))
        else:
            out.append({"at": list(at), "selector": prelude,
                        "declarations": parse_declarations(body)})
        index = cursor
    return out


def buckets(declarations: list[tuple[str, str]]) -> dict[str, dict[str, str]]:
    """The declarations of a rule, sorted into what they are."""
    out = {"tokens": {}, "geometry": {}, "type": {}, "behaviour": {}}
    for prop, value in declarations:
        if prop.startswith("--"):
            out["behaviour"][prop] = value
        elif VAR.search(value):
            out["tokens"][prop] = value
        elif prop in TYPE:
            out["type"][prop] = value
        elif prop in GEOMETRY:
            out["geometry"][prop] = value
        else:
            out["behaviour"][prop] = value
    return out


def sheet_rules() -> list[dict]:
    return parse(strip_comments(SHEET.read_text(encoding="utf-8")))


def class_tokens(selector: str) -> set[str]:
    """The class names a selector names, whole, and nothing else."""
    return set(CLASS_TOKEN.findall(selector))


def system_names() -> set[str]:
    """Every name the system publishes.

    A role is a published name as much as a layer is. The sheet binds its
    states to roles so that a state carries the step its substrate needs
    (COL-006); an arrangement whose state resolves through a role is
    naming vocabulary the system publishes, not a name it invents.
    """
    from project_tokens import layer_names, published_name, spacing_names, surface_names

    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    names = set(layer_names(tokens))
    names |= surface_names()
    names |= spacing_names(tokens)
    for role, weight in tokens["typography"]["weights"].items():
        names.add(f"--gnosix-weight-{role}")
    roles = json.loads((TOKENS.parent / "ROLES.json").read_text(encoding="utf-8"))
    for role in roles.get("roles", {}):
        names.add(published_name(role))
    return names


def sheet_semantics() -> dict[str, dict[str, str]]:
    """The sheet's own names, and what each resolves to per substrate.

    A semantic name is one the sheet's theme blocks declare: the surface
    it sits on, the rule it draws, the text it carries. A name an
    arrangement declares for itself is not a semantic; it is that
    arrangement's own, and the account says so.
    """
    out: dict[str, dict[str, str]] = {}
    for rule in sheet_rules():
        if not is_theme_rule(rule):
            continue
        substrate = "light" if any("light" in at for at in rule["at"]) else "dark"
        for prop, value in rule["declarations"]:
            if not prop.startswith("--g6-"):
                continue
            out.setdefault(prop, {})[substrate] = value
    return out


def is_theme_rule(rule: dict) -> bool:
    """Whether a rule is one of the sheet's theme blocks."""
    selector = rule["selector"]
    if selector == ":root":
        return True
    return "[data-g6-mode" in selector and "." not in selector


def account(rules: list[dict], name: str) -> dict:
    """The whole account of one arrangement: its rules, and what they are."""
    entries = []
    parts: set[str] = set()
    states: set[str] = set()
    tokens: set[str] = set()
    locals_: set[str] = set()
    token = f"g6-{name}"
    for rule in rules:
        tokens_in_rule = class_tokens(rule["selector"])
        # A rule belongs to the arrangement when it names the arrangement
        # itself or one of its parts: `.g6-doc` and `.g6-doc__nav` are the
        # same arrangement, seen at two levels.
        owned = [t for t in tokens_in_rule
                 if t == token or t.startswith(token + "__")]
        if not owned:
            continue
        for other in owned:
            if other.startswith(token + "__"):
                parts.add(other[len(token) + 2:])
        for marker in STATE_MARKER.findall(rule["selector"]):
            states.add(marker)
        sorted_buckets = buckets(rule["declarations"])
        for value in sorted_buckets["tokens"].values():
            for found in VAR.findall(value):
                tokens.add(found)
        for prop in sorted_buckets["behaviour"]:
            if prop.startswith("--"):
                locals_.add(prop)
        entries.append({
            "at": rule["at"],
            "selector": rule["selector"],
            "tokens": sorted_buckets["tokens"],
            "geometry": sorted_buckets["geometry"],
            "type": sorted_buckets["type"],
            "behaviour": sorted_buckets["behaviour"],
        })
    return {
        "parts": sorted(parts),
        "states": sorted(states),
        "tokens": sorted(tokens - locals_),
        "locals": sorted(locals_),
        "rules": entries,
    }


def derived(vocabulary: dict, rules: list[dict]) -> dict:
    """The account of every name the field declares, keyed by its name.

    The names the package publishes under the system's own elements are
    left out: their specification is the system's, and the projection gate
    holds the sheet to it. What is measured here is what the field wrote
    for itself.
    """
    out = {}
    for name, entry in vocabulary.items():
        kind = entry.get("is")
        if kind not in ("component", "pattern", "primitive"):
            continue
        if kind == "component" and entry.get("target") == name:
            continue
        out[name] = account(rules, name)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="specify the field's arrangements, measured from the sheet")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if not SHEET.is_file():
        print(f"FAIL: {SHEET.relative_to(ROOT)} does not exist")
        return 1
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    vocabulary = spec["vocabularies"]["gnu6-design"]["components"]
    rules = sheet_rules()
    measured = derived(vocabulary, rules)

    problems: list[str] = []

    # The tokens an arrangement names must exist: the sheet's own names
    # must be declared, and what they resolve to must be a name the system
    # publishes. A name the arrangement declares for itself is its own.
    published = system_names()
    semantics = sheet_semantics()
    for name, entry in measured.items():
        own = set(entry.get("locals", []))
        for token in entry["tokens"]:
            if token.startswith("--gnosix-"):
                if token not in published:
                    problems.append(f"{name}: names {token}, which the system "
                                    f"does not publish")
                continue
            if token not in semantics:
                problems.append(f"{name}: names {token}, which the sheet does "
                                f"not declare")
                continue
            for substrate, value in semantics[token].items():
                for found in VAR.findall(value):
                    if found not in published:
                        problems.append(
                            f"{name}: {token} resolves to {found} on the "
                            f"{substrate} substrate, which the system does "
                            f"not publish")
        for local in own:
            if local.startswith("--gnosix-"):
                problems.append(f"{name}: declares {local}, which is a name "
                                f"the system publishes; an arrangement does "
                                f"not declare the system's names")

    if args.write:
        counts = {"pattern": 0, "primitive": 0, "component": 0}
        for name, entry in measured.items():
            kind = vocabulary[name]["is"]
            counts[kind] = counts.get(kind, 0) + 1
            if kind == "component":
                # The field's own spelling of one of the system's elements.
                # It is the field's account of itself, and it lives in the
                # translation: the canonical name is the system's.
                vocabulary[name]["account"] = entry
                continue
            section = "patterns" if kind == "pattern" else "primitives"
            existing = spec.get(section, {}).get(name, {})
            meaning = existing.get("meaning") or vocabulary[name].get("note", "")
            spec.setdefault(section, {})[name] = {
                "kind": kind,
                "meaning": meaning,
                "parts": entry["parts"],
                "states": entry["states"],
                "tokens": entry["tokens"],
                "locals": entry["locals"],
                "rules": entry["rules"],
            }
        SPEC.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(f"WROTE: {counts['pattern']} patterns, {counts['primitive']} "
              f"primitives and {counts['component']} of the field's own "
              f"spellings specified, measured from the sheet")
        return 0

    if args.check:
        for section, kind in (("patterns", "pattern"), ("primitives", "primitive")):
            declared = spec.get(section, {})
            for name, entry in measured.items():
                if vocabulary[name]["is"] != kind:
                    continue
                if name not in declared:
                    problems.append(f"{name}: the contract does not specify it")
                    continue
                held = declared[name]
                for field in ("parts", "states", "tokens", "locals"):
                    if held.get(field) != entry[field]:
                        problems.append(
                            f"{name}: its {field} in the contract "
                            f"({held.get(field)}) are not the ones the sheet "
                            f"has ({entry[field]})")
                if held.get("rules") != entry["rules"]:
                    problems.append(f"{name}: its rules in the contract are not "
                                    f"the ones the sheet has")
        for name, entry in measured.items():
            if vocabulary[name]["is"] != "component":
                continue
            held = vocabulary[name].get("account")
            if held is None:
                problems.append(f"{name}: the contract does not account for "
                                f"the field's own spelling of it")
                continue
            for field in ("parts", "states", "tokens", "locals"):
                if held.get(field) != entry[field]:
                    problems.append(
                        f"{name}: its {field} in the contract "
                        f"({held.get(field)}) are not the ones the sheet "
                        f"has ({entry[field]})")
            if held.get("rules") != entry["rules"]:
                problems.append(f"{name}: its rules in the contract are not "
                                f"the ones the sheet has")

    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the arrangements")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    total = sum(len(e["rules"]) for e in measured.values())
    print(f"PASS: every arrangement is specified as the sheet has it "
          f"({len(measured)} arrangements, {total} rules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
