## 1. Research records and the port

- [x] 1.1 Add `WishResearchSource` to `src/inventor_workshop/jobs.py`: frozen record of `id`, `origin`, `title`, `excerpt`, `excerpt_sha256`, `retrieved_at`, with bounded text validation and a `to_dict()`; reject a source whose `excerpt_sha256` does not hash its own `excerpt`.
- [x] 1.2 Add `WishResearchFinding` to `jobs.py`: frozen record of `claim`, the brief `field` it decides, `source_ids`, and `decided_because`; reject a finding that carries both or neither.
- [x] 1.3 Add `WishResearch` to `jobs.py`: frozen record of `object`, `category`, `envelope_mm`, `wall_mm`, `features`, `print`, `components`, `fits`, `findings`, `sources`; validate every field the brief needs is present, that every `source_id` a finding names exists in `sources`, and that no field is left unattributed by any finding.
- [x] 1.4 Add `WishResearchRequest` to `src/inventor_workshop/concept.py`: frozen record carrying `wish`, `taste`, `blueprint`, `round`, mirroring `ConceptImageRequest`'s validation style; define `WishResearcher = Callable[[WishResearchRequest], WishResearch]`.
- [x] 1.5 Export the new names from `jobs.py.__all__`, `concept.py.__all__`, and `src/inventor_workshop/__init__.py`.
- [x] 1.6 Tests in `tests/test_concept_records.py`: a source whose hash does not match its excerpt is refused; a finding with both a source and a decision is refused; a research record citing an unknown source id is refused; a research record leaving a required brief field unattributed is refused.

## 2. Refusal rules over a breakdown

- [x] 2.1 Add the breakdown-quality checks to `concept.py`: refuse a features list whose only entry restates the Wish objective; refuse a lone component whose `form`, `placement`, and `interfaces` only restate the envelope; require a single-component breakdown to carry a finding stating the design is one printed part.
- [x] 2.2 Make every refusal a `ContractError` naming the rule that refused it, distinct from the `WaitingFor` path.
- [x] 2.3 Tests in `tests/test_concept_gen.py` for each refusal, asserting the error names its rule.

## 3. Brief derivation from research

- [x] 3.1 Change `derive_brief(context)` to `derive_brief(context, research)` in `concept.py`; keep the `context.previous is not None` refining path and `_accumulated_edits` exactly as they are.
- [x] 3.2 Delete `_DEFAULT_WALL_MM`, `_DEFAULT_ENVELOPE_MM`, the "signature interaction" feature fallback, the print orientation and supports fallbacks, and the single-`body` component fallback.
- [x] 3.3 Build `assumptions` from the research's `decided_because` findings, so each assumption carries its reason instead of the templated "The Wish did not state X".
- [x] 3.4 Keep `_components_from_constraints`: components already present in `wish.constraints` are honoured and recorded as decided by the Wish rather than researched.
- [x] 3.5 Tests in `tests/test_concept_gen.py`: a researched breakdown produces a brief stating its facts; a Wish carrying hand-authored components keeps them; no code path yields a 120×120×60 envelope or a `body` component unless research decided it.

## 4. Concept waits for the researcher

- [x] 4.1 Add `wish_researcher` to `DefaultConcept.__init__` and raise `Need("concept", "wish-research", …)` in `__call__` alongside the existing two needs when it is `None`.
- [x] 4.2 Call the researcher before the workspace's brief is locked, and only when `context.previous is None`; a refining round reuses the standing concept's research.
- [x] 4.3 Add `wish_researcher` to `WorkshopTools` in `src/inventor_workshop/workshop.py` with the same `_callable_or_none` validation as its siblings, and thread it into the `DefaultConcept` the Workshop builds.
- [x] 4.4 Tests in `tests/test_concept_pipeline.py`: no researcher parks the run at `concept` with capability `wish-research`; all three missing capabilities raise one `WaitingFor` carrying three needs; a refining round calls the researcher zero times.

## 5. Sealing the research with the concept

