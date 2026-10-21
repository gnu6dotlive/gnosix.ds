"""The register of upstream is a record of measurements, not of intentions.

The contract is the semantic authority, and an upstream is a projection
target or a source of evidence. So the register is held to the
obligations: a pin says what it is, who owns it, whether this repository
checks it, what was qualified against it, and what would refresh it; an
observation says what was observed and what is inferred, the evidence and
its limits, the level it reaches, and the scope of the claims it bears on.

The gate is held here in both directions — a complete record passes, and
every way of getting it wrong fails.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_upstream  # noqa: E402


def a_pin(**overrides) -> dict:
    pin = {
        "rail": "gpui-window-display",
        "exact_identity": "gpui-pre 0.3.5, a snapshot of zed-industries/zed@d89e9c2",
        "authority": "the field's vendor/ directory: the field owns this pin",
        "verification": "referenced",
        "qualification_scope": "the field's source-level qualification of the native surfaces",
        "known_divergence": "none recorded",
        "refresh_condition": "a new release, or a change in the field's vendored snapshot",
        "where": "the field's vendor/gpui-pre-linux-0.3.5",
        "measured_on": "2026-10-21",
    }
    pin.update(overrides)
    return pin


def an_observation(**overrides) -> dict:
    observation = {
        "id": "UP-001",
        "rail": "gpui-window-display",
        "upstream": {
            "what": "gpui_linux, the layer-shell surface path",
            "exact_identity": "gpui-pre-linux 0.3.5, a snapshot of zed-industries/zed@d89e9c2",
            "source": "the field's vendored source: vendor/gpui-pre-linux-0.3.5/src/linux/wayland/window.rs:311",
            "published_behaviour": "the published toolkit rewrites the compositor-selected size",
            "field_behaviour": "the field's snapshot preserves the compositor-sized request",
        },
        "bears_on": ["SUR-001"],
        "materiality": "a primitive's observable behaviour relevant to geometry",
        "observed_fact": "the request is preserved across configures",
        "inference": "the contract's geometry rules are read against a compositor-sized axis",
        "local_evidence": "the field's vendored source at the recorded location",
        "evidence_limits": "source-level only",
        "evidence_level": "source",
        "projection": "none",
        "projection_reason": "the native profile publishes values and names, and carries no behaviour",
        "gate": "tools/native_check.py",
        "next_experiment": "read the size the compositor grants across one hot output resize",
        "decision_owner": "the owner",
        "disposition": "recorded; no projection change",
        "scope_affected": ["the qualifications that depend on the resize path"],
        "scope_unaffected": ["the contract's semantic roles, tokens and guarantees"],
    }
    observation.update(overrides)
    return observation


def a_register(**overrides) -> dict:
    register = {
        "levels": list(check_upstream.LEVELS),
        "verifications": list(check_upstream.VERIFICATIONS),
        "rails": [{"id": "gpui-window-display", "subject": "a subject",
                   "materiality": "a materiality"}],
        "pins": [a_pin()],
        "observations": [an_observation()],
        "handoffs": [],
    }
    register.update(overrides)
    return register


class UpstreamRegisterTests(unittest.TestCase):
    def test_a_complete_record_passes(self):
        found = check_upstream.problems(a_register())
        self.assertEqual(found, [], found)

    # — the pin's obligations —

    def test_a_pin_without_its_authority_fails(self):
        register = a_register()
        register["pins"][0]["authority"] = ""
        found = check_upstream.problems(register)
        self.assertTrue(any("does not say authority" in problem for problem in found), found)

    def test_a_pin_without_its_qualification_scope_fails(self):
        register = a_register()
        register["pins"][0]["qualification_scope"] = ""
        found = check_upstream.problems(register)
        self.assertTrue(any("qualification scope" in problem for problem in found), found)

    def test_a_pin_without_its_refresh_condition_fails(self):
        register = a_register()
        register["pins"][0]["refresh_condition"] = ""
        found = check_upstream.problems(register)
        self.assertTrue(any("refresh condition" in problem for problem in found), found)

    def test_a_pin_that_names_a_moving_reference_fails(self):
        register = a_register()
        register["pins"][0]["exact_identity"] = "main"
        found = check_upstream.problems(register)
        self.assertTrue(any("moving reference" in problem for problem in found), found)

    def test_a_field_pin_claiming_to_be_verified_fails(self):
        # A pin this repository cannot check is referenced or declared.
        # Claiming it is verified would be claiming a check that does not
        # happen here.
        register = a_register()
        register["pins"][0]["verification"] = "verified"
        found = check_upstream.problems(register)
        self.assertTrue(any("claims to be verified" in problem for problem in found), found)

    def test_a_pin_verified_here_must_be_held_here(self):
        register = a_register()
        register["pins"][0].update({
            "authority": "this repository: ci/provision-engine.sh",
            "verification": "verified",
            "where": "ci/provision-engine.sh",
            "exact_identity": "figcraft 9.9.9",
        })
        found = check_upstream.problems(register)
        # The file exists but does not name this identity: the pin has rotted.
        self.assertTrue(any("rotted" in problem for problem in found), found)

    def test_an_unknown_verification_state_fails(self):
        register = a_register()
        register["pins"][0]["verification"] = "probably fine"
        found = check_upstream.problems(register)
        self.assertTrue(any("not one of" in problem for problem in found), found)

    # — the observation's obligations —

    def test_an_observation_without_its_evidence_limits_fails(self):
        register = a_register()
        register["observations"][0]["evidence_limits"] = ""
        found = check_upstream.problems(register)
        self.assertTrue(any("evidence limits" in problem for problem in found), found)

    def test_an_observation_without_its_scope_fails(self):
        register = a_register()
        register["observations"][0]["scope_affected"] = []
        found = check_upstream.problems(register)
        self.assertTrue(any("scope affected" in problem for problem in found), found)

    def test_an_observation_without_its_next_experiment_fails(self):
        register = a_register()
        register["observations"][0]["next_experiment"] = ""
        found = check_upstream.problems(register)
        self.assertTrue(any("next experiment" in problem for problem in found), found)

    def test_an_observation_without_its_disposition_fails(self):
        register = a_register()
        register["observations"][0]["disposition"] = ""
        found = check_upstream.problems(register)
        self.assertTrue(any("disposition" in problem for problem in found), found)

    def test_an_observation_at_an_unknown_level_fails(self):
        register = a_register()
        register["observations"][0]["evidence_level"] = "vibes"
        found = check_upstream.problems(register)
        self.assertTrue(any("level" in problem for problem in found), found)

    def test_an_observation_that_bears_on_something_unpublished_fails(self):
        register = a_register()
        register["observations"][0]["bears_on"] = ["SUR-999"]
        found = check_upstream.problems(register)
        self.assertTrue(any("does not publish" in problem for problem in found), found)

    def test_an_observation_that_names_a_rail_that_does_not_exist_fails(self):
        register = a_register()
        register["observations"][0]["rail"] = "nowhere"
        found = check_upstream.problems(register)
        self.assertTrue(any("not a rail" in problem for problem in found), found)

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

    # — the register of the contract itself —

    def test_the_register_of_the_contract_itself_is_readable(self):
        register = json.loads((ROOT / "core" / "UPSTREAM.json").read_text(encoding="utf-8"))
        for pin in register["pins"]:
            self.assertIn(pin["verification"], ("verified", "referenced", "declared"))
            self.assertTrue(pin.get("authority"))
        for observation in register.get("observations", []):
            self.assertTrue(observation.get("id"))
            self.assertTrue(observation.get("conclusion") or observation.get("disposition"))
            self.assertTrue(observation.get("scope_unaffected"))

    def test_the_field_handoff_states_no_pin_of_its_own(self):
        handoff = ROOT / "research" / "UPSTREAM-FIELD-VERIFICATION-HANDOFF-20261021.md"
        text = handoff.read_text(encoding="utf-8")
        self.assertIn("no pin", text.lower())
        self.assertIn("no observation", text.lower())
        self.assertIn("exit conditions", text.lower())


if __name__ == "__main__":
    unittest.main()
