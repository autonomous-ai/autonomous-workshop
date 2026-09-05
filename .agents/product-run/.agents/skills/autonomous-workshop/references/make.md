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

Do not delete `__cadgen__` or use `--fresh` inside the product sandbox. The
trusted host owns the isolated fresh rebuild. Keep caches, temporary work,
transcripts, and duplicate render families outside the sealed product tree.

## Required final product

Leave the tree at the exact `product_root` from `STAGE.json`. It contains:

- the exact nonempty root files named by `STAGE.json.required_root_files`:
  `product.json`, `assembled.step`, `assembled.step.json`, and `assembled.stl`;
- for a combined model whose `assembled.step.json` (the cadgen
  assembly-package) lists two or more occurrences, one printable mesh per
  occurrence at `parts/<occurrence-name>.stl`, one shell each, named exactly
  as the package names the occurrence (`STAGE.json.production_parts_rule`).
  The host rejects a multi-part Make without them. The shop receives these
  files as its addressable parts and renders each in the colour sealed on it;
- a surface colour on every leaf part of a multi-part model, authored as
  `Color(r, g, b)` with channels 0..1 taken directly from the sRGB hex you want
  the shop to show (`Color(0.82, 0.51, 0.18)` shows as `#d1822e`). Do not
  pre-convert channels to linear; the STEP, the GLB, the host renders, and the
  listing all read the sealed channels as sRGB;
- `product.json` with nonempty `title` and `summary` strings. Both are
  customer copy that reaches the shop unchanged: the title is a sayable name
  of one to four words with no dimensions, part counts, or sentences, and
  neither may use Workshop vocabulary (Wish, Taste, Goal, Make, Release,
  Playtest, Spark, Forge, Quest, artifact, gate);
- the self-contained CAD project, source, generated STEP/STL, measurements,
  passing `measure/print-preflight.md`, and final
  `measure/verification-pipeline.md`;
- one canonical final render family under `<cad-project>/snap/`;
- `<cad-project>/snap/SIGNATURE-REVIEW.json` bound to the exact concept,
  preflight, and images.

The root `assembled.*` files are sealed delivery copies of the final combined
CAD output. They do not replace the self-contained CAD project or its isolated
verification. Before finalizing, confirm every packet-named root file exists as
a nonempty regular file; a nested combined export alone is not publishable.

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
