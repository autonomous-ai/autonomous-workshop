## 1. The agent door and its injectable launcher

- [x] 1.1 Add `src/inventor_workshop/agent_session.py` with `AgentSessionDoor` implementing `doors.ModelDoor`: constructor takes a caller-supplied process launch configuration (no hardcoded binary/vendor) and a per-role configuration mapping (tool/file access, workspace pre-population, wall-clock bound, dollar budget); reject construction with no launch configuration.
- [x] 1.2 Define the injectable process-launcher seam (mirroring `_http.py::Transport`): a callable taking the role, request, resolved per-role access configuration, a fresh workspace path, and the result-file path, returning the process's exit status plus captured stdout/stderr for diagnostics.
- [x] 1.3 Implement `AgentSessionDoor.run(role, request, budget_micros)`: refuse an unconfigured role before launching anything; create a fresh workspace per call; invoke the launcher with the role's configured tool/file access; enforce the wall-clock bound by terminating an overrunning process; read the fixed result-file path after exit.
- [x] 1.4 Implement budget enforcement: refuse a non-positive `budget_micros` before launching; terminate the process if the launcher reports spend crossing the ceiling; always report actual elapsed time and (when known) actual cost on both success and failure.
- [x] 1.5 Implement failure handling: non-zero exit, timeout, missing result file, or a result file that doesn't match the role's declared shape all raise one error type naming the role and the specific failure — never a partial or inferred result.
- [x] 1.6 Add `tools/agent_door_fixture.py`: a deterministic, in-process launcher (no subprocess, no network) that returns a canned structured result for each of this change's three roles (`wish-research`, `concept-images`, `exploded-view-check`), following the same "not a real provider, deliberately kept out of `src/`" convention as `tools/concept_fixture.py` and `tools/wish_research_fixture.py`.
- [x] 1.7 Tests in `tests/test_agent_session.py`: unconfigured role fails closed with no process launched; fresh/isolated workspace per call including concurrent calls; wall-clock and budget bounds are enforced and terminate the process; missing/malformed result file fails naming the role; non-zero exit fails naming the role; a failed call still reports elapsed time/cost; construction without a launch configuration is rejected; the fixture launcher serves each of the three roles deterministically with no process or network access.

## 2. Concept's three ports, agent-backed

- [x] 2.1 Add `src/inventor_workshop/concept_agent_adapters.py` with `AgentWishResearcher`, `AgentConceptArtist`, `AgentExplodeInspector`, each taking a `ModelDoor` and satisfying the existing `WishResearcher` / `ConceptArtist` / `ExplodeInspector` callable contracts from `concept.py`.
- [x] 2.2 `AgentWishResearcher.__call__`: build the door request from `WishResearchRequest`, call role `wish-research`, parse the structured result into a `WishResearch` using the same strict validation `wish_researcher_openrouter.py` already applies (missing fact raises, unattributed field raises, unknown cited source raises) rather than duplicating or loosening it.
- [x] 2.3 `AgentConceptArtist.__call__`: build the door request from one `ConceptImageRequest`, call role `concept-images`, write exactly one returned image to `request.workspace / request.filename`, return that filename.
- [x] 2.4 `AgentExplodeInspector.__call__`: build the door request from the exploded image path and `ConceptBrief`, call role `exploded-view-check`, return only component keys the request offered, rejecting an answer that names an unoffered key.
- [x] 2.5 Tests in `tests/test_concept_agent_adapters.py` against the fixture launcher from 1.6: each adapter satisfies its port's existing contract test shape (mirror the fixture-based cases already in `tests/test_concept_pipeline.py`); wish-research attribution refusals still fire; concept-images stays one-request-one-image; exploded-view-check never reports an unoffered key; each adapter calls the door with exactly the role name its capability already uses.
- [x] 2.6 Confirm via a `DefaultConcept` test using all three agent-backed adapters (fixture-driven) that Concept's own behavior — waiting, sealing, refining, refusal rules — is unchanged from the OpenRouter-backed path already covered in `tests/test_concept_pipeline.py`.
- [x] 2.7 Confirm the boundary stays honest: a `Workshop` wired with `DefaultConcept` built from the three agent-backed adapters (and nothing else) still parks at `make` with the existing `_missing_make` `Need` once Concept completes — this change does not, and must not appear to, unblock Make.

## 3. Documentation

- [x] 3.1 Update `docs/ARCHITECTURE.md`: describe the role vocabulary for Concept's three capabilities and the agent door's contract, noting that Make/Playtest remain unimplemented and are covered by a separate proposal.
- [x] 3.2 Update `README.md`'s "Connecting the shared Concept capabilities" table and surrounding text to include the agent-backed alternative for the three Concept capabilities, including the launch-command and per-role configuration shape and their environment variables (read through `load_dotenv`, no hardcoded vendor).
- [x] 3.3 Update `CONTRIBUTING.md`: document the role-scoped tool-access requirement for any agent-backed capability (an unchecked prompt-only boundary is not acceptable), alongside the existing streaming-LLM-call convention already recorded there.

## 4. Repository checks

- [x] 4.1 Run `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py'` and confirm the full suite passes with no network access.
- [x] 4.2 Run `workshop skills list`, `workshop schemas list`, `workshop inventors --root . --check-entrypoints`, and `workshop check inventors --run`.
- [x] 4.3 Run `python tools/verify_skill_locks.py`, `python tools/verify_snapshot_locks.py`, `python tools/scan_secrets.py`, and `git diff --check`.
- [x] 4.4 Confirm existing sealed showcase toys under `inventors/*/toys/` still verify against their recorded hashes — this change adds new producers of `ConceptImages`; it must not alter how any already-sealed one is read or re-derived.
