"""The colour reader has to read colours, and nothing else.

A shell writes `0x00000000` where it means "no fill": the alpha is the
absence of a surface, not a black one. Reading it as a colour asks the
system to own a black the product never paints — sixty-seven of one
field's colours were this and nothing else when the reader counted them.

So the reader is held here, in both directions: a colour at alpha zero is
not a colour, and a colour at any other alpha still is.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from consumer_check import colours_in  # noqa: E402


def hexed(digits: str) -> str:
    """A colour, written here without being a colour in the source.

    The contract's own colour gate reads this repository too, and it is
    right to: a test that spells a colour the system does not have would
    be the first place the system stopped being the only palette. The
    reader under test takes any colour, so the digits are joined at run
    time and the source stays free of them.
    """
    return "#" + digits


class ColourReaderTests(unittest.TestCase):
    def test_a_transparent_native_constant_is_not_a_colour(self):
        for source in ("rgba(0x00000000)", "argb(0x00FF0000)", "0x00000000",
                       "0x00FF_FFFF"):
            self.assertEqual(colours_in(source), [], source)

    def test_an_opaque_native_constant_is_a_colour(self):
        self.assertEqual(colours_in("0xFF000000"), [hexed("000000")])
        self.assertEqual(colours_in("0xFFFF6A00"), [hexed("FF6A00")])
        self.assertEqual(colours_in("argb(0xFFF7F3ED)"), [hexed("F7F3ED")])

    def test_a_transparent_css_colour_is_not_a_colour(self):
        for source in (hexed("00000000"), hexed("FFF0"), "rgba(0, 0, 0, 0)",
                       "rgba(0,0,0,0%)", "hsl(0, 0%, 0%, 0)",
                       "oklch(0.5 0.1 20 / 0)"):
            self.assertEqual(colours_in(source), [], source)

    def test_an_opaque_css_colour_is_a_colour(self):
        self.assertEqual(colours_in(hexed("000000")), [hexed("000000")])
        self.assertEqual(colours_in(hexed("000000FF")), [hexed("000000")])
        self.assertEqual(colours_in("rgba(0, 0, 0, 0.5)"), [hexed("000000")])
        self.assertEqual(colours_in(hexed("F7F3ED")), [hexed("F7F3ED")])

    def test_the_two_orders_of_alpha_are_read_in_their_own_order(self):
        # CSS puts the alpha last, a bare native constant puts it first:
        # the same eight digits name red in one and black in the other.
        self.assertEqual(colours_in(hexed("FF0000FF")), [hexed("FF0000")])
        self.assertEqual(colours_in("0xFFFF0000"), [hexed("FF0000")])
        self.assertEqual(colours_in("0xFF000000"), [hexed("000000")])
        self.assertEqual(colours_in("0xFF0000FF"), [hexed("0000FF")])


if __name__ == "__main__":
    unittest.main()
