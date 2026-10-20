"""The contrast table, derived rather than declared.

core/TOKENS.json states seven approved pairings and the ratio each one
measures. Those numbers were written by hand, which meant a colour could
change and the ratio beside it would keep saying what it said before.

This computes every declared ratio from the palette it names, and fails
when the two disagree. The pairing names read `ink_on_substrate` - the
way the contract reads them, where COL-002 puts white essential text on
Signal Orange - and a name that is a family means that family's base.

    python3 tools/contrast.py --check    # the gate
    python3 tools/contrast.py --write    # restate the table from the palette
    python3 tools/contrast.py --list     # what each pairing measures
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oklch import contrast_ratio, hex_to_rgb  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "core/TOKENS.json"

# How far a declared ratio may sit from the computed one. The table rounds
# to two decimals, so this is the rounding and a little of it.
TOLERANCE = 0.005


def resolve(tokens: dict, name: str) -> str | None:
    """The value of a shade, or of a family's base."""
    colour = tokens["color"]
    if name in colour and isinstance(colour[name], dict) and "base" in colour[name]:
        return colour[name]["base"]
    for ramp in colour.values():
        if isinstance(ramp, dict) and name in ramp:
            return ramp[name]
    return None


def pairs(tokens: dict) -> list[tuple[str, str, str, float]]:
    """Every declared pairing: the ink, the substrate, and the ratio."""
    out = []
    for pairing, declared in tokens.get("contrast", {}).items():
        ink, substrate = pairing.split("_on_")
        out.append((pairing, ink, substrate, declared))
    return out


def computed_ratio(tokens: dict, ink: str, substrate: str) -> float | None:
    ink_value = resolve(tokens, ink)
    substrate_value = resolve(tokens, substrate)
    if not ink_value or not substrate_value:
        return None
    return contrast_ratio(hex_to_rgb(ink_value), hex_to_rgb(substrate_value))


def check(tokens: dict) -> list[str]:
    problems = []
    for pairing, ink, substrate, declared in pairs(tokens):
        got = computed_ratio(tokens, ink, substrate)
        if got is None:
            problems.append(f"{pairing}: the palette has no {ink} or no {substrate}")
            continue
        if abs(got - declared) > TOLERANCE:
            problems.append(
                f"{pairing}: the table says {declared}, the palette measures {round(got, 2)}")
    return problems


def write(tokens: dict) -> int:
    table = {}
    for pairing, ink, substrate, _ in pairs(tokens):
        got = computed_ratio(tokens, ink, substrate)
        if got is None:
            print(f"the palette has no {pairing}", file=sys.stderr)
            return 1
        table[pairing] = round(got, 2)
    tokens["contrast"] = table
    TOKENS.write_text(json.dumps(tokens, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {TOKENS.relative_to(ROOT)}: {len(table)} pairings, restated from the palette")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="the contrast table")
    parser.add_argument("--check", action="store_true", help="verify the table against the palette")
    parser.add_argument("--write", action="store_true", help="restate the table from the palette")
    parser.add_argument("--list", action="store_true", help="print what each pairing measures")
    args = parser.parse_args(argv)

    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))

    if args.write:
        return write(tokens)

    if args.list:
        for pairing, ink, substrate, declared in pairs(tokens):
            got = computed_ratio(tokens, ink, substrate)
            print(f"  {pairing:38} {declared:6.2f}  "
                  f"(ink {resolve(tokens, ink)}, substrate {resolve(tokens, substrate)}, "
                  f"measured {got:.3f})")
        return 0

    problems = check(tokens)
    if problems:
        print(f"FAIL: {len(problems)} pairing(s) the palette does not measure")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"PASS: the table measures what the palette says ({len(pairs(tokens))} pairings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
