# ADR 0090: Builds write Wiki Rules back to the upstream wiki, and the owner resyncs it

- Status: Accepted; the run's proposal file, the build loop's write-back and
  the resync skill are implemented; not yet exercised by a live build
- Date: 2026-10-14
- Relates to: ADR 0055 (Make Lessons on the design vault, unchanged)

## Context

The Make wiki under `src/workshop/make/skills/wiki/` is vendored from
`autonomous-product-to-cad`, and is consult-only inside a run. Upstream learns
every day: its agents end each task by writing what it taught into the wiki,
and they merge that into `main` without review. Workshop learned nothing the
same way.

- A run was told to report a missing rule in its final response, where it was
  lost when the run ended.
- No one resynced the vendored tree on a schedule. By 2026-10-14 it was 47
  upstream wiki commits behind.

ADR 0055's Make Lessons are a different thing. They are evidence rows the
host banks on the design vault and hands the next packet. They are not rules.

## Decision

1. **A run proposes.** A product run appends each rule the wiki lacked to
   `LESSON-PROPOSALS.md` at its run root, with the rule, its evidence, the
   failure class and the page it extends. That file sits outside every
   immutable tree and sealed manifest, so it is never hashed, gated or
   published, and no host code reads it.
2. **The build loop writes.** When a `build-a-toy` loop stops, it gathers
   every attempt's Lesson Proposals and what its own diagnoses found.
   - It keeps only Wiki Rules. A rule whose deletion would make a skill run
     its steps or gates wrongly is a workflow change, and goes through the
     harness-defect path instead.
   - It writes the rules into a fresh clone of upstream and pushes them to
     upstream `origin/main` with no review, the same way upstream treats its
     own lessons.
   - It never uses the owner's local checkout of upstream. Sessions run
     there, and its post-commit hook merges every commit into its `main`.
3. **The owner resyncs.** The `resync-vendored-skills` skill brings upstream
   into Workshop: a three-way merge, `LOCK.json`, `PROVENANCE.md` and the
   full suite, then a fast-forward of `main`, or a PR when something fails.
   The owner runs it about every 12 hours. It is a skill rather than a cron
   job, because an unattended agent session merging into `main` was not
   wanted.

## Consequences

- One wiki serves both repositories. A Workshop rule reaches runs one resync
  after its build stops, and frozen runs keep the bytes they materialized.
- Workshop pushes to upstream `main`. Any local checkout of upstream with
  unpushed commits must pull before its next push.
- Lesson Proposals are model prose. They become rules only through the build
  loop's judgment, and never move a gate.
