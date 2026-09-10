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
and returns the build123d shape. Generate and render it in this order inside
one foreground tool call so no agent reasoning cycle separates the
deterministic commands:

```bash
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen <entry.step.py> --write
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/render_product <entry.step> \
  -o <cad-project>/review/early-proof/held.png \
  --motion-sheet <cad-project>/review/early-proof/signature.png \
  --motion-angles=-12,0,12
```

When the Wish supplies images or names an existing object, follow
[visual-reference-inspection.md](visual-reference-inspection.md) before
committing the form: prefer the sealed `wish-references/`, search for one when
the Wish names an object and attaches none, and label a text-derived
interpretation as such when neither is reachable rather than stopping the run.

STEP is the only geometry format the toolchain writes. `render_product`
tessellates the exact STEP in memory and there is no mesh export. The print
gates do the same: `check_mesh`, `check_overhang` and `check_thickness` build
each printable entry from source and measure its tessellation in the gate, so
printability is checkable again without a mesh deliverable. Call a product
print-ready only behind a passing `--print-gates` run at the nozzle the print
will use.

## Ownership and pipeline

Make owns the stage inputs and output paths, independent blind review, bounded
visual repair, final product contract, and Make finalizer. The materialized
`cad` skill owns CAD planning, modeling methods, applicable progressive
references, source layout, generation, exports, printability, geometry checks,
image-derived checks, rendering mechanics, and CAD verification. Inventor
guidance owns specialist form and character judgment. A CAD artifact or gate
named here is a required Make outcome, not a replacement for an applicable
CAD-skill step. The host retains stage authority and the final deterministic
product gate.

Follow the applicable CAD pipeline when the frozen Make profile permits loading
the skill. Existing early-proof turns keep their prescribed narrow commands and
skill deferral. This ownership split does not change their handoff or introduce
a direct Make route.

Use one product funnel:

For final Make, this reference owns the visual repair allowance and supersedes
the older one-repair wording in economics references: allow three focused
repair-and-rereview cycles after the initial independent review (four reviews
total), within the run's remaining budget. Early-proof and manual-review limits
are separate. Frozen older runs retain their materialized rules and tools.

1. Write the smallest viable parametric baseline with exactly one non-part
   combined `*.step.py` entry and one `part_<role>.step.py` per printable part.
2. Generate explicit source targets with
   `.agents/skills/cad/scripts/gen <entry.step.py> --write`, which writes the
   sibling `.step`. That STEP is the only geometry artifact.
3. Run `make_round` after each source repair and inspect its exact visual packet.
   The Manager records misplaced, missing or extra parts, size/proportion
   mismatches, visible intersections, and form defects with image evidence and
   a concrete repair using `--record-visual`. Inspect the actual views even when
   likeness passes or no reference image exists. Pending or inconclusive visual
   feedback is not a pass. These self-checks do not replace independent review.
   Run only additional narrow checks affected by an edit. `make_round` gates
   every part that builds with `check_thickness` and `check_overhang` at the
   fixed 0.4 mm nozzle standard, so a wall or overhang defect surfaces in the
   round that caused it rather than at final verification.
4. Render the exact STEP to `<cad-project>/snap/iso.png` (at least 800×800 RGB)
   and `<cad-project>/snap/signature.png` (at least 1200×800 RGB). When the
   promise changes product geometry or state, generate distinct exact-state
   STEPs and use `render_product --state-sheet ... --state-source ...` at one
   fixed view. `--motion-sheet` rotates one unchanged shape and is only presentation
   viewpoint evidence; it can never prove a state transition. The signature
   sheet must show the promised states or interaction, not repeated angles.
5. For a moving mechanism, also produce and review exact-state animation using
   [motion review](motion-review-v1.md); still images cannot establish motion.
   Give one independent native critic only the images and that animation. Record its blind held
   object, volumetric form, subjects, action, and relationship. Then reveal the
   Wish and concept and check every positive and negative held-form constraint.
   Allow up to three focused repairs, each followed by regenerated preflight,
   images and an independent rereview. Stop as soon as the review passes.
6. Run the integrated final verifier once. Do not use it as an iteration loop.
7. Write product metadata and invoke the Make finalizer immediately.

