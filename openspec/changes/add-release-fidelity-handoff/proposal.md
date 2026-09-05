## Why

A shipped toy loses most of its fidelity at the Release → Factory boundary. Quarterhoot (`wish-20260903-235911-899eff45`, public since 2026-09-04) is the worked example. Make sealed two coloured parts (`owl_follower`, `reversible_nest`) in STEP and GLB and wrote a cadgen assembly-package descriptor, yet:

- the Factory received one grey `assembled.stl` (the CDN tree has no parts directory), so the shop renders a single mesh in its default colour and the sealed colours can address nothing;
- the manual's product images come from `render_product`, a flat per-face painter with no per-part input, so the booklet shows a teal owl with ochre tops, the inverse of the CAD;
- the listing has no build history, although the import API replays a `conversation.jsonl` into design turns.

None of the 32 Workshop-owned designs on the Factory carries a Workshop part colour or its session. Four gaps sit on one boundary:

1. `factory.py` builds a multipart transport only from a Factory-schema sidecar or from a `native-cad.assembly-descriptor` plus a `product.json` inventory. Make's required root file `assembled.step.json` is the cadgen assembly-package (`kind: assembly-package`, `schemaVersion: 2`), so the adapter deliberately falls back to a single mesh on every run. No producer of the descriptor it wants exists anywhere in the repository.
2. Part colours are implemented end to end (`read_step_part_colors` → `factory-part-colors` effect) but never fire because of 1. The STEP reader treats build123d colour channels as linear (cadgen's documented convention) while the GLB exporter treats them as sRGB, so the same part carries two different hex values.
3. Manual visuals must be hashed Made bytes and Make runs inside the Codex sandbox (network off, Workshop Python only), so no capable renderer can run there. Headless three.js and Blender exist on the host and render the same sealed GLB correctly (see `/root/shared-reports/quarterhoot-render-compare/`).
4. Workshop ships no `conversation.jsonl`; the run's Codex rollout is private host state.

## What Changes

- **Assembly-package handoff.** The Factory adapter accepts the sealed assembly-package at `assembled.step.json`, resolves each occurrence to `parts/<name>.stl`, and produces the existing multipart transport (`assembled_parts/<name>.stl` plus the synthesized Factory sidecar). Shell rules are unchanged. The Make gate requires one production STL per occurrence when a package has two or more occurrences. The receipt records which transport was used.
- **Part colours activate.** No new effect: once the Factory reports one mesh per occurrence, the existing `factory-part-colors` effect addresses them by `mesh_name`. One colour convention is enforced on the reading side: sealed STEP channels are reported as the sRGB hex the shop viewer shows (the vendored cadgen exporter is byte-locked and already agrees with the viewer), the sealed assembly-package supplies colours when the STEP is unstyled, and the Make reference tells authors to pick channels from the sRGB hex directly.
- **Host-owned product renders.** After the Make gate passes, the trusted host renders a hero, an optional turnaround set, and a fixed-camera state strip from the sealed part STLs, occurrence transforms, and STEP colours using a pinned headless three.js renderer. Outputs and inputs are bound in `renders.json`. Release manual visuals may cite them; the handoff ships the hero as the Factory cover. When the renderer is unavailable, Release proceeds on Make's snaps exactly as today.
- **Session history.** The host converts the run's Codex rollout into a redacted, Claude-Code-shaped `conversation.jsonl` at the handoff root, gated by an explicit run authorization, and records the replayed turn count on readback.
- **Readback.** After publish, the host verifies `assembly_parts` (count and colours) and records `history_turns`, `handoff_transport`, and `renders_sha256` in the release receipt and `workshop status`.

## Capabilities

### New Capabilities

- `workshop/factory-assembly-handoff`: multipart Factory transport derived from the sealed assembly-package, with active part colours and one colour convention.
- `workshop/manual-product-renders`: host-owned, hash-bound product renders available to Release manuals and the Factory cover, with a deterministic fallback.
- `workshop/factory-session-history`: authorized, redacted session history shipped with the Factory import and verified on readback.

### Modified Capabilities

None. Factory part colours were introduced by change fragment only; their behaviour is now specified inside `factory-assembly-handoff`.

## Impact

- `src/workshop/integrations/factory.py`: assembly-package reader, transport precedence, `conversation.jsonl` allowlist, cover file, readback fields.
- `src/workshop/make/native_gate.py`, new `src/workshop/make/assembly_package.py`: package parsing shared by gate and adapter; per-occurrence production STL rule.
- `src/workshop/make/cad/step_color.py`: sealed channels reported as sRGB; `references/make.md`: colour authoring rule (the cad skill tree is byte-locked).
- New `src/workshop/release/renders.py` and `tools/render/` (vendored three.js 0.160, playwright launcher): host render step, `renders.json` contract, doctor check.
- `src/workshop/release/manual_design.py`: `product_visuals` may resolve against `renders.json`.
- New `src/workshop/release/session_history.py`: rollout → `conversation.jsonl` converter with redaction and caps; `authorization.json` schema 3 with `history_disclosure_requested`.
- `src/workshop/workflow/native_run.py`, `src/cli/main.py`: Release stage inputs list renders, effect flow, `wish --disclose-session`, status and doctor output.
- `.agents/product-run/…`: Make requirement text, manual-design skill prefers host renders.
- `docs/PUBLISH_SEALED_PRODUCT.md`, `docs/NATIVE_AGENT_RUNTIME.md`: disclosure policy and render boundary.
- Tests mirrored under `tests/integrations`, `tests/make`, `tests/release`, `tests/workflow`, `tests/end_to_end`.
- New optional host tool dependency: Node 22 + playwright chromium (swiftshader). No new Python runtime dependency. Effect-ledger schema unchanged; receipt `details` gain fields.

## Non-goals

- Blender Cycles as the render backend now (evaluated 2026-09-05: CPU-only host, ~2 min 20 s per 1400 px frame inside the `panda-cc-agent:blender-test` image). The `renders.json` contract leaves a `renderer` slot for it.
- Rewriting `render_product`; it remains the sandbox-side proof renderer for the blind critic.
- Re-importing already published toys. Factory import is not idempotent, so Quarterhoot and the other 31 listings stay as they are until an operator decides to republish them as new designs.
- Backend changes. Every contract used here exists on `panda-social-backend` main (`docs/design-import-api.md`, `PATCH /designs/{slug}/part-colors`, `services/import_conversation.go`).
