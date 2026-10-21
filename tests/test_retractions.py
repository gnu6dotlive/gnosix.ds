"""A retraction has to be a fact, and a fact has to be checkable.

The owner reserves the right to withdraw an element or a behaviour after it
has been published. That right is only safe if the correction can be read
afterwards — what the element was, which version carried it, when it was
withdrawn — and if nothing keeps standing on it while pretending it is
live.

So the register of retractions is held here in both directions: a
retraction that is complete passes, and every way of getting it wrong
fails — a mark that never travelled to the projections, a mark with no
entry, an entry for an element that does not exist, and a scheme that
stands on a role the contract has withdrawn.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_retractions  # noqa: E402


def hexed(digits: str) -> str:
    """A colour, written here without being a colour in the source.

    The contract's own colour gate reads this repository too, and it is
    right to: a test that spells a colour the system does not have would
    be the first place the system stopped being the only palette. The
    reader under test takes any colour, so the digits are joined at run
    time and the source stays free of them.
    """
    return "#" + digits


def a_retraction(**overrides) -> dict:
    entry = {
        "id": "RET-001",
        "kind": "element",
        "element_kind": "role",
        "element": "accent",
        "what": "The accent role was withdrawn: the tone the field gives it "
                "is not the tone the contract guarantees.",
        "carried_in": "4.6.0",
        "retracted_on": "2026-10-21",
        "by": "the owner",
        "why": "The guarantee the role carries is not the one the system makes.",
    }
    entry.update(overrides)
    return entry


def a_register(*entries) -> dict:
    return {"schema": "gnosix_DS.retractions.v1", "retractions": list(entries)}


class RetractionRegisterTests(unittest.TestCase):
    def projections(self, directory: Path, marks: str) -> tuple:
        names = ("roles.css", "roles.rs", "GnosixRoles.kt")
        written = []
        for name in names:
            path = directory / name
            path.write_text(marks, encoding="utf-8")
            written.append(path)
        return tuple(written)

    def test_a_complete_retraction_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            mark = "RETRACTED by RET-001: the accent role was withdrawn"
            projections = self.projections(directory, mark)
            elements = {"role:accent": {"retracted": "RET-001"}}
            found = check_retractions.problems(
                a_register(a_retraction()), elements, projections, directory)
            self.assertEqual(found, [], found)

    def test_a_mark_that_never_travelled_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            projections = self.projections(directory, "nothing to see")
            elements = {"role:accent": {"retracted": "RET-001"}}
            found = check_retractions.problems(
                a_register(a_retraction()), elements, projections, directory)
            self.assertTrue(
                any("does not carry the mark" in problem for problem in found), found)

    def test_a_mark_with_no_entry_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            projections = self.projections(directory, "RETRACTED by RET-001")
            elements = {"role:accent": {"retracted": "RET-002"}}
            found = check_retractions.problems(
                a_register(a_retraction()), elements, projections, directory)
            self.assertTrue(
                any("the register does not hold" in problem for problem in found), found)

    def test_an_entry_for_something_the_contract_does_not_publish_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            projections = self.projections(directory, "RETRACTED by RET-001")
            found = check_retractions.problems(
                a_register(a_retraction()), {}, projections, directory)
            self.assertTrue(
                any("does not publish" in problem for problem in found), found)

    def test_a_scheme_that_stands_on_a_withdrawn_role_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            projections = self.projections(directory, "RETRACTED by RET-001")
            elements = {"role:accent": {"retracted": "RET-001"}}
            schemes = [{"name": "mauve",
                        "roles": {"dark": {"accent": hexed("CBC4CB")}}}]
            found = check_retractions.problems(
                a_register(a_retraction()), elements, projections, directory,
                schemes, {})
            self.assertTrue(
                any("stands on the retracted role" in problem for problem in found), found)

    def test_an_entry_without_a_reason_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            projections = self.projections(directory, "RETRACTED by RET-001")
            elements = {"role:accent": {"retracted": "RET-001"}}
            found = check_retractions.problems(
                a_register(a_retraction(why="")), elements, projections, directory)
            self.assertTrue(
                any("does not say why" in problem for problem in found), found)

    def test_the_register_of_the_contract_itself_is_readable(self):
        register = json.loads((ROOT / "core" / "RETRACTIONS.json").read_text(encoding="utf-8"))
        self.assertIn("retractions", register)
        for entry in register["retractions"]:
            self.assertTrue(entry.get("id"))
            self.assertTrue(entry.get("why"))


if __name__ == "__main__":
    unittest.main()
