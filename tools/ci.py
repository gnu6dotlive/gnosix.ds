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
sys.path.insert(0, str(ROOT / "tools"))

import gate_expectations  # noqa: E402

# (label, argv) — the argv is run from the package root with this
# interpreter, so a gate behaves the same here and in CI.
GATES: list[tuple[str, list[str]]] = [
    ("tokens project cleanly", ["tools/project_tokens.py", "--check"]),
    ("the surface layer is derived", ["tools/surfaces.py", "--check"]),
    ("the contrast table measures what the palette says", ["tools/contrast.py", "--check"]),
    ("the token exports are current", ["tools/export_tokens.py", "--check"]),
    ("the role layer is bound to the contract", ["tools/project_roles.py", "--check"]),
    ("the component stylesheet is what the spec projects", ["tools/project_components.py", "--check"]),
    ("every colour is one of ours", ["tools/contract_colors.py"]),
    ("the surfaces use the system's colours", ["tools/apply_surfaces.py", "--check"]),
    ("version authority", ["tools/version.py", "--check"]),
    ("contract validates", ["tools/contract.py", "--validate", "."]),
    ("manifest matches the tree", ["tools/rebuild_manifest.py", "--check"]),
    ("alpha masters are straight", ["tools/rekey_alpha.py", "--check"]),
    ("mascot alpha is repaired", ["tools/repair_mascot_alpha.py", "--check"]),
    ("svg wrappers embed once", ["tools/rebuild_svg_wrappers.py", "--check"]),
    ("favicons are the right crop", ["tools/build_favicons.py", "--check"]),
    ("icon subset is vendored", ["tools/vendor_icons.py", "--check"]),
    ("no ad-hoc glyphs", ["tools/apply_icons.py", "--check"]),
    ("the FigCraft projection matches the source", ["figcraft/generate.py", "--check"]),
    ("the two token projections agree", ["figcraft/check_tokens.py"]),
    ("the web code matches the design", ["figcraft/handoff.py", "--board", "Web / Landing", "--check"]),
    ("the native profile compiles and its tests pass", ["tools/native_check.py"]),
    ("the gnu6-design package is what the contract cuts", ["tools/package_gnu6_design.py", "--check"]),
    ("every name the field declares is classified", ["tools/check_vocabularies.py"]),
    ("every arrangement is specified as the sheet has it", ["tools/specify_components.py", "--check"]),
    ("every gate says what it must say", ["tools/gate_expectations.py", "--check"]),
    ("the severity register is honest", ["tools/check_deviations.py"]),
    ("the gates stay inside the repository", ["tools/check_containment.py"]),
    ("the surfaces render as the system carries them", ["tools/eye.py"]),
]

# A gate may report that it could not run, rather than that it passed or
# failed. The FigCraft projection gate is the case: the projection is not
# part of the package, so a copy of the package has nothing to compare, and
# the comparison of the project itself needs a FigCraft CLI that a CI
# runner does not have. Exit code 3 is that third answer, and it is not a
# pass.
SKIP = 3

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

    results: list[tuple[str, str, float, str]] = []
    started = time.monotonic()

    for label, cmd in gates:
        began = time.monotonic()
        # A gate whose script is not in this copy of the package cannot run.
        # The FigCraft projection is not package content, so the package
        # itself has no projection to check; that is a skip, not a failure.
        if not (ROOT / cmd[0]).exists():
            results.append((label, "SKIP", time.monotonic() - began,
                            f"not present in this copy: {cmd[0]}"))
            print(f"SKIP  {label}  (not present in this copy)")
            continue
        code, output = run(cmd)
        elapsed = time.monotonic() - began
        if code == SKIP:
            verdict = "SKIP"
        elif code == 0:
            # A gate that passes is a gate that exits zero. It is also a
            # gate that says something, and what it says is written down
            # in ci/GATES.md: a gate that changes its mind fails the
            # qualification rather than passing it quietly.
            said = gate_expectations.check_output(label, output)
            if said:
                verdict = "FAIL"
                output = (output + "\n" + "\n".join(said)).strip()
            else:
                verdict = "PASS"
        else:
            verdict = "FAIL"
        results.append((label, verdict, elapsed, output))
        print(f"{verdict}  {label}  ({elapsed:.1f}s)")

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
        results.append(("test suite", "PASS" if ok else "FAIL", elapsed, output))
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
            results.append(("pytest", "PASS" if ok else "FAIL", elapsed, output))
            print(f"{'PASS' if ok else 'FAIL'}  pytest  ({elapsed:.1f}s)")

    failed = [(label, output) for label, verdict, _, output in results if verdict == "FAIL"]
    skipped = [(label, output) for label, verdict, _, output in results if verdict == "SKIP"]
    total = time.monotonic() - started

    print()
    if failed:
        print(f"FAIL: {len(failed)} of {len(results)} gates failed in {total:.1f}s")
        for label, output in failed:
            print()
            print(f"--- {label} ---")
            print(output[-4000:] if len(output) > 4000 else output)
        return 1

    for label, output in skipped:
        reason = output.splitlines()[0] if output else "no reason given"
        print(f"SKIP  {label}: {reason}")

    passed = len(results) - len(failed) - len(skipped)
    print(f"PASS: {passed} gates in {total:.1f}s"
          + (f" ({len(skipped)} skipped)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
