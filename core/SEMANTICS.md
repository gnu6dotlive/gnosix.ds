# Semantic contract

Start with a role and a state. Then choose its visual encoding and target-specific control. A color, shape, platform widget or screenshot does not create semantics by itself. The machine-readable constraints live in `rules.json`.

| Role | Meaning | Required evidence in an interface |
|---|---|---|
| primary-action | Principal operation in a context | Verb label, focus treatment, pending/result distinction |
| secondary-action | Supporting operation | Distinct priority without loss of discoverability |
| destructive-action | Operation with material negative consequence | Text and consequence cue; no brand-orange default |
| prompt | Direction for an available next step | Textual invitation, not success evidence |
| status-stable | Observed calm/normal condition | Adjacent text; optional state pip |
| status-attention | Condition requiring inspection | Explicit text and non-color cue |
| status-breach | Failure or dangerous condition | Explicit consequence and non-color cue |
| evidence | Source or observation of a claim | Legible source/identifier; Space Grotesk with tabular numerals for terse metadata |
| focus | Current keyboard/assistive target | Visible indicator independent of hover |
| selection | Current choice or context | Structural edge, surface or outline plus accessible state |
| scalar-field | Quantity encoded spatially or chromatically | Domain, range, endpoints, neutral when relevant, missing handling, legend |

State words are distinct: **intended** describes a request, **observed** a reported external fact, **derived** a computed interpretation, and **projected** the message shown to a person. A request may be pending, rejected or later observed. Activating a control must not cause the UI to claim success prematurely. Where a backend is not present, examples must say they simulate the sequence locally.

CHIP-like status/filter/choice/category/count capsules are prohibited regardless of renaming. Use text and an optional state pip, proper filter/menu controls, row selection treatment, or aligned numeric text. Rounded functional controls remain valid.
