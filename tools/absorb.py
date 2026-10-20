#!/usr/bin/env python3
"""Absorb a consumer into the design system.

A consumer carries its own palette. The system says what a surface is
for, and the consumer has been choosing colours by hand, which is how a
stylesheet ends up with two hundred and fifty hardcoded hex values and
how a change of substrate becomes a manual job.

This does the mechanical half of the absorption: it finds the colours a
consumer uses that the system does not have, matches each of them to the
step of the system it is closest to, records the mapping, and rewrites
the consumer's sources to name the system instead of carrying the
literal.

What it will not do is decide. A colour whose nearest step is far away
is a design decision, and this leaves it alone and says so, because a
migration that silently changes what a product looks like is not a
migration. The threshold is the point at which the difference stops
being a rounding.

    python3 tools/absorb.py --consumer ../gnu6.live --report
    python3 tools/absorb.py --consumer ../gnu6.live --write
    python3 tools/absorb.py --consumer ../gnu6.live --check

The mapping is written to the consumer as gnosix.absorption.json, so the
decision is reviewable and the tool is repeatable rather than a one-off
hand edit. A consumer states which version of the system it honours in
gnosix.json.
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from oklch import hex_to_rgb, rgb_to_oklch  # noqa: E402
from consumer_check import (SOURCE_SUFFIXES, SKIP_DIRS, colour_forms,  # noqa: E402
                            colours_in, expand_hex, system_colours)

# How far a colour may be from the system and still be called the same
# colour. Beyond this the difference is a decision, not a rounding.
NEAR = 8.0

# A custom property is a CSS value. It is not a colour in an SVG
# presentation attribute, not a colour in a canvas, and not a colour in
# a computation. The tool therefore rewrites stylesheets, and reports the
# rest rather than breaking it.
CSS_SUFFIXES = {".css", ".scss"}

# A consumer may say that part of its tree is not the interface: a
# prototype that demonstrates something, a fixture that shows a data
# palette. The exemption is declared, with a reason, and it is reported.
EXEMPT_KEY = "exempt"


def oklch(value: str) -> tuple[float, float, float]:
    return rgb_to_oklch(hex_to_rgb(value))


def distance(first: str, second: str) -> float:
    """The distance between two colours, in a scale where hue counts.

    The hue of a colour with almost no chroma is noise rather than a
    direction, so the hue term is weighted by the chroma the two colours
    have. Without that, every near-grey of a consumer looks far from
    every near-grey of the system, and the measurement is worthless.
    """
    l1, c1, h1 = oklch(first)
    l2, c2, h2 = oklch(second)
    dh = min(abs(h1 - h2), 360 - abs(h1 - h2))
    weight = min(1.0, min(c1, c2) / 0.03)
    return (((l1 - l2) * 100) ** 2 + ((c1 - c2) * 100) ** 2
            + (dh * 0.7 * weight) ** 2) ** 0.5


def system_steps() -> dict[str, str]:
    """Every colour the system has, and the name it is published under."""
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    surfaces = json.loads((ROOT / "core/SURFACES.json").read_text(encoding="utf-8"))
    out = {}
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            name = "-".join(part.lower() for part in
                            re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", family).split())
            shade_name = "-".join(part.lower() for part in
                                  re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", shade).split())
            out["#" + value[1:].upper()] = f"--gnosix-{name}-{shade_name}"
    for spec in surfaces["families"].values():
        for step in spec["steps"]:
            out["#" + step["value"][1:].upper()] = f"--gnosix-{step['id']}"
    for accent in surfaces["accents"]:
        out["#" + accent["value"][1:].upper()] = f"--gnosix-{accent['id']}"
    return out


# The vocabulary, and the vocabulary only. The component stylesheet
# carries an icon import and a font face that resolve inside the system
# and not inside a consumer, so it is vendored only when the consumer
# says it has adopted the components.
VENDORED = ["tokens.css", "roles.css"]


def vendor(consumer: Path, where: str) -> list[str]:
    """Put the system's published web profiles inside the consumer.

    A consumer that names the system must have the system's names. The
    profiles are copied at a pinned version and a lock records what was
    copied and what it hashes to, so the consumer can prove which state
    of the system it is built against and a change to the system cannot
    change the consumer without the lock noticing.
    """
    import hashlib

    target = consumer / where
    target.mkdir(parents=True, exist_ok=True)
    written = []
    lock = []
    wanted = list(VENDORED)
    manifest = consumer / "gnosix.json"
    if manifest.is_file():
        try:
            document = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            document = {}
        if document.get("components") == "adopted":
            wanted.append("components.css")
    for name in wanted:
        source = ROOT / "profiles/web" / name
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        (target / name).write_text(text, encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        lock.append({"file": name, "sha256": digest, "bytes": len(text.encode("utf-8"))})
        written.append(str((target / name).relative_to(consumer)))
    document = {
        "schema": "gnosix_DS.lock.v1",
        "system": "gnosix.ds",
        "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "path": where,
        "files": lock,
        "note": "The system's published web profiles, copied at a pinned version. "
                "A change to the system changes this lock, and the lock is what says "
                "which state of the system the consumer is built against.",
    }
    (consumer / "gnosix.lock.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return written


def exempt_prefixes(consumer: Path) -> list[str]:
    """The paths a consumer declares as not being its interface."""
    manifest = consumer / "gnosix.json"
    if not manifest.is_file():
        return []
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    exempt = document.get(EXEMPT_KEY) or []
    return [item["path"] for item in exempt if isinstance(item, dict) and "path" in item]


def content_colours(consumer: Path) -> set[str]:
    """The colours a consumer declares as its own content palette.

    COL-004: a product may carry a palette for what it is showing. It
    has to declare it, and the declaration is what the check reads.
    """
    manifest = consumer / "gnosix.json"
    if not manifest.is_file():
        return set()
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    out = set()
    for item in document.get("content") or []:
        value = item.get("colour") if isinstance(item, dict) else item
        if isinstance(value, str) and value.startswith("#"):
            out.add(value.upper())
    return out


def collect(consumer: Path) -> dict[str, list[str]]:
    """The foreign colours a consumer uses, and the files that use them."""
    system = system_colours()
    content = content_colours(consumer)
    exempt = exempt_prefixes(consumer)
    found: dict[str, list[str]] = {}
    for path in sorted(consumer.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if set(path.parts) & SKIP_DIRS:
            continue
        relative = str(path.relative_to(consumer))
        if any(relative.startswith(prefix) for prefix in exempt):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for colour in colours_in(text):
            if colour in system or colour in content:
                continue
            files = found.setdefault(colour, [])
            if relative not in files:
                files.append(relative)
    return found


def forms_by_colour(consumer: Path, wanted: set[str]) -> dict[str, set[str]]:
    """The written forms of the colours that are to be replaced.

    A colour the consumer writes as oklch(16% 0.028 260) is replaced as
    that, not as a hex it never was.
    """
    out: dict[str, set[str]] = {}
    exempt = exempt_prefixes(consumer)
    for path in sorted(consumer.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if set(path.parts) & SKIP_DIRS:
            continue
        relative = str(path.relative_to(consumer))
        if any(relative.startswith(prefix) for prefix in exempt):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for form, (colour, alpha) in colour_forms(text).items():
            if colour in wanted:
                out.setdefault(colour, set()).add((form, alpha))
    return out


def build_mapping(consumer: Path) -> dict:
    """The mapping: every foreign colour, and the step it lands on."""
    steps = system_steps()
    foreign = collect(consumer)
    mapping = {}
    decisions = []
    for colour in sorted(foreign):
        best = min(steps, key=lambda s: distance(colour, s))
        gap = distance(colour, best)
        entry = {"to": steps[best], "distance": round(gap, 2),
                 "files": foreign[colour]}
        if gap < NEAR:
            mapping[colour] = entry
        else:
            decisions.append({"colour": colour, "nearest": steps[best],
                              "distance": round(gap, 2), "files": foreign[colour]})
    return {"near": mapping, "decisions": decisions}


def in_regex_literal(line: str, column: int) -> bool:
    """Whether a position in a line sits inside a regular expression.

    A substitution that lands inside one is not wrong - the colour it
    names is right - but the name it substitutes carries parentheses,
    and parentheses are group syntax in a regular expression. The tool
    cannot rewrite the author's regex for them, so it says where it
    happened and the author escapes it.
    """
    slashes = 0
    index = 0
    while index < column:
        character = line[index]
        if character == "\\":
            index += 2
            continue
        if character == "/":
            slashes += 1
        index += 1
    return slashes % 2 == 1


def apply_mapping(consumer: Path, mapping: dict) -> int:
    """Rewrite the consumer's sources to name the system.

    The exemptions are honoured here as they are in the measurement. A
    part of the tree that the consumer has declared to be an exhibit is
    not rewritten because a colour of it happens to appear in the
    interface as well.
    """
    changed = 0
    warned: list[str] = []
    elsewhere: list[str] = []
    forms = forms_by_colour(consumer, set(mapping))
    exempt = exempt_prefixes(consumer)
    for path in sorted(consumer.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if set(path.parts) & SKIP_DIRS:
            continue
        relative = str(path.relative_to(consumer))
        if any(relative.startswith(prefix) for prefix in exempt):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if path.suffix.lower() not in CSS_SUFFIXES:
            # Not a stylesheet: a colour here may be an SVG attribute, a
            # canvas fill or a computed value, and a custom property is
            # none of those. It is reported and left alone.
            for colour, entry in mapping.items():
                if re.search(r"(?<![#\w-])#" + colour[1:] + r"\b", text, re.IGNORECASE):
                    elsewhere.append(f"{relative}: {colour}")
            continue

        original = text
        for colour, entry in mapping.items():
            for form, alpha in sorted(forms.get(colour, set()),
                                      key=lambda item: len(item[0]), reverse=True):
                if alpha is None:
                    replacement = f"var({entry['to']})"
                else:
                    # A custom property carries no alpha, so a colour that
                    # had one is replaced by a mix against transparency.
                    replacement = (f"color-mix(in srgb, var({entry['to']}) "
                                   f"{round(alpha * 100)}%, transparent)")
                pattern = re.compile(re.escape(form), re.IGNORECASE)
                for match in list(pattern.finditer(text)):
                    line_start = text.rfind("\n", 0, match.start()) + 1
                    line = text[line_start:text.find("\n", match.start())]
                    column = match.start() - line_start
                    if in_regex_literal(line, column):
                        warned.append(f"{relative}: {colour} inside a regular expression")
                text = pattern.sub(replacement, text)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
    if warned:
        print("")
        print("These substitutions landed inside a regular expression. The name is")
        print("right, but parentheses are group syntax there: escape them.")
        for warning in warned[:10]:
            print(f"  - {warning}")
    if elsewhere:
        print("")
        print("These colours are outside a stylesheet and were left alone. A custom")
        print("property is not a colour in an SVG attribute, a canvas or a")
        print("computation; each of these is a decision about the consumer.")
        for item in elsewhere[:12]:
            print(f"  - {item}")
    return changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="absorb a consumer into the system")
    parser.add_argument("--consumer", required=True)
    parser.add_argument("--report", action="store_true", help="print the mapping")
    parser.add_argument("--write", action="store_true", help="rewrite the consumer")
    parser.add_argument("--vendor", action="store_true",
                        help="copy the system's published profiles into the consumer")
    parser.add_argument("--where", default="app/styles/gnosix",
                        help="where the vendored profiles go in the consumer")
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero when the consumer still carries foreign colours")
    args = parser.parse_args(argv)

    consumer = Path(args.consumer).expanduser().resolve()
    if not consumer.is_dir():
        print(f"there is no consumer at {consumer}")
        return 3

    result = build_mapping(consumer)
    near, decisions = result["near"], result["decisions"]
    total = sum(len(entry["files"]) for entry in near.values())
    print(f"# {consumer.name}")
    print("")
    print(f"- **{len(near)}** colour(s) map onto a step of the system "
          f"({total} file(s) affected)")
    print(f"- **{len(decisions)}** colour(s) are a decision and were left alone")

    if decisions:
        print("")
        print("| colour | nearest step | distance | files |")
        print("|---|---|---|---|")
        for decision in decisions:
            print(f"| `{decision['colour']}` | `{decision['nearest']}` | "
                  f"{decision['distance']} | {', '.join(decision['files'][:3])} |")

    if args.report:
        print("")
        print("| colour | becomes | distance |")
        print("|---|---|---|")
        for colour, entry in sorted(near.items()):
            print(f"| `{colour}` | `var({entry['to']})` | {entry['distance']} |")

    if args.vendor:
        written = vendor(consumer, args.where)
        print("")
        for name in written:
            print(f"vendored {name}")
        print(f"wrote {consumer / 'gnosix.lock.json'}")
        print(f"import it first: @import url(\"{args.where}/tokens.css\"); "
              f"@import url(\"{args.where}/roles.css\");")
        return 0

    if args.write:
        document = {
            "schema": "gnosix_DS.absorption.v1",
            "version": read_version(consumer),
            "note": "The mapping a consumer's colours landed on when it was absorbed. "
                    "A colour that is not here was a decision and was left alone.",
            "near": near,
            "decisions": decisions,
        }
        (consumer / "gnosix.absorption.json").write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        changed = apply_mapping(consumer, near)
        print(f"")
        print(f"wrote {consumer / 'gnosix.absorption.json'}")
        print(f"rewrote {changed} file(s)")
        return 0

    if args.check:
        remaining = collect(consumer)
        if remaining:
            print("")
            print(f"FAIL: {len(remaining)} colour(s) the consumer still carries "
                  "that the system does not have")
            for colour, files in sorted(remaining.items())[:10]:
                print(f"  - {colour} in {', '.join(files[:2])}")
            return 1
        print("")
        print("PASS: the consumer carries only what the system has")
    return 0


def read_version(consumer: Path) -> str | None:
    manifest = consumer / "gnosix.json"
    if not manifest.is_file():
        return None
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except json.JSONDecodeError:
        return None


if __name__ == "__main__":
    sys.exit(main())
