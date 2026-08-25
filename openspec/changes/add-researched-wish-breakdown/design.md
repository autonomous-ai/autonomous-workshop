## Context

See `proposal.md` — Why. The relevant constraints on the approach:

- `DefaultConcept` (`src/inventor_workshop/concept.py:574`) already takes optional capabilities and raises `WaitingFor` with one `Need` per missing one. A third capability fits that shape with no new mechanism.
- `ConceptImages.from_root` builds its manifest with `build_artifact_manifest(root, created_at="content-addressed")`, which walks the whole concept root. Anything written under the root before sealing is hashed into `concept_sha256` automatically, and `assert_current()` re-checks it. A `research/` subtree therefore needs no new sealing machinery.
- `Wish` is frozen and `_copy_mapping` round-trips its constraints through JSON, so a "derived Wish" is a second `Wish` instance, not a mutation.
- `RoutingContext` (`src/inventor_workshop/manager.py:563`) computes and re-asserts `wish_sha256` over the routed Wish. That object must keep its bytes, or every routing and shortlist binding breaks.
- `derive_brief` already has a second job unrelated to defaults: on a refining round it carries the standing brief forward and folds `_accumulated_edits` into `assumptions`. That path stays.
- The repo has no HTTP dependency; `_http.py` supplies `Transport` / `HttpResponse` / `make_urllib_transport`, and both existing adapters take an injectable transport so tests never touch the network.

## Goals / Non-Goals

**Goals:**

- One seam for research, injected the same way the artist and inspector are, so an operator wires all three the same way.
- The brief's numbers become checkable: each is either attributable to a recorded source or to a recorded decision, and the check is mechanical, not a matter of taste.
- The research travels with the concept and is covered by `concept_sha256`, so a concept cannot be re-explained after the fact.
- Later jobs receive constraints worth having, without losing the person's exact words or the identity routing was decided from.

**Non-Goals:**

- Re-deriving or re-sealing the existing showcase toys under `inventors/*/toys/`. Their recorded hashes stand.
- Independently re-fetching cited URLs to prove they still say what was read. The record is a record of the research, not a live claim about the web.
- Judging research quality. The rules here are about attribution and completeness; whether a finding is *good* is Playtest's problem.
- Changing the six-job vocabulary, stage transitions, or blueprint task coverage.

## Decisions

### Research is a Concept capability, not a seventh job

Adding a `wish` breakdown job would touch `WORKSHOP_JOBS`, stage transitions, every blueprint's declared tasks, `Need.job` validation, run-state payloads, and the archived `workshop/concept-job` requirement that the job set is exactly six. The value is entirely in *what the brief contains*, and the brief is Concept's output.

**Alternative considered:** a job between Wish and Make that writes constraints onto the Wish. Rejected — same result, much larger blast radius, and it would split "decide the physical facts" across two jobs.

**Alternative considered:** an offline `tools/` script an operator runs before creating the Wish. Rejected — the breakdown would sit outside the seal, so nothing would stop a concept being drawn from constraints nobody recorded.

### The port shape mirrors `ConceptArtist`

```python
WishResearcher = Callable[[WishResearchRequest], WishResearch]
```

`WishResearchRequest` carries the `Wish`, the `Taste`, the `ToyBlueprint`, and the round. `WishResearch` is a frozen record of `findings` (each: a claim, the brief field it decides, and either `source_ids` or `decided_because`), `sources` (each: `id`, `origin`, `title`, `excerpt`, `excerpt_sha256`, `retrieved_at`), and the decided fields the brief needs. `DefaultConcept` gains a `wish_researcher` argument; `WorkshopTools` gains a matching field so it is installed once per Workshop.

Keeping the researcher's return a *record of decisions* rather than a `ConceptBrief` means the attribution rules are enforced by the Workshop in one place, not trusted from each provider.

### `derive_brief` becomes `derive_brief(context, research)`

It keeps the refining-round path unchanged and drops `_DEFAULT_WALL_MM`, `_DEFAULT_ENVELOPE_MM`, the "signature interaction" feature fallback, the orientation and supports fallbacks, and the single-`body` component fallback. Where research recorded a decision rather than a source, that decision's text becomes the assumption line — which is why the assumption strings stop being templated "The Wish did not state X" and start carrying a reason.

`_components_from_constraints` stays: a Wish that already carries hand-authored components is still honoured, and those components are recorded as decided-by-the-Wish rather than researched.

**Alternative considered:** having the researcher return a `ConceptBrief` directly, via the existing `brief_maker` hook. Rejected — `brief_maker` is the escape hatch for an inventor that already knows its own facts and deliberately bypasses attribution; folding research into it would make the two indistinguishable and leave the citation rules unenforced.

### The research record lives under the concept root

```
<concept root>/
  concept.json          # descriptor, gains a research binding
  images/…
  research/
    findings.json       # claim -> brief field -> source ids | decided_because
    sources/001.json    # origin, title, excerpt, excerpt_sha256, retrieved_at
```

