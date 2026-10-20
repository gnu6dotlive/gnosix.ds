#!/usr/bin/env python3
"""Check that the work's own places are inside the repository.

The local worker contract says the work happens in the repository: every
tool, engine, browser and cache the work needs lives under a directory
the repository ignores, and `/tmp` is for what is genuinely disposable
and small.

That is a rule about where the work is, and a rule about where the work
is is worth exactly as much as the check that holds it. This check
reads the three places where the location is decided — the simulation's
work directory, the engine's cache and the browser's cache — and fails
when one of them points outside the repository.

    python3 tools/check_workplace.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP = 3

SIMULATION = ROOT / "ci" / "local-ci.sh"
PROVISIONING = (ROOT / "ci" / "provision-engine.sh",
                 ROOT / "ci" / "provision-browser.sh")


def work_line(text: str) -> str:
    """The line that says where the work goes."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("WORK="):
            return stripped
    return ""


def main() -> int:
    problems = []
    # The local simulation is not package content: a copy of the package
    # does not do the work, it receives it. Where the work's own places
    # are not written down, there is nothing to hold.
    if not SIMULATION.is_file():
        print("SKIP: this copy carries no local simulation, so the work's "
              "places are not written down here")
        return SKIP

    # The simulation's work directory: the clone, the engine, the browser.
    line = work_line(SIMULATION.read_text(encoding="utf-8"))
    if not line:
        problems.append("the simulation does not say where its work directory "
                        "is; it must be inside the repository")
    elif "REPO" not in line or ".ci-cache" not in line:
        problems.append(f"the simulation's work directory is {line!r}, which is "
                        f"not the repository's own cache")

    # The provisioning scripts: where the engine and the browser go.
    for path in PROVISIONING:
        if not path.is_file():
            print(f"SKIP: this copy carries no {path.name}, so the work's "
                  f"places are not written down here")
            return SKIP
        line = work_line(path.read_text(encoding="utf-8"))
        if not line:
            problems.append(f"{path.relative_to(ROOT)} does not say where its "
                            f"work directory is")
            continue
        if ".ci-cache" not in line:
            problems.append(
                f"{path.relative_to(ROOT)} fills {line!r}, which is not the "
                f"repository's own cache")

    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the workplace")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("PASS: the work's own places are inside the repository")
    return 0


if __name__ == "__main__":
    sys.exit(main())
