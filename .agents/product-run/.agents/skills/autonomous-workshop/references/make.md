# Make contract

Read `STAGE.json` once. It binds the sealed Wish, Invent result, selected
Inventor, exact output root, round, transition, and any host rejection. Repair
the cited bytes when a rejection exists; never resubmit unchanged work.

Create or continue one Make Goal. Its objective is the exact printable product
that satisfies the sealed concept and Wish. Its stopping condition is a
successful `make` finalizer writing `agent-outcome.json`. Only an exact
build-blocking contradiction may use the optional
`make-invent-revision-v1.md` route.

## Critical path

For Forge and Quest, trust the sealed Invent contract. Do not repeat research,
roster comparison, or broad concept exploration. For Spark, rank the complete
roster once from `STAGE.json`'s compact `inventor_discovery_index`, read only
the best three full custom-agent TOMLs, select the Inventor whose Taste owns
the hardest-to-fake magic, and write one compact source with exactly
`selected_inventor_id`, roster-covering `ranking`, `concept`, and `research`.

During a frozen deep-v8 or deep-v9 proof turn, follow the host prompt literally. Create or
continue the Make Goal immediately, then inspect the required stable
instructions, stage packet, and sealed concept in one bounded batch rather than
separate tool calls. Write source and its parent directories in the next file
edit before optional reading or help discovery. The broad CAD skill is
deliberately not applicable until the proof marker exists: the host already
supplies the complete proof interface. Do not inspect an empty product tree,
create an empty directory as separate work, or spawn an early critic. Persist
exact mechanism/relationship evidence, neutral held/signature blockout images,
and one compact root visual finding under
`<cad-project>/review/early-proof/`. The canonical independent blind critic
remains mandatory during final Make. The host-provided
`.make-proof-ready.json` marker ends only that native turn; it never advances
Make. The resumed high-reasoning turn must reuse the passing proof rather than
restart, and only then loads the broad CAD skill.

Replace the bracketed paths from `STAGE.json`; do not invoke help to rediscover
this interface or configure a cache. The host binds a private writable
`XDG_CACHE_HOME`. The proof entry defines exactly one module-scope `gen_step()`
and returns the build123d shape. Generate, export, and render it in this order
inside one foreground tool call so no agent reasoning cycle separates the
deterministic commands:

```bash
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen <entry.step.py> --write
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/export <entry.step> --stl
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/render_product <entry.stl> \
  -o <cad-project>/review/early-proof/held.png \
  --motion-sheet <cad-project>/review/early-proof/signature.png \
  --motion-angles=-12,0,12
```

Use one product funnel:

1. Write the smallest viable parametric baseline with exactly one non-part
   combined `*.step.py` entry and one `part_<role>.step.py` per printable part.
2. Generate explicit source targets with
   `.agents/skills/cad/scripts/gen <entry.step.py> --write`. Export STL from the
   fresh STEP with `.agents/skills/cad/scripts/export <entry.step> --stl`.
3. Run only narrow checks affected by an edit. Once the baseline is plausible,
   run `.agents/skills/cad/scripts/verify_project <cad-project>
   --print-preflight` without `--fresh`. It must cover every printable at the
   fixed 0.4 mm nozzle standard.
4. Render the exact STL to `<cad-project>/snap/iso.png` (at least 800×800 RGB)
   and `<cad-project>/snap/signature.png` (at least 1200×800 RGB). When the
   promise changes product geometry or state, generate distinct exact-state
   STLs and use `render_product --state-sheet ... --state-stl ...` at one fixed
   view. `--motion-sheet` rotates one unchanged mesh and is only presentation
   viewpoint evidence; it can never prove a state transition. The signature
   sheet must show the promised states or interaction, not repeated angles.
5. Give one independent native critic only those images. Record its blind held
   object, volumetric form, subjects, action, and relationship. Then reveal the
   Wish and concept and check every positive and negative held-form constraint.
   Make one focused repair at most and one blind rereview at most.