- [x] 5.1 Write `research/findings.json` and `research/sources/NNN.json` under the concept root before `ConceptImages.from_root`, so the existing manifest walk covers them.
- [x] 5.2 Extend `_write_descriptor` to record the research record's digest and to repeat the `valid_as_product_proof: false` provenance block for the research.
- [x] 5.3 Carry the research on `ConceptImages` and re-check it in `assert_current()` through the existing `_fresh_manifest` path.
- [x] 5.4 Tests in `tests/test_concept_records.py`: the sealed root contains the research; editing `research/findings.json` after sealing makes `assert_current()` fail; two identical briefs with different research seal to different `concept_sha256`.

## 6. Derived Wish write-back

- [x] 6.1 Build the derived `Wish` from the research in `concept.py`: routed `product_id`, `objective`, and `context` copied verbatim, `constraints` carrying the researched envelope, wall, features, print stance, fits, and components; refuse a derived record whose words differ from the routed Wish.
- [x] 6.2 Return the derived Wish from Concept alongside `ConceptImages`, and record `wish_sha256` and `derived_wish_sha256` in the run's `concept` payload in `workshop.py` next to `concept_sha256`.
- [x] 6.3 Build the round's `MakeContext` from the derived Wish so `Made.wish` and `artifact/wish.json` carry the researched constraints; leave the routed Wish object untouched.
- [x] 6.4 Verify resume restores the same derived Wish hash and rejects a restored state naming a different one.
- [x] 6.5 Tests in `tests/test_toy_workshop.py` and `tests/test_manager.py`: `RoutingContext.wish_sha256` is unchanged across a run; `artifact/wish.json` carries the researched constraints; `instructions.py`'s quoted objective is still the person's words; a derived Wish that altered the objective is refused.

## 7. Fixture researcher for tests and showcases

- [x] 7.1 Add `tools/wish_research_fixture.py` with the same "not a real provider, deliberately kept out of `src/`" module docstring as `tools/concept_fixture.py`, returning a deterministic breakdown whose findings are all marked as fixture decisions.
- [x] 7.2 Inject it in `tools/build_showcase_products.py` and across the test suites that today construct a `DefaultConcept`.
- [x] 7.3 Confirm `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py'` passes end to end with no network.

## 8. Real researcher adapter

- [x] 8.1 Add `src/inventor_workshop/wish_researcher_openrouter.py` with `OpenAICompatibleWishResearcher`: caller-supplied base URL, API key, and model; injectable `Transport` from `_http.py`; bearer auth; bounded response size; bounded retries on 429/5xx; immediate failure on other 4xx.
- [x] 8.2 Build the request from the Wish objective and constraints, the Taste description, and the lane category, instructing the endpoint to attribute each fact and to say where it had no source; enable the endpoint's web search facility.
- [x] 8.3 Parse the answer strictly into a `WishResearch`: raise naming the missing fact rather than defaulting it, raise on an unparseable answer rather than returning an empty breakdown, and raise on a cited source with no returned origin or excerpt.
- [x] 8.4 Add a `from_env()` constructor reading `WISH_RESEARCHER_BASE_URL`, `WISH_RESEARCHER_API_KEY`, and `WISH_RESEARCHER_MODEL` through `load_dotenv`, matching the existing adapters.
- [x] 8.5 Tests in a new `tests/test_wish_researcher_openrouter.py` against a fake transport, covering construction validation, request shape, strict parsing, and each failure path; no real network calls.

## 9. Documentation and checks

- [x] 9.1 Update `docs/ARCHITECTURE.md`'s Concept paragraph and job-contract diagram to read research → brief → images, and name `wish-research` among the capabilities a run can wait for.
- [x] 9.2 Update `README.md` where it describes what a run waits for, and add the new env variables to the adapter configuration notes.
- [x] 9.3 Run the full check list from `README.md` — unittest discovery, `workshop check inventors --run`, `verify_skill_locks.py`, `verify_snapshot_locks.py`, `scan_secrets.py`, `git diff --check` — and confirm the sealed showcase toys under `inventors/*/toys/` still verify against their recorded hashes.
