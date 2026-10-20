#!/usr/bin/env python3
"""Check that the gates stay inside the repository.

A gate that reads a file outside the repository is a gate the local
qualification cannot reproduce. The runner has the repository and the
pinned dependencies and nothing else; this machine has a home
directory, with other projects in it, and a gate that reaches into it
finds things the runner will not have. The local run passes, the runner
fails, and the run on the runner is a failure of method rather than of
the code.

So the tools may name no path outside the repository, with a short
allowlist for the system's own places: a temporary directory, a shell,
a device.

    python3 tools/check_containment.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNED = ("tools", "figcraft", "tests")

# The places a gate may name that are not the repository.
ALLOWED = (
    "/tmp", "/usr", "/dev", "/etc", "/proc", "/sys", "/bin", "/sbin",
    "/lib", "/lib64", "/run", "/var/tmp", "/var/log",
)

# The roots that belong to the machine and to nobody else. A path under
# one of them is a path the runner will not have.
MACHINE_ROOTS = ("/home", "/root", "/Users", "/mnt", "/media", "/srv",
                 "/opt", "/var/lib", "/var/cache")

# A literal that looks like a path, rather than a regular expression or a
# comment: it starts at the root, it has a second segment, and it has
# nothing in it that only a pattern would have.
META = set("*\\()[]{}?|+$^")

LITERAL = re.compile(r"""(['"])(/[^'"\n]*)\1""")
HOME_LITERAL = re.compile(r"""(['"])(~/[^'"\n]*)\1""")


def is_path(value: str) -> bool:
    if value.startswith("//"):
        return False
    if any(character in META for character in value):
        return False
    if value.rstrip("/") in MACHINE_ROOTS:
        return True
    return value.count("/") >= 2 and not value.endswith("/")


def source_files() -> list[Path]:
    files = []
    for entry in SCANNED:
        path = ROOT / entry
        if not path.is_dir():
            continue
        for child in sorted(path.rglob("*.py")):
            files.append(child)
    return files


def main() -> int:
    problems = []
    for path in source_files():
        # This file names the machine's roots on purpose: it is the list
        # of what a gate may not name.
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            for _, value in LITERAL.findall(line):
                if not is_path(value):
                    continue
                if any(value == allowed or value.startswith(allowed + "/")
                       for allowed in ALLOWED):
                    continue
                problems.append(
                    f"{path.relative_to(ROOT)}:{number}: names {value!r}, "
                    f"which is outside the repository")
            # A gate may take a path on the command line — that is the
            # user's choice — but it may not require one that is written
            # into its own source, in the machine's home. The projection's
            # tools are exempt: they are not packaged, and the engine
            # they look for is the one the workflow provisions.
            if path.parts[len(ROOT.parts)] != "figcraft":
                for _, value in HOME_LITERAL.findall(line):
                    problems.append(
                        f"{path.relative_to(ROOT)}:{number}: names {value!r}, "
                        f"which is a path in the machine's home")
    if problems:
        print(f"FAIL: {len(problems)} problem(s): the gates reach outside "
              f"the repository")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"PASS: the gates stay inside the repository "
          f"({len(source_files())} files scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
