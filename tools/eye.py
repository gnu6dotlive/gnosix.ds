#!/usr/bin/env python3
"""The eye: the system's own surfaces, rendered and looked at.

The qualification says what the contract holds. It does not say what the
contract *looks like*: that a badge carries its condition as a shape and
a word, that a focus ring is visible, that a text reads on its ground.
Those are facts about pixels, and a fact about pixels has to be looked
at.

So the eye renders the system's own web surfaces, walks them with axe,
and compares the pictures with the ones the system carries.

Three answers, and the third is not a failure:

  pass    the findings are the ones the system knows, and the pictures
          are the ones the system carries;
  fail    a new accessibility finding, or a surface that moved;
  skip    the browser is not provisioned here, so there is nothing to
          look at with. A copy of the package has no browser, and the
          browser is not part of the package.

    python3 tools/eye.py
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EYE = ROOT / "qa" / "eye"
SCRIPT = EYE / "audit.mjs"
EXPECTED = EYE / "expected.json"
BASELINES = EYE / "baselines"
NODE_MODULES = EYE / "node_modules"

SKIP = 3


def provisioned() -> bool:
    """Whether the browser is here to look with.

    The browser is not part of the package, and the package is what a
    consumer receives. So the question is not whether the eye can run
    but whether anybody looked: a machine with the browser answers.
    """
    if not NODE_MODULES.is_dir():
        return False
    if not shutil.which("node"):
        return False
    home = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if home and Path(home).is_dir():
        return True
    cache = Path.home() / ".cache" / "ms-playwright"
    return cache.is_dir() and any(cache.iterdir())


def load_expected() -> dict:
    if not EXPECTED.is_file():
        return {"surfaces": {}, "findings": []}
    return json.loads(EXPECTED.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="render the surfaces and look at them")
    parser.add_argument("--write", action="store_true",
                        help="record the current surfaces as the ones the system carries")
    args = parser.parse_args(argv)

    if not SCRIPT.is_file():
        print(f"FAIL: {SCRIPT.relative_to(ROOT)} does not exist")
        return 1
    if not provisioned():
        print("SKIP: the eye has no browser to look with "
              "(run ci/provision-browser.sh)")
        return SKIP

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        result = subprocess.run(
            ["node", str(SCRIPT), "--out", str(out)],
            cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print("FAIL: the surfaces did not render")
            print((result.stdout + result.stderr)[-3000:])
            return 1
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))

        if args.write:
            BASELINES.mkdir(parents=True, exist_ok=True)
            for surface in report["surfaces"]:
                name = Path(surface["file"]).name
                shutil.copyfile(out / name, BASELINES / name)
            EXPECTED.write_text(json.dumps({
                "note": "The accessibility findings the system knows. A finding "
                        "that is not in this list is a new one, and the eye "
                        "fails on it.",
                "findings": report["findings"],
                "surfaces": {s["name"]: s["sha256"] for s in report["surfaces"]},
            }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"WROTE: {len(report['surfaces'])} surfaces recorded, "
                  f"{len(report['findings'])} findings")
            return 0

        expected = load_expected()
        problems = []

        # The findings are a ratchet: what the system knows, and no more.
        known = {(f["surface"], f["id"], f["impact"]) for f in expected.get("findings", [])}
        for finding in report["findings"]:
            key = (finding["surface"], finding["id"], finding["impact"])
            if key not in known:
                problems.append(
                    f"{finding['surface']}: a new accessibility finding — "
                    f"{finding['id']} ({finding['impact']}): {finding['help']}")
        for key in sorted(known):
            if key not in {(f["surface"], f["id"], f["impact"])
                           for f in report["findings"]}:
                problems.append(f"{key[0]}: the finding {key[1]} is gone")

        # The pictures are the ones the system carries.
        for surface in report["surfaces"]:
            name = Path(surface["file"]).name
            baseline = BASELINES / name
            if not baseline.is_file():
                problems.append(f"{surface['name']}: the system carries no "
                                f"picture of this surface")
                continue
            if baseline.read_bytes() != (out / name).read_bytes():
                problems.append(
                    f"{surface['name']}: the surface moved (the picture the "
                    f"system carries is {baseline.stat().st_size} bytes, the "
                    f"one rendered here is {surface['bytes']})")

        if problems:
            print(f"FAIL: {len(problems)} problem(s) with the eye")
            for problem in problems:
                print(f"  - {problem}")
            return 1

        print(f"PASS: the surfaces render as the system carries them "
              f"({len(report['surfaces'])} surfaces, "
              f"{len(report['findings'])} findings)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