Complete the blind signature review and, if needed, up to three focused repairs before
running the integrated final verifier once. The review must separately match the exact subjects,
action, and spatial/causal relationship; matching only nouns is a failure.
Enumerate every explicit positive and negative held-form requirement from
the Wish in the review's `critical_form_requirements`; each entry needs
exact blind visual evidence. Any visible departure from one of those
requirements belongs in `blocking_visual_defects`, not in a nonblocking
caveat. Use one critic and no more than four review rounds (initial plus three
rereviews). On rereview, record fresh image observations before comparison and
disclose that the critic already knows the Wish; do not claim naive recognition.
After the fourth failed review, preserve the failures and finalize a truthful
failed need rather than exceeding the allowance. Do not use the
full verifier as the visual iteration loop. Any geometry change after the
review invalidates it and requires a fresh blind read of the regenerated
images; copying old prose and replacing hashes is not a review.

Do not manually delete `__cadgen__` or use `--fresh` inside the product
sandbox. The trusted host owns the isolated fresh rebuild. The finalizer safely
removes ordinary derived-cache files before hashing. If the sandbox protects a
now-empty cache directory from removal, leave it in place: byte-free
directories are ignored by both the finalizer and host gate, so never report an
empty cache directory as a blocker. Keep temporary work, transcripts, and
duplicate render families outside the sealed product tree.

## Required final product

Leave the tree at the exact `product_root` from `STAGE.json`. It contains:

- the exact nonempty root files named by `STAGE.json.required_root_files`:
  `product.json`, `assembled.step`, and `assembled.step.json`;
- for a combined model whose `assembled.step.json` (the cadgen
  assembly-package) lists two or more occurrences, one production solid per
  occurrence at `parts/<occurrence-name>.step`, one solid each, named exactly
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
- the self-contained CAD project, source, generated STEP, measurements, the
  passing `measure/thickness-<role>.md` and `measure/overhang-<role>.md`
  reports for every printable part, and final
  `measure/verification-pipeline.md`;
- one canonical final render family under `<cad-project>/snap/`;
- `<cad-project>/snap/SIGNATURE-REVIEW.json` bound to the exact concept,
  images, and print-gate reports.

The root `assembled.*` files are sealed delivery copies of the final combined
CAD output. They do not replace the self-contained CAD project or its isolated
verification. Before finalizing, confirm every packet-named root file exists as
a nonempty regular file; a nested combined export alone is not publishable.

The canonical schema-v8 review contains exactly: `schema_version`, `kind`,
`concept_sha256`, `iso_sha256`, `signature_sha256`, `reviewer`,
`blind_held_read`, `blind_form_read`, `blind_subjects_read`,
`blind_action_read`, `blind_relationship_read`,
`anti_generic_signature_read`, `wish_revealed_after_blind_read`,
`held_object_unmistakable`, `form_matches_wish`, `subjects_match_wish`,
`action_matches_wish`, `relationship_matches_wish`,
`anti_generic_signature_visible`, `signature_experience_unmistakable`,
`finished_product_desirable`, `review_rounds`, `critical_form_requirements`,
`blocking_visual_defects`, `print_gate_sha256s`, `largest_risk`, and
`resolution`. Use kind `autonomous-workshop.signature-experience-review`.
`print_gate_sha256s` maps each cited `measure/<gate>-<role>.md` report, relative
to the CAD project, to its exact sha256. Bind every printable part's passing
thickness and overhang reports there and seal product status
`full-with-thickness` with `print_ready_claim: true`; leave the map empty and
seal `digitally-verified-not-print-ready` with `false` when the round did not
open the print gates, and then never call the product print-ready. The host
reruns the verifier in the tier those two declarations name, so a claim the
sealed project cannot reproduce is refused rather than downgraded.
Every boolean is true; `review_rounds` is an integer from one through four; blockers are empty; each
critical requirement has exactly `requirement`, `blind_evidence`, and
`matches: true`. Evaluate form against the actual Wish: an exposed mechanism
or a flat component is not inherently a defect. Wrong required relationships,
unresolved geometry defects, and unproved promised functions remain blockers.

Separate immutable user requirements from inventor-selected styling. In Spark,
before the final review, revise nonessential naming, species, palette or
styling decisions when the result suggests a better fit; preserve the previous
choice and reason in `research.design_changes`. Keep the required function,
constraints and distinctive experience. The final concept, product, manual
and review must agree. Never retroactively rewrite a failed review or simply
change hashes. Forge/Quest sealed concepts still require their existing
authorized revision path. A missing function cannot become a styling change.

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
the Goal and return immediately after the finalizer succeeds. The host seals
the exact submitted bytes. Forge and Quest additionally run their isolated CAD
verification; Spark accepts Make's output without repeating that verification.

Digital evidence never proves a successful print, tactile fit, durability,
comfort, discoverability, or human delight. Quest Playtest owns its separate
evidence; Spark and Forge truthfully record Playtest as not run.
