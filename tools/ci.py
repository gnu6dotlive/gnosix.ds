"""The qualification contract: one command, every gate, one verdict.

Every gate this package has is a read-only check that reports the property it
verifies. They were documented as a list of ten commands, which meant a
developer and CI could each run a different subset, in a different order, and
a missing gate was indistinguishable from a passing one. The list grew a gate
(the version authority) and the risk grew with it.

This module is that list, in one place, executed by one command:

    python -m tools.ci

It is the same command a developer runs before committing and the same
command CI runs. The YAML in .github/workflows exists to provision an
environment and then get out of the way; the qualification contract lives
here, in the repository, where a human and an agent run exactly the same
thing. Reproducing the check list in the workflow is how local truth and CI
truth drift apart: it is a second implementation of the same contract, and the
second one is the one nobody runs locally.

Gates run in order and every gate runs, even after one fails: an independent
failure should not hide behind an earlier one. The verdict is the summary,
and the exit status is the summary's verdict too.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (label, argv) — the argv is run from the package root with this
# interpreter, so a gate behaves the same here and in CI.
GATES: list[tuple[str, list[str]]] = [
    ("tokens project cleanly", ["tools/project_tokens.py", "--check"]),
    ("version authority", ["tools/version.py", "--check"]),
    ("contract validates", ["tools/contract.py", "--validate", "."]),
    ("manifest matches the tree", ["tools/rebuild_manifest.py", "--check"]),
    ("alpha masters are straight", ["tools/rekey_alpha.py", "--check"]),
    ("mascot alpha is repaired", ["tools/repair_mascot_alpha.py", "--check"]),
    ("svg wrappers embed once", ["tools/rebuild_svg_wrappers.py", "--check"]),
    ("favicons are the right crop", ["tools/build_favicons.py", "--check"]),
    ("icon subset is vendored", ["tools/vendor_icons.py", "--check"]),
    ("no ad-hoc glyphs", ["tools/apply_icons.py", "--check"]),
]

# The suite runs on the standard library so that qualification never depends
# on a package that is not installed. pytest is run as well when it is
# available, because it is what most readers reach for first, and its
# collection order exposes failures unittest's alphabetical order can hide.
TEST_SUITE = ["-m", "unittest", "discover", "-s", "tests"]


def run(argv: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, *argv],
        cwd=ROOT, capture_output=True, text=True, check=False)
    return result.returncode, (result.stdout + result.stderr).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="the qualification contract")
    parser.add_argument("--only", help="run only the gate whose label contains this")
    parser.add_argument("--gates-only", action="store_true",
                        help="run the gates without the test suite")
    args = parser.parse_args(argv)

    gates = GATES
    if args.only:
        gates = [(label, cmd) for label, cmd in GATES if args.only in label]

    results: list[tuple[str, bool, float, str]] = []
    started = time.monotonic()

    for label, cmd in gates:
        began = time.monotonic()
        code, output = run(cmd)
        elapsed = time.monotonic() - began
        ok = code == 0
        results.append((label, ok, elapsed, output))
        print(f"{'PASS' if ok else 'FAIL'}  {label}  ({elapsed:.1f}s)")

    # --gates-only exists so that the gates can be run without the test
    # suite. The suite contains a test that extracts the distributable
    # archive and qualifies it; qualifying it runs the suite again, which
    # runs that test again. The gates are the part of the contract that can
    # be checked in a package without recursing.
    if not args.gates_only:
        began = time.monotonic()
        code, output = run(TEST_SUITE)
        elapsed = time.monotonic() - began
        ok = code == 0
        results.append(("test suite", ok, elapsed, output))
        print(f"{'PASS' if ok else 'FAIL'}  test suite  ({elapsed:.1f}s)")

    if not args.only and not args.gates_only:
        try:
            import pytest  # noqa: F401
        except ImportError:
            print("SKIP  pytest (not installed; the standard-library suite ran)")
        else:
            began = time.monotonic()
            code, output = run(["-m", "pytest", "-q"])
            elapsed = time.monotonic() - began
            ok = code == 0
            results.append(("pytest", ok, elapsed, output))
            print(f"{'PASS' if ok else 'FAIL'}  pytest  ({elapsed:.1f}s)")

    failed = [(label, output) for label, ok, _, output in results if not ok]
    total = time.monotonic() - started

    print()
    if failed:
        print(f"FAIL: {len(failed)} of {len(results)} gates failed in {total:.1f}s")
        for label, output in failed:
            print()
            print(f"--- {label} ---")
            print(output[-4000:] if len(output) > 4000 else output)
        return 1

    print(f"PASS: {len(results)} gates in {total:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
