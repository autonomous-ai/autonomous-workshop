# Solid (Workshop Make) harness — Make

You are Codex running in a Harness workspace for **Workshop**: describe a 3D object, get a
validated, printable STEP part or assembly. This file is the whole workflow for that; it is the
Make stage of Autonomous Workshop on its own, with no Inventor, Wish packet, host gate or shop.

## What is already set up

- `CAD_SKILL_ROOT` and `WORKSHOP_PYTHON` are set in your environment. Every CAD command is
  `"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/<tool>"`. Where a skill says
  `CAD_SKILL_ROOT="$(workshop skills path)/cad"`, skip that line — the variable is already correct.
- Skills are materialized under `.agents/skills/`: `cad` (modeling, generation, gates),
  `make-round` (one repair round, batched), `step-parts` (purchasable parts), `image-to-cad`
  (reference images), `design-reference`, `electromechanical-integration`. Read
  `.agents/skills/cad/SKILL.md` before the first build; load its references by their triggers.
- **A 3D pane is open beside this terminal.** It shows `model.step` and redraws by itself a few
  seconds after every `gen --write`. Never start a viewer, never print a URL, never ask the user
  to open a file: writing the STEP *is* showing it.
- `.harness/verdict.json` is written by `verify_project` and read by Harness for the pane header.
  Never write or edit it yourself.

## Project layout

The workspace *is* the project. It starts as Tier 1:

```
model.step.py     the combined entry — gen_step() returns the object. THE NAME IS FIXED.
model.step        the generated STEP, the only deliverable; rewritten by every gen --write
README.md         what each file is and the rebuild commands (keep it true)
snap/             review renders        measure/   gate reports and manifests
```

`model.step.py` starts as a placeholder 20 mm cube. Replace `gen_step()`; do not rename the file —
the pane follows `model.step`, and a workspace has exactly one combined entry. When the model
outgrows one file (separately printable parts, 3+ named parts, or ~120 code lines —
`references/project-structure.md`), it becomes Tier 2 in place: `model_lib.py` holds parameters and
part builders, `model.step.py` becomes placement plus labels, and each printable part gets its own
`part_<role>.step.py` in print orientation. `check_layout` enforces the tier; run it before `gen`.
Never edit generated artifacts (`model.step`, `__cadgen__/`, `snap/`, `measure/`); edit source.

STEP is the only deliverable. There is no STL, 3MF or GLB export — say so if asked, and answer
"does it print?" with the print gates below rather than a mesh.

## The loop

Before the first line of geometry: classify the task, load only the references its triggers name,
write the brief (`references/cad-brief.md`) with dimensions, units, datum and validation targets,
and check bought parts by name *and* by form with `$step-parts` (never author your own gear, bolt,
bearing or servo). Ask the user one question only if the model is impossible or fit-critical
without it; decide wall thickness, clearances, fillets, orientation yourself from the defaults.

Every round, in one shell call where the tools allow it:

```bash
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/check_layout" .
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/gen" model.step.py --write --json
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/inspect" refs model.step --facts --planes --positioning
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/render_review" model.step.py --view front --view top --view iso -o snap/review
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/verify_project" . --quick
```

`gen --write` is the only thing that writes `model.step` — always pass `--write` on the run that
ends an edit. Look at the review PNGs (front, top, iso) once per round and fix what you see:
misplaced or missing parts, proportions, intersections, floating geometry, a blob on a plaque.
Then the targeted `inspect measure|align|frame|diff` checks the edit changed. Defer
`inspect validate` and `inspect interfere` until the shape has stopped changing; they are the
expensive half of a run (`references/run-cost.md`). In a Tier 2 project, `make-round` batches a
round (`.agents/skills/make-round/SKILL.md` is its tool card): pass every component through its
own `--component part_<role>.step.py` loop, then the assembly with `--require-component-passes`.

Rules that hold every round:

- Edit the smallest responsible source section, regenerate, rerun the failed check — same round.
- Batch targets into one `gen` and one `inspect batch`; never run warm CAD CLIs concurrently.
- Motion verification is opt-in: `--check-motion true` on `make_round`/`verify_project` when the
  object has a joint, a lid, an insertion or a snap, with `measure/motion.json` written per
  `references/motion-manifests.md`. Without it, motion is unverified — say so, never "assembles".
- Powered or lit products go through `$electromechanical-integration` before the layout is fixed.
- After editing a shared `model_lib.py`, delete `__cadgen__/` before the next build.
- Keep the session small: read round summaries, not logs; learn flags from `--help`, not by
  reading scripts; start a long command with a generous yield and continue it with stdin rather
  than sleeping between polls.

## The final gate

When the shape has settled, generate every entry with `--write`, run `inspect validate` and
`inspect interfere` once, then the print gates and the final pipeline:

```bash
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/verify_project" . --print-gates --nozzle 0.4
```

Final mode refuses to start until `snap/SIGNATURE-REVIEW.json` exists — the blind review that
Workshop requires before its integrated gate. Produce it like this:

1. `render_product model.step -o snap/iso.png` and a fixed-camera state or motion sheet at
   `snap/signature.png` (`--state-sheet` for a mechanism, `--motion-sheet` for a static shape),
   both at least 1200×800.
2. Give one independent critic (a subagent) only those two images, without the user's request,
   and record its held-object, form, subjects, action, relationship and anti-generic reads. Then
   reveal the request and judge the matches. Repair and re-render if it finds a blocker; at most
   four review rounds.
3. Write the review as canonical JSON (`sort_keys`, separators `,` and `:`, no trailing newline)
   with exactly these keys: `schema_version` (8), `kind`
   (`autonomous-workshop.signature-experience-review`), `concept_sha256` (sha256 of your brief),
   `iso_sha256`, `signature_sha256` (sha256 of the two PNGs), `reviewer`, `blind_held_read`,
   `blind_form_read`, `blind_subjects_read`, `blind_action_read`, `blind_relationship_read`,
   `anti_generic_signature_read`, `largest_risk`, `resolution` (non-empty text);
   `wish_revealed_after_blind_read`, `held_object_unmistakable`, `form_matches_wish`,
   `subjects_match_wish`, `action_matches_wish`, `relationship_matches_wish`,
   `anti_generic_signature_visible`, `signature_experience_unmistakable`,
   `finished_product_desirable` (all `true`); `review_rounds` (1–4);
   `critical_form_requirements` (1–16 of `{requirement, blind_evidence, matches: true}`);
   `blocking_visual_defects` (`[]`); `print_gate_sha256s` (`{}` until the print gates ran, then
   each cited `measure/<gate>-<role>.md` mapped to its sha256).

`verify_project` writes `measure/verification-pipeline.md` and the Harness verdict. A passing
final run is what lets you call the model verified; a passing `--print-gates` run at the nozzle
the print will use is what lets you call it print-ready. Report the checks that actually ran.
Digital evidence never proves a successful print, fit or durability — do not claim them.

## Reporting to the user

Short. What the object is, its bounding box, the part count and print orientation, which gates
ran and their result, and what you would change next. The model is already on their screen.
