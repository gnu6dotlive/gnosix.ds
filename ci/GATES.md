# The gates

What each gate is for, the command it runs, and the words it must say.

Until now the qualification said what passes and never what to expect: a
gate that began to say something else would still be green, because a gate
that exits zero is a gate that passes, whatever it prints on the way. The
run now compares each gate's own output with what this file says it must
contain, so a gate that changes its mind fails the qualification instead
of passing it quietly.

The file is read by the qualification itself, so a gate that is added
without a section here fails the run, and a section that names a gate
that does not exist fails it too.

---

## 1. Tokens project cleanly

```bash
python3 tools/project_tokens.py --check
```

Expected: no output. The projection writes nothing when the file on disk
is what the contract projects; the words are the gate's business, and the
gate that says so is the one below.

## 2. The surface layer is derived

```bash
python3 tools/surfaces.py --check
```

Expected: `PASS: the surface layer holds`.

## 3. The contrast table measures what the palette says

```bash
python3 tools/contrast.py --check
```

Expected: `PASS: the table measures what the palette says`.

## 4. The token exports are current

```bash
python3 tools/export_tokens.py --check
```

Expected: `PASS: the exports match the token source`.

## 5. The role layer is bound to the contract

```bash
python3 tools/project_roles.py --check
```

Expected: `PASS: the role layer projects cleanly`.

## 6. The component stylesheet is what the spec projects

```bash
python3 tools/project_components.py --check
```

Expected: `PASS: the stylesheet is what the specification projects`.

## 7. Every colour is one of ours

```bash
python3 tools/contract_colors.py
```

Expected: `PASS: every colour is one of ours`.

## 8. The surfaces use the system's colours

```bash
python3 tools/apply_surfaces.py --check
```

Expected: `PASS: every first-party surface uses the system's colours`.

## 9. Version authority

```bash
python3 tools/version.py --check
```

Expected: `PASS: every slot carries`.

## 10. Contract validates

```bash
python3 tools/contract.py --validate .
```

Expected: `PASS`.

## 11. Manifest matches the tree

```bash
python3 tools/rebuild_manifest.py --check
```

Expected: `clean`.

## 12. Alpha masters are straight

```bash
python3 tools/rekey_alpha.py --check
```

Expected: `[ok]`.

## 13. Mascot alpha is repaired

```bash
python3 tools/repair_mascot_alpha.py --check
```

Expected: `[ok]`.

## 14. Svg wrappers embed once

```bash
python3 tools/rebuild_svg_wrappers.py --check
```

Expected: `--check: nothing written`.

## 15. Favicons are the right crop

```bash
python3 tools/build_favicons.py --check
```

Expected: `--check: nothing written`.

## 16. Icon subset is vendored

```bash
python3 tools/vendor_icons.py --check
```

Expected: `licenses present`.

## 17. No ad-hoc glyphs

```bash
python3 tools/apply_icons.py --check
```

Expected: `would replace 0 ad-hoc glyph(s) in total`.

## 18. The FigCraft projection matches the source

```bash
python3 figcraft/generate.py --check
```

Expected: `PASS: the project matches the source`.

## 19. The two token projections agree

```bash
python3 figcraft/check_tokens.py
```

Expected: `PASS: the two projections agree on`.

## 20. The web code matches the design

```bash
python3 figcraft/handoff.py --board "Web / Landing" --check
```

Expected: `PASS: the web code matches the design`.

## 21. The native profile compiles and its tests pass

```bash
python3 tools/native_check.py
```

Expected: `test result: ok.`.

## 22. The gnu6-design package is what the contract cuts

```bash
python3 tools/package_gnu6_design.py --check
```

Expected: `PASS: the package is what the contract cuts`.

## 23. Every name the field declares is classified

```bash
python3 tools/check_vocabularies.py
```

Expected: `PASS: every name the package declares is classified`.

## 24. Every arrangement is specified as the sheet has it

```bash
python3 tools/specify_components.py --check
```

Expected: `PASS: every arrangement is specified as the sheet has it`.

## 25. Every gate says what it must say

```bash
python3 tools/gate_expectations.py --check
```

Expected: `PASS: every gate says what it must say`.

## 26. The severity register is honest

```bash
python3 tools/check_deviations.py
```

Expected: `PASS: the severity register holds`.

## 27. The gates stay inside the repository

```bash
python3 tools/check_containment.py
```

Expected: `PASS: the gates stay inside the repository`.

## 28. The surfaces render as the system carries them

```bash
python3 tools/eye.py
```

Expected: `PASS: the surfaces render as the system carries them`.

## 29. The work's own places are inside the repository

```bash
python3 tools/check_workplace.py
```

Expected: `PASS: the work's own places are inside the repository`.

## 30. The native profile carries the contract's states

```bash
python3 tools/project_native_states.py --check
```

Expected: `PASS: the native profile carries the contract's states`.

## 31. Every scheme keeps the system's guarantees

```bash
python3 tools/audit_scheme.py
```

Expected: `PASS: every scheme keeps the system's guarantees`.

---
