# Active Invent Concept boundary v1

This immutable capability activates Concept only as a compound sub-boundary of
Forge and Quest Invent. The existing Invent Goal and native turn select the
Inventor, seal the invention, and author the complete pre-render Concept
source. After that turn exits, the trusted Workshop host alone validates the
source, performs any authorized durable image effect, seals the exact returned
bytes, and advances the one Invent gate directly to Make.

The capability never adds a Concept stage, Goal, turn, checkpoint, transition,
or status value. Spark has no Invent stage and does not activate this boundary.
Runs that did not freeze these exact bytes retain their prior protocol.

Concept research and images are design instruction, not product, Playtest,
manufacture, publication, delivery, or physical evidence. Provider credentials
and private effect state remain host-only.

When `STAGE.json.inputs.invent_concept_capability` binds these exact bytes, the
Manager and selected Inventor must author, at the packet-named `concept_root`,
exactly these five JSON files before the one Invent finalizer call:

- `brief.json`: decided object/category, envelope, wall thickness, print
  stance, distinctive features, fit target, stable component keys with exact
  form/dimensions/placement/interfaces, and one source-or-decision attribution
  for every required fact;
- `research.json`: bounded sources with exact excerpt hashes and retrieval
  times, plus findings that cite only recorded source ids;
- `prompts.json`: presentation treatment and exact instructions for `front`,
  `top`, `bottom`, `exploded`, and every stable component. Preserve the declared
  dependency order: front; top/bottom from front; exploded from all three;
  components from front only;
- `descriptor.json`: one distinct permitted image path for every overall and
  component role, with path-only leaves; and
- `derived_wish.json`: the original Wish words and context unchanged, plus the
  researched physical constraints that Make must obey.

Do not add source files, placeholder values, rendered images, provider ids, or
credentials. Reconcile component names across the Invented source, brief,
prompts, descriptor, and mechanism before finalizing. On a revision, use the
packet's exact standing sealed Concept and revision evidence; author a fresh
round tree rather than editing or reusing the old one.

Invoke exactly one ready finalizer after both the four-field creative source
and five-file tree are complete:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent --source <invent-source.json> \
  --concept-root <STAGE.json.inputs.concept_root>
```

The finalizer only validates, derives provenance, and preserves exact bytes.
It never researches, composes prompts, renders, reads credentials, judges
meaning, seals returned images, or advances the lifecycle. After it succeeds,
complete the same Invent Goal and return control. The host performs authorized
effects after the native process exits and may later resume this same session
at Make; do not invoke another finalizer for host-rendered bytes.
