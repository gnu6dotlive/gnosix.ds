import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTABLE_LAWS = {"MOT-LAW-CAUSALITY", "MOT-LAW-PERFORMANCE", "MOT-LAW-CONTINUITY",
                 "MOT-LAW-INTERRUPTIBLE", "MOT-LAW-REDUCED-EQUIVALENCE", "MOT-LAW-STILLNESS"}


def load_motion():
    return json.loads((ROOT / "profiles/motion/motion.json").read_text())


class MotionProfileTests(unittest.TestCase):
    def test_status_is_declared_and_valid(self):
        status = json.loads((ROOT / "profiles/motion/status.json").read_text())
        self.assertEqual(status["profile"], "motion")
        self.assertIn(status["status"], {"specified", "mapped", "rendered", "verified"})
        self.assertTrue(status["gaps"], "an unpromoted profile must declare its gaps")

    def test_version_tracks_core_rules(self):
        motion = load_motion()
        rules_version = json.loads((ROOT / "core/rules.json").read_text())["version"]
        self.assertEqual(motion["version"], rules_version)

    def test_portable_layer_is_complete(self):
        portable = load_motion()["portable"]
        laws = {law["id"] for law in portable["laws"]}
        self.assertEqual(laws, PORTABLE_LAWS)
        for law in portable["laws"]:
            with self.subTest(law=law["id"]):
                self.assertTrue(law["statement"].strip())
                self.assertTrue(law["test"].strip(), "every law needs a way to check it")
        for role in portable["roles"]:
            with self.subTest(role=role["id"]):
                self.assertIsInstance(role["interruptible"], bool)
                self.assertTrue(role["reduced_motion_equivalent"].strip(),
                                "every role needs a defined reduced-motion projection")
        for seam in portable["seams"]:
            with self.subTest(seam=seam["id"]):
                self.assertIn("reduced_motion_equivalent", seam)
                self.assertIn("intent", seam)

    def test_idle_motion_and_identity_motion_are_prohibited(self):
        bans = {b["id"]: b for b in load_motion()["portable"]["prohibitions"]}
        self.assertIn("MOT-BAN-IDLE", bans)
        self.assertIn("MOT-BAN-IDENTITY-MOTION", bans)
        self.assertIn("ID-003", bans["MOT-BAN-IDENTITY-MOTION"]["rules"])
        self.assertIn("ID-001", bans["MOT-BAN-IDENTITY-MOTION"]["rules"])
        self.assertIn("MOT-BAN-TOKEN-LADDER", bans)

    def test_pending_motion_may_not_resolve_a_state(self):
        motion = load_motion()
        roles = {r["id"]: r for r in motion["portable"]["roles"]}
        self.assertIn("state-pending", roles)
        self.assertIn("not success", roles["state-pending"]["meaning"].lower())
        self.assertIn("STA-001", motion["portable"]["state_timing"]["rules"])

    def test_target_numbers_stay_out_of_the_token_source(self):
        """MOT-BAN-TOKEN-LADDER, enforced structurally.

        A substring search for ladder step names is not usable here: the colour ramps
        already contain a step literally named "base", which collides with the motion
        ladder. So walk the token document instead and reject motion vocabulary outright.
        """
        motion = load_motion()
        remotion = motion["targets"]["remotion"]
        self.assertTrue(remotion["ladder_frames"])
        self.assertIn("target-local", remotion["note"].lower())

        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        motion_vocabulary = {
            "motion", "duration", "durations", "easing", "ease", "transition", "transitions",
            "frames", "frame", "fps", "tween", "keyframe", "keyframes", "seam", "seams",
            "ladder", "animate", "animation", "spring", "curve", "timing", "delay",
        }
        ladder_names = set(remotion["ladder_frames"])

        def walk(node, trail):
            if isinstance(node, dict):
                for key, value in node.items():
                    with self.subTest(token_path="/".join(trail + [str(key)])):
                        self.assertNotIn(key.lower(), motion_vocabulary,
                                         f"motion vocabulary {key!r} leaked into core/TOKENS.json")
                        self.assertNotIn(key, ladder_names,
                                         f"motion ladder step {key!r} leaked into core/TOKENS.json")
                    walk(value, trail + [str(key)])
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, trail + [str(index)])

        walk(tokens, [])

    def test_motion_ladder_names_do_not_collide_with_token_names(self):
        """A ladder step that reuses an existing token name makes a leak undetectable.

        The colour ramps already own a step called "base". An earlier motion draft reused it,
        so a check for "did a motion name reach TOKENS.json" could not tell a leak from a
        legitimate colour token. Keep the vocabularies disjoint.
        """
        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        ladder_names = set(load_motion()["targets"]["remotion"]["ladder_frames"])

        def keys(node, into):
            if isinstance(node, dict):
                for key, value in node.items():
                    into.add(key)
                    keys(value, into)
            elif isinstance(node, list):
                for value in node:
                    keys(value, into)

        token_keys: set = set()
        keys(tokens, token_keys)
        overlap = ladder_names & token_keys
        self.assertEqual(overlap, set(),
                         f"motion ladder step name(s) collide with token names: {sorted(overlap)}")

    def test_ratified_token_sections_are_unchanged(self):
        """The token source is load-bearing for a negative assertion above, so pin its shape."""
        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        self.assertEqual(
            set(tokens),
            {"schema", "status", "color", "typography", "spacing", "radius",
             "contrast"},
        )

    def test_the_atoms_are_judged_by_the_laws(self):
        """The field's mechanisms are carried by name, and judged.

        An atom that idles is refused: a law is a law whichever field
        wrote the atom. And an atom that names a duration or a curve the
        profile does not carry is a mechanism that cannot be expressed.
        """
        motion = load_motion()
        atoms = motion["portable"]["atoms"]
        self.assertTrue(atoms, "the profile carries no atom")
        durations = set(motion["portable"]["durations"])
        curves = set(motion["targets"]["remotion"]["easing_curves"])
        laws = {law["id"] for law in motion["portable"]["laws"]}
        for atom in atoms:
            self.assertIn(atom["duration"], durations,
                          f"{atom['id']}: no such duration")
            self.assertNotIn("+", atom["duration"],
                             f"{atom['id']}: a composed duration is carried "
                             f"as its base and its delay")
            self.assertIn(atom["easing"], curves, f"{atom['id']}: no such curve")
            if atom["verdict"] == "forbidden":
                self.assertIn("reason", atom, f"{atom['id']}: refused with no reason")
                named = [law for law in laws if law in atom["reason"]]
                self.assertTrue(named, f"{atom['id']}: refused without naming a law")
            else:
                self.assertEqual(atom["verdict"], "lawful")

    def test_reduced_motion_must_be_an_explicit_input(self):
        """A headless renderer reports the render machine's preference, not the viewer's."""
        remotion = load_motion()["targets"]["remotion"]
        reduced = remotion["reduced_motion"]
        self.assertIn("explicit input", reduced["detection"])
        self.assertEqual(reduced["duration_frames"], 1)
        self.assertIn("state_text", reduced["retain"])
        for banned in ("transform", "blur", "loop"):
            self.assertIn(banned, reduced["drop"])


if __name__ == "__main__":
    unittest.main()
