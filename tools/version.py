"""The version authority: one value, every slot, one gate.

The package states its version in more than one place, and until now each of
those places was written by hand. That is how V3.4.2 shipped with a manifest
still announcing V3.4.0 and a web manifest still announcing V3.4.1: the two
files that were supposed to describe the release were themselves drifting
independently of it, and nothing in the gate chain noticed.

This module makes the version a single value with a single owner:

    VERSION                 the canonical value, one line, at the repository root
    core/rules.json         the version the test suite already treats as authoritative
    profiles/motion/*.json  the version the motion profile tracks
    references/*.json       the version each reference scene declares
    references/*.svg        the caption each reference sheet prints
    site/index.html         the six display slots of the public reference
    site/site.webmanifest   the name the installed web app carries
    manifest.json           the version and name of the package manifest

`--check` is a gate: it verifies the property, not a diff, and reports the
slot that disagrees rather than a patch. `--sync` writes the canonical value
into every slot. `--set` moves the canonical value and syncs it.

    python -m tools.version --check
    python -m tools.version --show
    python -m tools.version --sync
    python -m tools.version --set 3.5.0

Only mechanical slots are rewritten. Prose that names a past release ("V3.4.2
repairs the asset containers") is history, not a slot, and is left alone: the
patterns below are anchored on their surrounding markup so that a bare
version number in a sentence is never a candidate.

The package's public nomenclature prints the version with a leading zero
("3.4.2" is shown as "03.4.2"). That zero belongs to the slot's markup, not to
the version, so it is part of each pattern's prefix and is left alone by the
rewrite. The version itself is always captured as a plain semantic version.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

# The version as it is written. Captured out of every slot, plain, with no
# display decoration. Named groups, so that a slot pattern reads as
# prefix / version / suffix and cannot be renumbered by accident.
VERSION_PATTERN = r"(?P<ver>\d+\.\d+\.\d+)"


def public_form(version: str) -> str:
    """The version as the package prints it. Display only; never a slot value."""
    return "0" + version


# ---------------------------------------------------------------- JSON slots

def json_slots() -> list[tuple[str, str]]:
    """(relative path, dotted key path) for every JSON file that states a version."""
    slots = [("core/rules.json", "version"), ("profiles/motion/motion.json", "version")]
    for path in sorted((ROOT / "references").glob("*.json")):
        slots.append((f"references/{path.name}", "version"))
    return slots


def read_json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def write_json_slot(rel: str, key: str, version: str) -> None:
    """Set one key's value without re-encoding the rest of the file.

    These files are hashed into manifest.json and are read by consumers that
    compare them byte for byte, so re-serialising them to change one string
    is not acceptable: json.dumps would un-escape the non-ASCII characters
    the files currently carry, and the diff would show a change that has
    nothing to do with the version. The key is edited in place and the
    result is re-parsed to confirm the value landed where it was meant to.
    """
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r'("' + re.escape(key) + r'"\s*:\s*")(\d+\.\d+\.\d+)(")')
    updated, count = pattern.subn(lambda m: m.group(1) + version + m.group(3), text, count=1)
    if count == 0:
        raise SystemExit(f"{rel}: no {key} key to update")
    path.write_text(updated, encoding="utf-8")
    written = read_json(rel).get(key)
    if written != version:
        raise SystemExit(f"{rel}: {key} is {written!r} after the edit, expected {version!r}")


# --------------------------------------------------------------- text slots

# (relative path, regex, description)
#
# Each pattern is prefix + version + suffix, anchored on markup that only a
# slot can produce. A version in running prose has no such anchor, so it is
# not reachable from here.
TEXT_SLOTS: list[tuple[str, str, str]] = [
    ("site/index.html",
     r'(?P<pre><meta name="gnosix-contract-version" content=")' + VERSION_PATTERN + r'(?P<post>")',
     "the contract version the page declares"),
    ("site/index.html",
     r'(?P<pre><title>gnosix_DS 0)' + VERSION_PATTERN + r'(?P<post> — Portable visual reference</title>)',
     "the document title"),
    ("site/index.html",
     r'(?P<pre><span class="version">0)' + VERSION_PATTERN + r'(?P<post> / PORTABLE CONTRACT</span>)',
     "the version badge"),
    ("site/index.html",
     r'(?P<pre><span class="eyebrow">gnosix_DS / V)' + VERSION_PATTERN + r'(?P<post></span>)',
     "the hero eyebrow"),
    ("site/index.html",
     r'(?P<pre><code>0)' + VERSION_PATTERN + r'(?P<post> / 1440 / project://gnosix)',
     "the technical line"),
    ("site/index.html",
     r'(?P<pre><span>gnosix_DS / 0)' + VERSION_PATTERN + r'(?P<post> / portable contract</span>)',
     "the footer credit"),
    ("site/site.webmanifest",
     r'(?P<pre>"name": "gnosix_DS 0)' + VERSION_PATTERN + r'(?P<post> — Portable visual reference")',
     "the installed application name"),
]


def reference_svg_slots() -> list[tuple[str, str, str]]:
    slots = []
    for path in sorted((ROOT / "references").glob("*.svg")):
        slots.append((f"references/{path.name}",
                      r'(?P<pre>gnosix_DS 0)' + VERSION_PATTERN + r'(?P<post>\s+•)',
                      "the sheet caption"))
    return slots


def manifest_slots() -> list[tuple[str, str, str]]:
    return [
        ("manifest.json", r'(?P<pre>"version": ")' + VERSION_PATTERN + r'(?P<post>")', "the package version"),
        ("manifest.json", r'(?P<pre>"name": "gnosix_DS V)' + VERSION_PATTERN + r'(?P<post> )', "the package name"),
    ]


def all_text_slots() -> list[tuple[str, str, str]]:
    return TEXT_SLOTS + reference_svg_slots() + manifest_slots()


# ------------------------------------------------------------------ reading

def read_version() -> str:
    if not VERSION_FILE.exists():
        raise SystemExit("VERSION is missing; the version authority has no source")
    value = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not SEMVER.match(value):
        raise SystemExit(f"VERSION is not a semantic version: {value!r}")
    return value


def read_slot(rel: str, pattern: str) -> str | None:
    path = ROOT / rel
    if not path.exists():
        return None
    match = re.search(pattern, path.read_text(encoding="utf-8"))
    return match.group("ver") if match else None


def json_slot_value(rel: str, key: str) -> str | None:
    if not (ROOT / rel).exists():
        return None
    node = read_json(rel)
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return str(node) if node is not None else None


# ------------------------------------------------------------------ writing

def write_slot(rel: str, pattern: str, version: str) -> bool:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")

    def replace(match: re.Match) -> str:
        # The prefix carries the display zero where the slot has one; the
        # version is written plain.
        return match.group("pre") + version + match.group("post")

    updated, count = re.subn(pattern, replace, text)
    if count == 0:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def sync(version: str) -> list[str]:
    """Write `version` into every slot. Returns the slots that changed."""
    changed = []
    for rel, key in json_slots():
        data = read_json(rel)
        if data.get(key) == version:
            continue
        write_json_slot(rel, key, version)
        changed.append(f"{rel} ({key})")
    for rel, pattern, description in all_text_slots():
        if read_slot(rel, pattern) == version:
            continue
        if write_slot(rel, pattern, version):
            changed.append(f"{rel} ({description})")
    return changed


# -------------------------------------------------------------------- gates

def check(version: str) -> list[str]:
    """Verify the property. Returns a list of disagreements (empty means pass)."""
    problems: list[str] = []

    for rel, key in json_slots():
        actual = json_slot_value(rel, key)
        if actual is None:
            problems.append(f"{rel}: no {key} key")
        elif actual != version:
            problems.append(f"{rel}: {key} is {actual}, expected {version}")

    for rel, pattern, description in all_text_slots():
        actual = read_slot(rel, pattern)
        if actual is None:
            problems.append(f"{rel}: {description} not found")
        elif actual != version:
            problems.append(f"{rel}: {description} is {actual}, expected {version}")

    problems.extend(check_tag(version))
    return problems


def check_tag(version: str) -> list[str]:
    """A tagged commit must agree with VERSION.

    An untagged working tree is not a problem: the tag is created after the
    commit it names. But once a commit carries a tag, that tag and VERSION
    are two statements about the same state and may not disagree.
    """
    if not (ROOT / ".git").exists():
        return []
    try:
        described = subprocess.run(
            ["git", "describe", "--tags", "--exact-match", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=False)
    except OSError:
        return []
    if described.returncode != 0:
        return []
    tag = described.stdout.strip()
    expected = f"v{version}"
    if tag != expected:
        return [f"HEAD is tagged {tag}, but VERSION is {version} (expected tag {expected})"]
    return []


def head_tag() -> str | None:
    if not (ROOT / ".git").exists():
        return None
    described = subprocess.run(
        ["git", "describe", "--tags", "--exact-match", "HEAD"],
        cwd=ROOT, capture_output=True, text=True, check=False)
    return described.stdout.strip() if described.returncode == 0 else None


# --------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="the version authority")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="verify every slot agrees with VERSION")
    group.add_argument("--sync", action="store_true", help="write VERSION into every slot")
    group.add_argument("--set", dest="set_version", metavar="X.Y.Z", help="move VERSION and sync it")
    group.add_argument("--show", action="store_true", help="print the version and every slot")
    args = parser.parse_args(argv)

    if args.set_version:
        if not SEMVER.match(args.set_version):
            raise SystemExit(f"not a semantic version: {args.set_version!r}")
        VERSION_FILE.write_text(args.set_version + "\n", encoding="utf-8")
        changed = sync(args.set_version)
        print(f"VERSION -> {args.set_version}")
        for item in changed:
            print(f"  synced {item}")
        return 0

    version = read_version()

    if args.sync:
        changed = sync(version)
        if changed:
            for item in changed:
                print(f"  synced {item}")
        else:
            print(f"every slot already carries {version}")
        return 0

    if args.show:
        print(f"VERSION            {version}")
        print(f"public form        {public_form(version)}")
        tag = head_tag()
        print(f"HEAD tag           {tag or '(untagged)'}")
        print("slots:")
        for rel, key in json_slots():
            print(f"  {rel:34} {key:8} {json_slot_value(rel, key)}")
        for rel, pattern, description in all_text_slots():
            print(f"  {rel:34} {description:44} {read_slot(rel, pattern)}")
        return 0

    # --check, the default.
    problems = check(version)
    if problems:
        print(f"FAIL: {len(problems)} slot(s) disagree with VERSION {version}")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"PASS: every slot carries {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