Written before `ConceptImages.from_root`, so the manifest covers it and `assert_current()` protects it. `concept.json` records the research record's own digest and repeats the `valid_as_product_proof: false` provenance block, so the honest-labelling rule that already governs concept art governs research too.

**Alternative considered:** a sibling directory outside the concept root. Rejected — it would not be sealed, and `_inside(concept.root, concept_workspace, …)` would have nothing to check.

### Write-back is a derived `Wish`, and it is what Make receives

Concept returns the derived `Wish` alongside `ConceptImages`. The Workshop builds that round's `MakeContext` from the derived Wish, so `Made.wish` — and therefore `artifact/wish.json` — carries the researched constraints. `product_id`, `objective`, and `context` are copied verbatim, which is what keeps `instructions.py`'s `"wish": context.wish.objective` quoting the person's own words, and keeps `RoutingContext.wish_sha256` valid because the routed object is never touched.

The run's `concept` payload records `wish_sha256` (routed) and `derived_wish_sha256` next to `concept_sha256`, so the pair is recoverable on resume and a swap is detectable.

**Alternative considered:** mutating `Wish.constraints` in place. Impossible without breaking the frozen record, and it would silently invalidate every routing binding taken over the original bytes.

**Alternative considered:** leaving `MakeContext.wish` as the routed Wish and passing constraints only through the brief. Rejected — the brief is the binding contract for geometry, but the Wish is what `Workbench.make` forwards to the CAD adapter (`src/inventor_workshop/make.py:410`), so constraints that never reach the Wish never reach CAD.

### Refusals are contract errors, waits are `Need`s

A missing researcher is a `WaitingFor(Need("concept", "wish-research", …))` — the capability is absent, so the run parks and can resume. A researcher that returns an unattributed fact, a missing field, or a placeholder component is a `ContractError` naming the rule that refused it — the capability ran and produced something the Workshop will not seal. Retrying that automatically would be the "try again blindly" the README rules out.

### The real adapter follows `OpenAICompatibleExplodeInspector` exactly

`OpenAICompatibleWishResearcher` in a new `src/inventor_workshop/wish_researcher_openrouter.py`: caller-supplied base URL, API key, model; injectable transport; bounded response size; bounded retries on 429/5xx; immediate failure on other 4xx. Web search is enabled through the request's plugin/tool field, and the endpoint's returned source annotations become the `sources` list. Nothing is wired into an inventor by the module.

Env names follow the existing convention (`WISH_RESEARCHER_BASE_URL`, `WISH_RESEARCHER_API_KEY`, `WISH_RESEARCHER_MODEL`), read through `load_dotenv`.

### Tests and the showcase builder get a fixture, kept out of `src/`

`tools/wish_research_fixture.py`, alongside `tools/concept_fixture.py` and for the same stated reason: it must never be installable into a real Workshop. It returns a deterministic breakdown derived from the Wish text with its findings marked as fixture decisions, so the pipeline runs end to end offline while nothing in it can be mistaken for research that happened.

## Risks / Trade-offs

- **Every existing caller that reached Make now parks at Concept.** → Intended, and stated as **BREAKING** in the proposal. Mitigated for the repo's own suites by the fixture researcher; mitigated for operators by a `Need` whose instructions name exactly what to configure.
- **Attribution is checkable, truthfulness is not.** A provider can cite a source that says nothing of the kind. → The record makes the claim inspectable — origin, excerpt, and hash are all there for a human or a later check to read. This change buys accountability, not correctness, and the specs say so.
- **A model-authored breakdown can still be wrong about the world.** → It is bounded by the same Playtest loop that already exists: a bad design comes back as feedback, and `_design_edits` folds it into the standing brief rather than restarting.
- **`MAX_CONCEPT_COMPONENTS` is 12**, and a real object can want more (a chess set has six piece types plus a board — it fits; a 32-piece set enumerated individually would not). → Components are part *types*, not instances; the count per type belongs in the component's `purpose` and `placement` text. Called out because a researcher that enumerates instances will hit the cap, and the refusal message should say why.
- **Research adds a slow network call at the top of round 1.** → It runs once per run, not once per round: refining rounds reuse the standing research. Bounded retries and a response-size cap match the existing adapters.
- **The excerpt hash proves what was recorded, not what the URL said.** → Explicitly a non-goal above, and the spec words it as "the excerpt relied upon" rather than as a claim about the source's current content.

## Migration Plan

1. Land the port, the records, and the refusal rules with `DefaultConcept` still accepting `wish_researcher=None` in its signature — but raising the `Need` when it is `None`. There is no compatibility window where a default brief is produced.
2. Land the fixture researcher and switch the test suite and `tools/build_showcase_products.py` onto it in the same change, so the suite never goes red.
3. Land the real adapter last; it is inert until an operator constructs it.

Rollback is reverting the change: no persisted format outside a concept root changes shape, and existing sealed toys are untouched either way.

## Open Questions

- Whether `findings.json` should record the researcher's model identity and the request parameters alongside the sources. It would strengthen provenance and costs nothing at seal time, but it is additive to the record and does not change any requirement here, so it can be added later without disturbing the specs or the task breakdown.
