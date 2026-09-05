## Context

See `proposal.md` for motivation. Facts established on 2026-09-05 against the Quarterhoot run and `panda-social-backend` main:

- Make's product root must contain `product.json`, `assembled.step`, `assembled.step.json`, `assembled.stl` (`native_gate.NATIVE_MADE_REQUIRED_ROOT_FILES`). The cadgen `artifact` tool writes `assembled.step.json` as an assembly-package: `kind: "assembly-package"`, `schemaVersion: 2`, `packageSchemaVersion: 3`, `occurrences[]` with `id`, `name`, `component`, 4×4 `transform`, `color`, and `stats.occurrenceCount`. Quarterhoot lists `reversible_nest` and `owl_follower`.
- The build-group contract (`native.validate_build_groups`) already places one printable STL per component at `parts/<key>.stl`, hashed in `groups/<group>.json`. Quarterhoot's `parts/owl_follower.stl` and `parts/reversible_nest.stl` are byte-identical to `cad/part_*.stl`, each is one shell, and `assembled.stl` is exactly two shells, so the adapter's existing `_inspect_shells` rules would pass.
- `factory._occurrence_transport` accepts, at the same path, only a Factory sidecar (`schemaVersion 1`, `entryKind assembly`, `primaryPose assembled`, `parts[]`) or a `native-cad.assembly-descriptor` bound to a `product.json` `cad`/`inventory` block. Anything else returns `None` and the handoff is single mesh. The Factory then reports one mesh named `assembled`, so `_part_color_plan` has nothing to address and no `factory-part-colors` intent is written. Quarterhoot's ledger holds only `factory-import` and `factory-publish`.
- The Factory worker names meshes after the STL stems it finds under `<primary>_parts/` (`internal/slicer/tree.go`, `models.AssemblyPart`), and the adapter's own tests assert `assembled_parts/<name>.stl`. `_OCCURRENCE_NAME` is `^[a-z0-9][a-z0-9_-]{0,127}$`.
- `read_step_part_colors` applied the sRGB transfer to build123d channels (cadgen's docstring calls `Color` linear), while the cadgen GLB exporter converts the same channels from sRGB to linear for glTF and the shop viewer shows them as sRGB. Quarterhoot's owl read as `#eabd76` from STEP and displays as `#d1822e` in the viewer.
- Manual visuals are validated by `manual_design.validate_manual_design_evidence` against `made.product_manifest.entries`; the Made tree is agent-authored and any host change to it fails `NativeMadeTreeGateError`.
- The import API finds `conversation.jsonl` at the archive root, republishes it with the folder, and replays it into `import_step` turns: one turn per user record with visible text, `isMeta` dropped, tool-result-only user records kept inside the current turn, dedupe by record `uuid`, caps 200 turns / 5 000 entries / 512 KB per entry / 12 MB. A malformed transcript costs the history, never the import.
- The run's Codex rollout lives at `~/.codex/sessions/<date>/rollout-<ts>-<thread_id>.jsonl` (`thread_id` from state `codex-session.json`). Quarterhoot's main thread is 1 827 lines / 15 MB: 63 messages, 273 tool calls with outputs, 289 encrypted reasoning items, and 282 token-count events. Subagent threads are separate files keyed by `parent_thread_id`.
- Existing policy: the public git example "contains no agent session, prompt, transcript, chain of thought" and the adapter deliberately omits Factory's `prompt` field. Run authorization (`authorization.json` schema 2) carries `publish_requested` and `github_publish_requested` only.

## Goals / Non-Goals

**Goals**

- Every multi-part toy reaches the Factory as one mesh per sealed occurrence, in the sealed colours, with no new effect kind.
- Product renders that look like the shop viewer, produced by the trusted host from sealed inputs only, usable by the manual and as the Factory cover, never blocking Release.
- Build history on the listing when, and only when, the run authorizes it.
- Everything verifiable on readback and visible in `workshop status`.

**Non-Goals**

- Any renderer inside the native session; any second agent framework; any change to the ledger schema or to how Made bytes are sealed.
- Blender backend, `render_product` redesign, backend changes, re-import of published toys.

## Decisions

### 1. The adapter reads the assembly-package; Make guarantees a production STL per occurrence

Add `workshop.make.assembly_package.read_assembly_package(bytes)` returning a typed, validated view (`occurrences`: ordered `(name, transform, color)`, `occurrence_count`). Validation: `kind == "assembly-package"`, `schemaVersion == 2`, `packageSchemaVersion >= 3`, `entryKind == "assembly"`, unique names matching `_OCCURRENCE_NAME`, `stats.occurrenceCount == len(occurrences)`, finite transforms.

`_occurrence_transport` gains a third branch after the two existing ones: when the sidecar is a valid assembly-package with two or more occurrences, each occurrence resolves to the sealed Made entry `parts/<name>.stl`; the transport is built exactly as today (`assembled_parts/<name>.stl`, synthesized Factory sidecar written to `assembled.step.json` in the zip, `assembled.step` copied, shell inspection of the assembly and each part). A single-occurrence package is transported as the root mesh (unchanged). A package that fails validation still degrades to single mesh, but the receipt now records `handoff_transport: "single-mesh"` with a bounded `handoff_transport_reason`.

The Make gate (`native_gate`) adds a deterministic rule: a package with ≥ 2 occurrences requires `parts/<name>.stl` for each, one shell each, and `assembled.stl` with exactly `occurrence_count` shells. Rejection text names the missing part so the native session repairs it. The product-run `autonomous-workshop` skill and finalizer input list this requirement next to `required_root_files`.

Alternatives rejected: (a) asking Make to also write the `native-cad.assembly-descriptor` and a `product.json` inventory duplicates data the package already holds and pushes an adapter contract into agent-authored files; (b) uploading `cad/part_*.stl` directly would bypass the build-group hashes and the `_parts` naming the Factory worker relies on.

### 2. One colour convention: the sealed channels are what the viewer shows

Measured on Quarterhoot: build123d writes the channels a designer passes to `Color(r, g, b)` into the STEP unchanged, the cadgen GLB exporter converts those same channels from sRGB to linear for glTF, and the shop's three.js viewer therefore displays them as sRGB (`#4d859e`, `#d1822e`). Only Workshop's STEP reader disagreed, applying a second transfer (`#95bfce`, `#eabd76`). The cadgen skill tree is byte-locked, so the exporter stays untouched and the reader moves: `read_step_part_colors` reports `#rrggbb` from the raw channels, the assembly-package reader reports the same, and the host renderer paints with them. Authoring guidance lives in the repository-authored Make reference: pick channels directly from the sRGB hex, never pre-convert with cadgen's `srgb()` helper, which double-darkens in this pipeline. `_part_color_plan` needs no change: with Decision 1 the Factory's `mesh_name` equals the STEP occurrence name.

### 3. Host-owned renders beside the Made tree, bound by `renders.json`

After the Make CAD gate passes for round `rNNNN`, the host writes `artifacts/make/rNNNN/renders/`:

- `hero.png` 2000×2000, `turnaround_<view>.png` 1200×1200 for `front|back|side_l|side_r|top` (optional, on by default), `signature.png` fixed-camera strip when states are declared;
- `renders.json`: `kind`, `schema_version`, `made_product_sha256`, `renderer` (`three-swiftshader`, three.js and chromium version, hash of the vendored bundle), `inputs[]` (Made paths + sha256), `outputs[]` (path, sha256, bytes, width, height), `status` (`rendered` | `unavailable` with a bounded reason).

Inputs are sealed Made bytes only: `parts/<name>.stl` placed by the package transforms with STEP colours (single-mesh products use `assembled.stl` with the single sealed colour or a neutral default), and state STLs declared by Make in `product.json` as `presentation.states: ["<path>", …]` (2–5 entries; Quarterhoot's were under `cad/snap/states/`). The strip reuses the existing state-difference rule: indistinguishable frames make `signature.png` `unavailable` rather than misleading.

Renderer: `tools/render/` holds a vendored three.js 0.160 bundle and a launcher script that starts a loopback HTTP server, loads the scene in playwright chromium with swiftshader (`--use-gl=angle --use-angle=swiftshader`), renders with `MeshPhysicalMaterial`, `RoomEnvironment` PMREM, key/fill/rim lights, `PCFSoftShadowMap` on a `ShadowMaterial` ground, ACES tone mapping, and a 62 % bounding-box framing. It runs under `minimal_tool_environment` with a 5-minute bound and no network. Outputs are re-validated with Pillow (dimensions, PNG, size cap) before binding. `workshop doctor` reports node, playwright, and a smoke render.

Release: the stage input lists `renders/` paths; `validate_manual_design_evidence` accepts `product_visuals[].source_path` under `renders/` when `renders.json` is bound to the current Made product sha and the file hash matches; the manual-design skill prefers host renders for the cover and the signature spread and falls back to Make snaps. The handoff zip adds `assembled_review/_assembled.png` (the hero) so the Factory's own cover ranking picks it.

Fallback: renderer missing or failing writes `status: unavailable`; Release, the manual, and the handoff behave exactly as today and `workshop status` shows a warning. A missing renderer never blocks publication.

Alternatives rejected: rendering in the native session (sandbox has no node/chromium and would need network), adding files into the Made tree (breaks the sealed-tree gate), Blender now (cost and docker dependency; contract leaves the slot open).

### 4. Session history is a trusted-host projection of the rollout, shipped only when authorized

`workshop.release.session_history.build_conversation(run_state, disclosure) -> bytes` reads the main-thread rollout for `codex-session.json.thread_id` and emits Claude-Code-shaped JSONL:

- first record: a synthetic user record whose text is the exact Wish when `disclose_exact_wish` is granted, otherwise the sealed public product summary; `uuid` = its sha256. The Factory derives the listing's originating prompt from it, so the adapter keeps omitting the `prompt` form field.
- `response_item.message` with `role: user` and visible `input_text` → `{"type":"user","uuid":<id>,"timestamp":…,"message":{"role":"user","content":"<text>"}}` (host stage Goals; trimmed to 8 KB);
- `role: assistant` → `{"type":"assistant", …, "content":[{"type":"text","text":…}]}`;
- `custom_tool_call` / `function_call` → assistant record with a `tool_use` block (`id` = `call_id`, `name`, parsed `input` or `{"raw": …}`); `*_call_output` → user record with a `tool_result` block, output trimmed to 16 KB;
- `reasoning` (encrypted), `developer` messages, `event_msg`, `turn_context`, `world_state`, `compacted`, plugin banners, and `spawn_agent` payloads are omitted or marked `isMeta: true`; subagent threads are not included in v1 and their count is recorded.

Redaction: workspace-relative paths kept, other absolute host paths replaced by `<host>`, `tools/scan_secrets.py` patterns applied, credential-shaped strings dropped. Caps mirror the server: ≤ 200 turns, ≤ 5 000 entries, ≤ 512 KB per entry, ≤ 12 MB total (oldest tool results trimmed first). Records are ordered by rollout ordinal and `uuid`s are the rollout item ids, so a repeat import de-duplicates.

Placement: `conversation.jsonl` at the handoff archive root, allow-listed in `_assert_archive_inventory`. It is not a Made or Release manifest entry; it changes the zip bytes and therefore `pack_sha256`, so the ledger binds it without a schema change.

Gate: `authorization.json` schema 3 adds `history_disclosure_requested: bool`, set by `workshop wish --disclose-session` or by an Inventor-account default in Workshop config. Without it no file ships. The Factory publishes the file on the public CDN folder and shows turns to strangers once the design is public, so the docs state this plainly.

### 5. Readback and status

`_complete_release_draft` records `handoff_transport`, `occurrence_count`, `renders_sha256` (when rendered), and after publish `history_turns` from `GET /designs/{slug}/turns` (owner token, best effort: a server-side drop is a warning, not a failure). `assembly_parts` readback already asserts colours. `workshop status` prints transport, colours, renders, and turns.

## Risks / Trade-offs

- Host tool dependency (node, playwright, chromium). Mitigated by doctor, pinned versions, and the unavailable-fallback.
- Zip growth (≤ 12 MB history, part STLs, one PNG) against the Factory's 100 s Cloudflare window. Measure on Quarterhoot-sized runs; keep total under 50 MB.
- Public transcript disclosure. Mitigated by the explicit authorization, redaction, and updated policy docs; the owner decides the default.
- Mesh naming relies on the Factory worker's `<primary>_parts/` convention, already asserted by adapter tests and observed on `five-job-checkers`.
- Colour convention change alters GLB colours for future runs only; frozen runs are unaffected.

## Migration Plan

- Frozen runs keep their materialized protocol. New runs materialize the updated skill text and finalizer inputs.
- `authorization.json` schema 2 reads as schema 3 with `history_disclosure_requested: false`.
- Already published toys are not re-imported. Quarterhoot can be republished as a new design once the change lands, then the old listing unpublished; this is an operator decision.

## Open Questions

- Default for `history_disclosure_requested` on Workshop-owned Inventor accounts: on (owner's stated wish) or off (current policy).
- Turnaround set on by default, or hero + strip only, given ~5 s per frame on swiftshader.
- Whether `presentation.states` should become required for products whose Wish promises a signature motion.
