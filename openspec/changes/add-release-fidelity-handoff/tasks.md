## 1. Assembly-package handoff and part colours (PR 1)

- [x] 1.1 Add `src/workshop/make/assembly_package.py` with a typed reader for the cadgen assembly-package (`kind`, `schemaVersion 2`, `packageSchemaVersion >= 3`, ordered occurrences with safe unique names, finite transforms, count check); unit tests under `tests/make/test_assembly_package.py` cover Quarterhoot-shaped input, single occurrence, duplicate and unsafe names, and malformed documents.
- [x] 1.2 Extend `factory._occurrence_transport` with the assembly-package branch resolving `parts/<name>.stl`, keeping Factory-sidecar and native-descriptor precedence; verify `tests/integrations/test_factory.py` shows `assembled_parts/<name>.stl`, the synthesized sidecar, shell inspection, and single-mesh fallback with a recorded `handoff_transport_reason`.
- [x] 1.3 Verify the existing `factory-part-colors` effect fires for a two-occurrence package with two STEP colours (intent, PATCH body by `mesh_name`, readback assertion) and stays silent for a single-colour single mesh.
- [x] 1.4 Add the Make gate rule in `native_gate`: ≥ 2 occurrences require `parts/<name>.stl` (one shell each) and an `assembled.stl` with `occurrence_count` shells; rejection names the missing part; tests in `tests/make/test_native_cad_gate.py`.
- [x] 1.5 List the requirement in the Make finalizer inputs (`native_run`) and the product-run `autonomous-workshop` skill text; verify materialized template tests.
- [x] 1.6 Record `handoff_transport` and `occurrence_count` in the release receipt and `workshop status`; add `changes/factory-assembly-package-handoff.added.md`.

## 2. Colour convention (PR 2)

- [x] 2.1 Keep the vendored cadgen GLB exporter untouched (locked skill bytes) and align the reader instead: `read_step_part_colors` reports sealed channels as the sRGB hex the viewer shows, so STEP, GLB, host renders, and Factory `part_colors` agree; tested in `tests/make/test_step_color.py` and `tests/make/test_assembly_package.py`.
- [x] 2.2 The CAD skill tree is byte-locked, so the colour authoring rule lives in the repository-authored `references/make.md` (author `Color(r, g, b)` from the sRGB hex directly, never pre-converted); fragment `changes/cad-step-colour-srgb.fixed.md`.

## 3. Host-owned product renders (PR 3)

- [x] 3.1 Add `tools/render/` with a vendored three.js 0.160 bundle, the playwright launcher, pinned versions, and a `THIRD_PARTY_NOTICES.md` entry; add the doctor check (node, playwright, chromium smoke render).
- [x] 3.2 Add `src/workshop/release/renders.py`: scene assembly from `parts/<name>.stl` + package transforms + STEP colours (single-mesh path from `assembled.stl`), hero/turnaround/state-strip rendering under `minimal_tool_environment` with time and size bounds, Pillow re-validation, `renders.json` binding to the Made product sha, and the `unavailable` fallback; tests with a fake renderer and with the real renderer skipped when node is absent.
- [x] 3.3 Accept optional `presentation.states` in Make `product.json` (2–5 sealed STL paths) and reuse the state-difference rule for the strip; contract tests in `tests/make`.
- [x] 3.4 Run the render step in `native_run` after a passing Make CAD gate; list `renders/` in the Release stage inputs; verify a failing or missing renderer leaves Release identical to today.
- [x] 3.5 Extend `manual_design.validate_manual_design_evidence` to accept `renders/` sources bound through `renders.json`; tests in `tests/release/test_manual_design.py` for accepted, stale, and tampered renders.
- [x] 3.6 Update the materialized `manual-design` skill to prefer host renders for the cover and signature spread; add `assembled_review/_assembled.png` (hero) to the handoff zip and assert it in adapter tests; add `changes/host-product-renders.added.md`.

## 4. Session history (PR 4)

- [x] 4.1 Add `authorization.json` schema 3 with `history_disclosure_requested`, `workshop wish --disclose-session`, and an Inventor-account default in config; schema-2 files read as `false`; tests in `tests/workflow`.
- [x] 4.2 Add `src/workshop/release/session_history.py`: rollout discovery by `thread_id`, record mapping (Wish/summary opener, user Goals, assistant text, tool_use/tool_result pairs), omission of reasoning/developer/event records, redaction, caps, deterministic ordering; fixture-driven tests including a Quarterhoot-shaped rollout excerpt and an oversized tool output.
- [x] 4.3 Ship `conversation.jsonl` at the handoff root when authorized; allow-list it in `_assert_archive_inventory`; verify `pack_sha256` changes and the ledger binds it without a schema change.
- [x] 4.4 Record `history_turns` from `GET /designs/{slug}/turns` after publish (warning on mismatch); show it in `workshop status`.
- [x] 4.5 Update `docs/PUBLISH_SEALED_PRODUCT.md`, `docs/NATIVE_AGENT_RUNTIME.md`, and the public-example README sentence to state what the Factory listing carries when history is disclosed; add `changes/factory-session-history.added.md`.

## 5. Acceptance

- [x] 5.1 Run the full offline suite (`PYTHONPATH=src python -m unittest discover -s tests -t . -p 'test_*.py'`), `openspec validate add-release-fidelity-handoff --strict`, `tools/scan_secrets.py`, and `git diff --check`.
- [x] 5.2 Dry-run a Quarterhoot-shaped fixture end to end with the mock Factory: two `assembly_parts` with the sealed colours, `renders.json` rendered, `conversation.jsonl` under 12 MB, receipt fields present.
- [ ] 5.3 Publish one new toy on the real Factory with the change enabled; confirm on the listing: two coloured meshes in the viewer, hero cover from the host render, manual pages using the renders, turns visible after publish.
