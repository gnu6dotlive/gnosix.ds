"""The register of upstream is a record of measurements, not of intentions.

The contract is the semantic authority, and an upstream is a projection
target or a source of evidence. So the register is held to the exit
condition of the intake: the exact revision, the contract element it bears
on, whether a projection changes, and either a gate that holds the answer
or the reason there is no effect.

The gate is held here in both directions — a complete observation passes,
and every way of getting it wrong fails.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_upstream  # noqa: E402


def a_register(**overrides) -> dict:
    register = {
        "rails": [{"id": "gpui-window-display", "subject": "a subject",
                   "materiality": "a materiality"}],
        "pins": [{"rail": "gpui-window-display", "revision": "1.2.3",
                  "exact": "1.2.3 @ abcdef", "where": "the field's host"}],
        "observations": [{
            "id": "UP-001",
            "rail": "gpui-window-display",
            "upstream": {"what": "gpui_linux", "revision": "gpui-pre-linux 0.3.5",
                         "change": "the sizing of a layer-shell surface"},
            "bears_on": ["SUR-001"],
            "projection": "none",
            "evidence": "source",
            "gate": "tools/native_check.py",
            "conclusion": "No projection changes: the native profile carries values, not behaviour.",
        }],
    }
    register.update(overrides)
    return register


class UpstreamRegisterTests(unittest.TestCase):
    def test_a_complete_observation_passes(self):
        found = check_upstream.problems(a_register())
        self.assertEqual(found, [], found)

    def test_an_observation_without_a_pinned_revision_fails(self):
        register = a_register()
        register["observations"][0]["upstream"]["revision"] = "latest"
        found = check_upstream.problems(register)
        self.assertTrue(any("moving reference" in problem for problem in found), found)

    def test_an_observation_that_bears_on_something_unpublished_fails(self):
        register = a_register()
        register["observations"][0]["bears_on"] = ["SUR-999"]
        found = check_upstream.problems(register)
        self.assertTrue(any("does not publish" in problem for problem in found), found)

    def test_an_observation_without_a_gate_or_a_conclusion_fails(self):
        register = a_register()
        register["observations"][0].pop("gate")
        register["observations"][0]["conclusion"] = ""
        found = check_upstream.problems(register)
        self.assertTrue(any("neither a gate nor a conclusion" in problem for problem in found), found)

    def test_an_observation_naming_a_gate_that_does_not_exist_fails(self):
        register = a_register()
        register["observations"][0]["gate"] = "tools/not_a_gate.py"
        found = check_upstream.problems(register)
        self.assertTrue(any("not in the repository" in problem for problem in found), found)

    def test_a_rail_without_a_pin_fails(self):
        register = a_register()
        register["rails"].append({"id": "hyprland-compositor", "subject": "s", "materiality": "m"})
        found = check_upstream.problems(register)
        self.assertTrue(any("has no pin" in problem for problem in found), found)

    def test_a_pin_that_names_a_moving_reference_fails(self):
        register = a_register()
        register["pins"][0]["exact"] = "main"
        found = check_upstream.problems(register)
        self.assertTrue(any("moving reference" in problem for problem in found), found)

    def test_the_register_of_the_contract_itself_is_readable(self):
        register = json.loads((ROOT / "core" / "UPSTREAM.json").read_text(encoding="utf-8"))
        self.assertTrue(register.get("rails"))
        for rail in register["rails"]:
            self.assertTrue(rail.get("materiality"))
        for observation in register.get("observations", []):
            self.assertTrue(observation.get("id"))
            self.assertTrue(observation.get("conclusion") or observation.get("gate"))


if __name__ == "__main__":
    unittest.main()
