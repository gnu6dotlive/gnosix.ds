#!/usr/bin/env python3
"""Check that the field's vocabularies are translated in the contract.

The gnu6-design package carries a vocabulary of its own — the g6-*
classes — that the field uses and the system does not declare. The
contract translates it: each of its components is either one of the
system's own elements, a pattern the system states without declaring it
as an element, or a primitive the type, spacing or accessibility tier
governs.

Two things can go wrong and neither is visible by reading: a name the
package declares and the contract does not classify, and a classification
that names a component the contract does not have. So both are checked.

    python3 tools/check_vocabularies.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "packaging/gnu6-design/gnu6.css"
SPEC = ROOT / "core/COMPONENTS.json"

KIND = {"component", "pattern", "primitive"}


def main() -> int:
    if not SHEET.is_file():
        print(f"FAIL: {SHEET.relative_to(ROOT)} does not exist")
        return 1
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    declared = set(spec.get("components", {}))
    arrangements = set(spec.get("patterns", {})) | set(spec.get("primitives", {}))
    vocabularies = spec.get("vocabularies") or {}
    problems = []

    sheet = SHEET.read_text(encoding="utf-8")
    used = {m for m in re.findall(r"\.g6-([a-z-]+)", sheet)}
    base = {name.split("--")[0] for name in used}

    for name, vocabulary in vocabularies.items():
        if not isinstance(vocabulary, dict):
            continue
        entries = vocabulary.get("components") or {}
        # A vocabulary that names a package is checked against it, both
        # ways. A vocabulary that names no package — the native shell's,
        # which the field writes and does not vendored — is checked for its
        # shape only: there is nothing here to compare it with.
        vendored = "package" in vocabulary

        if vendored:
            # A component the contract classifies but the package does not
            # declare is a stale classification.
            for name in entries:
                if name not in base:
                    problems.append(f"{name}: the contract classifies it and "
                                    f"the package does not declare it")

            # A name the package declares that no classified component owns
            # is unclassified. A part belongs to the component that prefixes
            # it.
            for name in sorted(base):
                if name in entries:
                    continue
                if not any(name.startswith(owner + "-") for owner in entries):
                    problems.append(f"{name}: the package declares it and the "
                                    f"contract does not classify it")

        for name, entry in entries.items():
            kind = entry.get("is")
            if kind not in KIND:
                problems.append(f"{name}: classified as {kind!r}, which is "
                                f"not a component, a pattern or a primitive")
            elif kind == "component":
                target = entry.get("target")
                if target not in declared:
                    problems.append(f"{name}: names the component {target!r}, which "
                                    f"the contract does not declare")
            elif kind in ("pattern", "primitive"):
                # A name the field declares and the contract classifies as
                # an arrangement must be an arrangement the contract holds
                # — for a vocabulary that is vendored. A vocabulary nobody
                # vendored is a translation: it says what the field made,
                # and the system has not adopted it.
                if name not in arrangements and vendored:
                    problems.append(f"{name}: classified as a {kind}, which the "
                                    f"contract does not specify")
            else:
                problems.append(f"{name}: classified as {kind!r}, which is "
                                f"not a component, a pattern or a primitive")

    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the vocabularies")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    counts = {}
    for vocabulary in vocabularies.values():
        if not isinstance(vocabulary, dict):
            continue
        for entry in (vocabulary.get("components") or {}).values():
            counts[entry.get("is")] = counts.get(entry.get("is"), 0) + 1
    summary = ", ".join(f"{n} {kind}" for kind, n in sorted(counts.items()))
    print(f"PASS: every name the package declares is classified ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
