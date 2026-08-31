# ADR 0035: Remove proof startup and scheduling leaks

- Status: Accepted
- Date: 2026-08-31
- Owners: Runtime, workflow, product-run protocol, and CAD-skill maintainers
- Supersedes for new runs: ADR 0034's `deep-economics-v6` profile

## Context

The identical Three-Sky Seed production Quest tested deep-v6 through the
regular CLI in an untouched persistent Codex session. The run stopped safely
after Invent and two bounded Make turns. It was not published or pushed as a
finished toy.

V6 corrected the executable contract. Make recovery authored one valid
module-scope `gen_step()`, generated STEP and STL, and rendered a 900×900 held
image plus a 2700×900 three-pose signature sheet. The result was a fully
volumetric faceted seed/pod with a captive halo. It still did not make the
three distinct skies and interaction unmistakable, and no blind-review record
or proof marker was written before timeout.

Exact tool output and artifact timestamps exposed three remaining startup and
scheduling leaks:

1. The first correct generation command failed while `ezdxf` tried to write
   `$HOME/.cache/ezdxf/font_manager_cache.json`. The product sandbox correctly
   denies the user's home tree. Recovery spent a reasoning cycle creating a
   run-local cache and exporting `XDG_CACHE_HOME` itself.
2. The proof turn loaded the root instructions, Workshop skill, Make reference,
   and the broad CAD skill, then reread all three skills after truncation. The
   Workshop skill, Make reference, and broad CAD skill together were about
   59.5 KB even though the host already supplied the complete three-command
   proof interface.
3. Generation, export, and rendering were issued in separate native-agent
   cycles. The proof source existed at 06:55:03, STEP at 06:57:01, STL at
   06:58:55, and renders at 06:59:53/57. The blind critic was not spawned until
   07:01:47, only 46 seconds before the 07:02:33 boundary.

Local native-session diagnostics reported these root-Manager counts:

| Stage / turn | Input | Cached input | Uncached input | Output | Reasoning output |
|---|---:|---:|---:|---:|---:|
| Invent initial | 323,888 | 266,752 | 57,136 | 3,604 | 369 |
| Invent recovery | 184,484 | 149,504 | 34,980 | 5,537 | 200 |
| Make proof | 189,382 | 157,696 | 31,686 | 2,800 | 1,323 |
| Make proof recovery | 197,906 | 161,792 | 36,114 | 2,343 | 91 |
| **Root total** | **895,660** | **735,744** | **159,916** | **14,284** | — |

Three bounded native children reported 140,197 input, 88,576 cached input,
51,621 uncached input, and 2,910 output tokens. Root and children together
reported 1,035,857 input and 17,194 output tokens over about 40m15s. That is a
failed-run diagnostic, not completed-product cost. It reduced root input 28%
and output 26% versus v5, but quality and terminal completion still failed.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v7.md`.

- The host creates a private 0700 `<run-root>/.cache` and binds
  `XDG_CACHE_HOME` before every native launch and resume. Cache paths remain
  outside the sealed product tree.
- V7 retains v6's reasoning levels, 20/10-minute Invent boundaries,
  8/30-minute Make phases, 24k compaction, marker semantics, medium later
  stages, and eight-turn command cap.
- During the early proof only, the broad CAD skill is deliberately not
  applicable. The root instructions, Workshop skill, current Make reference,
  and host prompt contain the complete narrow contract. The broad CAD skill is
  loaded after the marker for final Make.
- The root spawns one blind critic without the Wish or concept before the CAD
  batch and gives it only the future held/signature paths to await.
- Generate, export, and render execute in order in one foreground tool call.
  The host still supplies exact `$WORKSHOP_PYTHON` commands and the source still
  defines exactly one module-scope `gen_step()`.
- The root compares the blind read with the sealed Wish. A second child turn
  that merely reveals stable text is unnecessary.
- A generic or ambiguous proof receives at most one focused repair and one
  repeat batch. Only exact proof bytes, a blind finding, and the
  checkpoint-bound marker end the proof turn.
- No lifecycle, CAD, visual-review, Playtest, manual, Factory-publication, or
  GitHub-snapshot gate is weakened.

## Consequences

- Deterministic CAD startup no longer depends on a writable user-home cache.
- The bounded proof phase spends its context on shape and interaction rather
  than the full final-CAD manual.
- The blind critic can inspect immediately when renders arrive instead of
  waiting behind three root reasoning cycles.
- V7 adds no Python planner, retry loop, model judge, lifecycle state, or
  external effect path. Codex still owns the creative work and critique.
- The economics target remains unproven until fresh Quest and Forge products
  complete every gate, publish, and preserve desirable snapshots. Spark must
  also retain its separately frozen low-cost profile and prove quality on a
  fresh terminal run.

## Compatibility and migration

Deep-v6 and every older profile remain recognized by exact frozen capability
hash. Existing run roots retain their materialized instructions and runtime
policy. Resume accepts only the exact immediately preceding runtime policy
without the private cache, plus the already-supported historical policy
predecessors; arbitrary policy drift continues to fail closed.

## Verification

- Runtime tests require the private cache environment and 0700 directory,
  reject a cache symlink, and prove exact predecessor resume.
- Prompt and capability tests independently prove v7 batching/deferral and v6
  frozen compatibility.
- A real acceptance test runs generate, export, and render from a workspace
  path containing spaces with the private cache bound, then verifies STEP,
  STL, held PNG, and signature PNG outputs.
- Full deterministic repository tests pass before production runs.
- Untouched fresh Spark, Forge, and Quest sessions must complete, publish with
  authenticated readback, preserve their GitHub toys, and show a distinctive
  desirable signature experience before the cross-effort goal is achieved.