6. Run the integrated final verifier once. Do not use it as an iteration loop.
7. Write product metadata and invoke the Make finalizer immediately.

## Marked Concept handoff

When `STAGE.json.inputs.invent_concept_capability` is present, the packet also
contains `required_product_component_keys`. These are the stable Concept
component keys, not implementation-specific CAD variants or repeated physical
instances. One Concept component may produce multiple variant models or
multiple manufactured instances; `product.json.components` must still contain
each packet key exactly once. Copy the packet's exact key set into the root
product metadata before detailed CAD work; do not derive aliases from filenames
or expand one key per variant:

```json
{
  "title": "Product title",
  "summary": "Bounded product summary.",
  "components": ["component-key-a", "component-key-b"]
}
```

The `components` array has each packet key exactly once, with no omission,
alias, renamed counterpart, duplicate, side suffix, or extra. Reopen the bound
sealed Concept and effect evidence before building. Brief and derived-Wish
numbers are authoritative; Concept images communicate design intent but do not
prove geometry, fit, printability, or completion. Generate all product geometry
and presentation evidence freshly. Never copy sealed Concept image bytes into
the product tree, even under another filename.

Do not manually delete `__cadgen__` or use `--fresh` inside the product
sandbox. The trusted host owns the isolated fresh rebuild. The finalizer safely
removes ordinary derived-cache files before hashing. If the sandbox protects a
now-empty cache directory from removal, leave it in place: byte-free
directories are ignored by both the finalizer and host gate, so never report an
empty cache directory as a blocker. Keep temporary work, transcripts, and
duplicate render families outside the sealed product tree.

## Required final product

Leave the tree at the exact `product_root` from `STAGE.json`. It contains:

- `product.json` with nonempty `title` and `summary` strings, plus the exact
  `components` array above for a marked Concept packet;
- the self-contained CAD project, source, generated STEP/STL, measurements,
  passing `measure/print-preflight.md`, and final
  `measure/verification-pipeline.md`;
- one canonical final render family under `<cad-project>/snap/`;
- `<cad-project>/snap/SIGNATURE-REVIEW.json` bound to the exact concept,
  preflight, and images.

The canonical schema-v6 review contains exactly: `schema_version`, `kind`,
`concept_sha256`, `iso_sha256`, `signature_sha256`, `reviewer`,
`blind_held_read`, `blind_form_read`, `blind_subjects_read`,
`blind_action_read`, `blind_relationship_read`,
`anti_generic_signature_read`, `wish_revealed_after_blind_read`,
`held_object_unmistakable`, `form_matches_wish`, `subjects_match_wish`,
`action_matches_wish`, `relationship_matches_wish`,
`anti_generic_signature_visible`, `signature_experience_unmistakable`,
`finished_product_desirable`, `review_rounds`, `critical_form_requirements`,
`blocking_visual_defects`, `print_preflight_sha256`, `largest_risk`, and
`resolution`. Use kind `autonomous-workshop.signature-experience-review`.
Every boolean is true; `review_rounds` is one or two; blockers are empty; each
critical requirement has exactly `requirement`, `blind_evidence`, and
`matches: true`. A generic object, flat/plaque form, exposed mechanism,
ambiguous action, wrong relationship, raw prototype, or visible caveat is a
blocker, not prose to waive.

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <STAGE product_root> \
  --cad-project-path <path inside product root> \
  --cad-verification-path <path inside product root>
```

For Spark only, also pass `--source <spark-source.json>`. Do not pass it when
`STAGE.json` already contains sealed assignment and Invented inputs. Complete
the Goal and return immediately after the finalizer succeeds. The host then
rehashes the complete tree and reruns the authoritative isolated CAD gate.

Digital evidence never proves a successful print, tactile fit, durability,
comfort, discoverability, or human delight. Quest Playtest owns its separate
evidence; Spark and Forge truthfully record Playtest as not run.
