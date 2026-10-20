"""COL-001, made executable.

The rule says: "Read exact approved colors from core/TOKENS.json and
generate platform projections from it." Nothing checked it, and the
package's own public reference broke it in ninety-four places with
fifty-nine colours the contract never stated.

This is that check. Every colour in the package must be one of:

  - an approved token, from core/TOKENS.json;
  - a step of the surface layer, from core/SURFACES.json;
  - a declared accent, from the same file.

Anything else is a colour the system does not have. A file that needs one
has to say which token it means, in the file.

    python3 tools/contract_colors.py
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "core/TOKENS.json"
SURFACES = ROOT / "core/SURFACES.json"

HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")

# Where a colour may legitimately appear. The manifest is excluded because it
# holds the hashes, not colours.
#
# The frontend audit is excluded for the same kind of reason as the FigCraft
# projection: it is a report *about* the colours the system does not have. The
# inventory quotes them in order to name them, and a gate that asked a
# quotation to be a token would forbid the report that says where the system
# is not yet used.
# The adopted legacy vocabulary is exempt because it is a record: it is
# the sheet as it was, kept so that the re-cut can be read against what
# it replaced. It quotes the colours the system does not have because
# that is what it was. The re-cut beside it carries none, and the gate
# examines the re-cut like any other part of the tree.
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "dist", "handoff", "figcraft",
             "frontend-audit", "legacy"}
# The audit's configuration quotes the same colours its reports do, and is
# exempt for the same reason.
SKIP_FILES = {"frontend-audit.json"}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ttf", ".woff2", ".ico", ".zip"}

# The assets tree is artwork, not surface. A flag carries its country's
# colours and an identity master carries its own; neither is a surface of
# the system, and the gate would only ever ask a drawing to be a token.
SKIP_TREES = {"assets"}


def allowed() -> dict[str, str]:
    """Every colour the system has, and where it came from."""
    out: dict[str, str] = {}
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            out[value.upper()] = f"token {family}/{shade}"
    surfaces = json.loads(SURFACES.read_text(encoding="utf-8"))
    for family, spec in surfaces.get("families", {}).items():
        for step in spec.get("steps", []):
            out[step["value"].upper()] = f"surface {step['id']}"
    for accent in surfaces.get("accents", []):
        out[accent["value"].upper()] = f"accent {accent['id']}"
    # A merged tint is the same colour under another name, and the layer
    # says so; it is sanctioned by the colour it was merged into.
    for family, spec in surfaces.get("families", {}).items():
        for step in spec.get("steps", []):
            for alias in step.get("aliases", []):
                out[alias.upper()] = f"surface {step['id']} (merged)"
    for accent in surfaces.get("accents", []):
        for alias in accent.get("aliases", []):
            out[alias.upper()] = f"accent {accent['id']} (merged)"
    return out


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if set(rel.parts) & SKIP_DIRS:
            continue
        if set(rel.parts) & SKIP_TREES:
            continue
        if path.suffix.lower() in SKIP_SUFFIX:
            continue
        if rel.name == "manifest.json":
            continue
        if rel.name in SKIP_FILES:
            continue
        yield rel, path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="every colour must be one of ours")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)

    root = Path(args.root)
    legal = allowed()
    problems: list[str] = []
    seen = 0

    for rel, path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for value in HEX.findall(text):
            seen += 1
            upper = value.upper()
            if upper in legal:
                continue
            line = text[:text.find(value)].count("\n") + 1
            problems.append(f"{rel}:{line}  {upper}  ({legal.get(upper, 'not a colour of the system')})")

    if problems:
        print(f"FAIL: {len(problems)} colour(s) that the system does not have")
        for problem in problems[:40]:
            print(f"  - {problem}")
        if len(problems) > 40:
            print(f"  … and {len(problems) - 40} more")
        return 1

    print(f"PASS: every colour is one of ours ({seen} occurrences, {len(legal)} sanctioned values)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
