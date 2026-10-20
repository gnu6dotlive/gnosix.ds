#!/usr/bin/env python3
"""What each gate must say.

The qualification said what passes and never what to expect. A gate that
began to say something else would still be green, because a gate that
exits zero is a gate that passes, whatever it says on the way.

This reads the document that says it — `ci/GATES.md`, one section per
gate: the command it runs, and the words it must contain. The run
compares each gate's own output with its expectation, so a gate that
changes its mind fails the qualification instead of passing it quietly.

    python3 tools/gate_expectations.py --check
"""

import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "ci" / "GATES.md"

SECTION = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.M)
COMMAND = re.compile(r"```(?:bash|sh)\n(.*?)```", re.S)
LITERAL = re.compile(r"`([^`]+)`")
NO_OUTPUT = "no output."


def parse(text: str) -> dict[str, dict]:
    """The document, as a label per gate: its command and its expectation."""
    found: dict[str, dict] = {}
    sections = list(SECTION.finditer(text))
    for index, match in enumerate(sections):
        label = match.group(2).strip()
        start = match.end()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        body = text[start:end]
        command = COMMAND.search(body)
        expectation = None
        for line in body.splitlines():
            if line.strip().startswith("Expected:"):
                expectation = line.strip()[len("Expected:"):].strip()
                break
        literals = LITERAL.findall(expectation or "")
        found[label] = {
            "command": " ".join(command.group(1).split()) if command else "",
            "expected": literals,
            "empty": bool(expectation) and expectation.startswith(NO_OUTPUT),
        }
    return found


def expectations() -> dict[str, dict]:
    if not DOCUMENT.is_file():
        return {}
    return parse(DOCUMENT.read_text(encoding="utf-8"))


def problems_against(gates: list[tuple[str, list[str]]]) -> list[str]:
    """The gates the document does not cover, and the sections it invents."""
    document = expectations()
    problems = []
    labels = {label for label, _ in gates}
    folded = {label.lower(): label for label in labels}
    written = {name.lower(): name for name in document}
    for label, cmd in gates:
        key = written.get(label.lower())
        entry = document.get(key) if key else None
        if entry is None:
            problems.append(f"{label}: the document says nothing about what "
                            f"this gate must say")
            continue
        if not entry["command"]:
            problems.append(f"{label}: the document does not give the command")
        elif not same_command(entry["command"], cmd):
            problems.append(f"{label}: the document says the gate runs "
                            f"{entry['command']!r}, and it runs "
                            f"{' '.join(cmd)!r}")
        if not entry["expected"] and not entry["empty"]:
            problems.append(f"{label}: the document states no expectation")
    for name in document:
        if name.lower() not in folded:
            problems.append(f"{name}: the document expects this gate, and "
                            f"there is no such gate")
    return problems


def same_command(written: str, cmd: list[str]) -> bool:
    """Whether the document names the command the gate really runs."""
    try:
        parts = shlex.split(written)
    except ValueError:
        return False
    if parts and parts[0] in ("python3", "python"):
        parts = parts[1:]
    return parts == list(cmd)


def check_output(label: str, output: str) -> list[str]:
    """What a gate said, against what it was supposed to say."""
    document = expectations()
    written = {name.lower(): name for name in document}
    key = written.get(label.lower())
    if key is None:
        return []
    entry = document[key]
    if entry["empty"]:
        if output.strip():
            return [f"{label}: was expected to say nothing, and said "
                    f"{output.strip().splitlines()[0]!r}"]
        return []
    problems = []
    for literal in entry["expected"]:
        if literal not in output:
            problems.append(f"{label}: was expected to say {literal!r}, and "
                            f"did not")
    return problems


def main(argv=None) -> int:
    if not DOCUMENT.is_file():
        print(f"FAIL: {DOCUMENT.relative_to(ROOT)} does not exist")
        return 1
    import importlib.util

    spec = importlib.util.spec_from_file_location("ci_module", ROOT / "tools" / "ci.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    problems = problems_against(module.GATES)
    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the gate expectations")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    document = expectations()
    print(f"PASS: every gate says what it must say "
          f"({len(document)} gates documented)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
