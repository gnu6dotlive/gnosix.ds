"""A scheme that does not know its values has to state what it promises.

SUR-011. The system admits a computation in place of a value only at the
floor that computation guarantees, and it reads the derived role at that
floor against every pairing the role is written in. These tests hold the
three answers: a derived ground is admitted, a derived ink whose floor is
short is refused, and a derived ink that needs an operation the system
cannot see is admitted only with the deviation that carries the proof.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from audit_scheme import audit  # noqa: E402
from project_roles import load  # noqa: E402


class DerivationTests(unittest.TestCase):
    def setUp(self):
        self.document, self.tokens, self.surfaces = load()
        self.roles = self.document["roles"]

    def test_a_derived_ground_is_admitted(self):
        scheme = {"name": "a wallpaper's chrome",
                  "roles": {},
                  "derived": {"accent": {"by": "from-source"}}}
        self.assertEqual(audit(scheme, self.roles, self.tokens, self.surfaces), [])

    def test_an_ink_under_its_floor_is_refused(self):
        # best-of-extremes guarantees 4.09 against an unknown ground: enough
        # for a mark, short of the 4.5 a text role is read at.
        scheme = {"name": "a wallpaper's chrome",
                  "roles": {},
                  "derived": {"accent-ink": {"by": "best-of-extremes"}}}
        problems = audit(scheme, self.roles, self.tokens, self.surfaces)
        self.assertTrue(problems)
        joined = " ".join(problems)
        self.assertIn("accent-ink", joined)
        self.assertIn("4.09", joined)
        self.assertIn("4.5", joined)

    def test_a_clamped_ink_names_the_deviation_that_proves_it(self):
        scheme = {"name": "a wallpaper's chrome",
                  "roles": {},
                  "derived": {"accent-ink": {"by": "best-of-extremes-clamped"}}}
        problems = audit(scheme, self.roles, self.tokens, self.surfaces)
        self.assertTrue(any("names none" in problem for problem in problems))

    def test_a_closed_deviation_is_not_a_proof(self):
        register = json.loads((ROOT / "core/DEVIATIONS.json").read_text(encoding="utf-8"))
        closed = next(entry["id"] for entry in register["deviations"]
                      if entry["state"] == "closed")
        scheme = {"name": "a wallpaper's chrome",
                  "roles": {},
                  "derived": {"accent-ink": {"by": "best-of-extremes-clamped",
                                             "deviation": closed}}}
        problems = audit(scheme, self.roles, self.tokens, self.surfaces)
        self.assertTrue(any("still owes its proof" in problem for problem in problems))

    def test_an_open_deviation_admits_the_clamp(self):
        register = json.loads((ROOT / "core/DEVIATIONS.json").read_text(encoding="utf-8"))
        opened = next(entry["id"] for entry in register["deviations"]
                      if entry["state"] == "open")
        scheme = {"name": "a wallpaper's chrome",
                  "roles": {},
                  "derived": {"accent-ink": {"by": "best-of-extremes-clamped",
                                             "deviation": opened}}}
        self.assertEqual(audit(scheme, self.roles, self.tokens, self.surfaces), [])

    def test_an_unknown_derivation_is_refused(self):
        scheme = {"name": "a wallpaper's chrome",
                  "roles": {},
                  "derived": {"ink": {"by": "trust-me"}}}
        problems = audit(scheme, self.roles, self.tokens, self.surfaces)
        self.assertTrue(any("does not hold" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
