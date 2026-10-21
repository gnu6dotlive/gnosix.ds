"""The consultation suite has to say everything the contract says.

A reference that is missing a rule is worse than no reference: it answers
the question with a silence. So the projection is held here from both
sides — every element of the contract is on the page, and the page adds
no element the contract does not have.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import project_reference  # noqa: E402


class ConsultationSuiteTests(unittest.TestCase):
    def setUp(self):
        self.page, self.script = project_reference.build()

    def test_every_role_is_on_the_page(self):
        roles = json.loads((ROOT / "core" / "ROLES.json").read_text(encoding="utf-8"))["roles"]
        for name in roles:
            self.assertIn(f'id="role-{name}"', self.page, name)

    def test_every_rule_is_on_the_page(self):
        rules = json.loads((ROOT / "core" / "rules.json").read_text(encoding="utf-8"))["rules"]
        for rule in rules:
            self.assertIn(f'id="rule-{rule["id"].lower()}"', self.page, rule["id"])

    def test_every_component_is_on_the_page(self):
        components = json.loads(
            (ROOT / "core" / "COMPONENTS.json").read_text(encoding="utf-8"))["components"]
        for name in components:
            self.assertIn(f'id="component-{name}"', self.page, name)

    def test_every_state_is_on_the_page(self):
        states = json.loads(
            (ROOT / "profiles" / "native" / "states.json").read_text(encoding="utf-8"))["states"]
        for state in states:
            self.assertIn(f'id="state-{state["id"]}"', self.page, state["id"])

    def test_every_statement_of_the_owner_is_on_the_page(self):
        intent = json.loads((ROOT / "core" / "INTENT.json").read_text(encoding="utf-8"))
        for statement in intent["statements"]:
            self.assertIn(f'id="statement-{statement["id"].lower()}"', self.page,
                          statement["id"])

    def test_every_deviation_is_on_the_page(self):
        deviations = json.loads(
            (ROOT / "core" / "DEVIATIONS.json").read_text(encoding="utf-8"))["deviations"]
        for deviation in deviations:
            self.assertIn(f'id="deviation-{deviation["id"].lower()}"', self.page,
                          deviation["id"])

    def test_the_search_index_holds_every_entry(self):
        index = json.loads(self.script.split("const GNOSIX_INDEX = ", 1)[1]
                           .split(";", 1)[0])
        self.assertGreater(len(index), 100)
        for entry in index:
            self.assertIn(entry["anchor"], self.page, entry["anchor"])

    def test_the_projection_is_deterministic(self):
        again, script = project_reference.build()
        self.assertEqual(self.page, again)
        self.assertEqual(self.script, script)


if __name__ == "__main__":
    unittest.main()
