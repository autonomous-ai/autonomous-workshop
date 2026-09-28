# Handoff: operator Answer / Contract Amendment for waiting Make runs

Written 2026-09-28 at the end of a long session. The owner writes in
Vietnamese; reply in Vietnamese, keep it short, and let them review toys by
images, never by contract rows.

## Goal of the next session

1. Build a host mechanism that lets the operator answer a Make run that
   stopped in `waiting` with one need, optionally carrying an amended Design
   Contract, and resume the **same** native session without restarting.
2. Then use it to answer the waiting Broken God run
   `wish-20260928-142712-25fb17ef` with the fixed contract. The previous
   session was told **not** to answer it; this session should.

## Why

Codex Make runs in Contract Mode stop with `status: waiting` when two
contract numbers cannot both hold. There is no channel for an answer today:
`workshop resume` only takes `--effort`, `--check-motion`, `--max-tokens`,
`--turn-budget`, `--turn-minutes`, `--refresh-tools`. The only fix was to
edit the contract and start a new wish, losing the work (15 min and 5 to 8M
tokens each time). The product-run protocol for a need is in
`.agents/product-run/.agents/skills/autonomous-workshop/SKILL.md` (the
`stage_proposal.py ... need --status waiting` section). A run's waiting
reason is the receipt's `needs[0]` (`workshop status <id> --json`).

## Settled decisions (the owner answered Q1 to Q10)

- **Q1 Channel:** `workshop resume <id> --answer-file FILE`. The host keeps the
  answer verbatim as a read-only, hash-recorded input file in the run root and
  puts it in the resume prompt. Only for a run in `waiting`; never injected
  into an active turn.
- **Q2 Authority:** an answer may carry a full replacement contract.
- **Q6 The Wish stays immutable.** The replacement is a separate sealed
  **Contract Amendment** that supersedes the Wish's contract for Make and for
  the final review. `wish_sha256` does not change; it stays traceable which
  contract the run started from.
- **Q7 What may change:** the reference images (same files and bytes), title,
  inventor and envelope must stay identical. Geometries, numbers and
  requirement rows may change. Changing an image needs `workshop fix`.
- **Q8 When:** only while the run waits in Make. After Make, use `workshop fix`.
- **Q9 How many:** unlimited, each recorded. The token budget stays the
  backstop.
- **Q10 Parts already built:** the host diffs the old and new contract block
  per geometry (extents, count, wall, geometry-scoped rows). The answer must
  also list geometries its prose changes affect. For the union, earlier
  component evidence (make_round rounds, likeness, print checks) is voided
  and must be redone. Unchanged parts keep theirs. Assembly evidence and the
  final review are always redone, because they are bound to the rows.
- **Q3 Who answers:** the build-a-toy agent answers every need itself,
  including ones that change something visible, then reports afterwards (see
  memory `agent-answers-run-needs.md`).
- **Q4 Fewer stops:** contracts now carry a "Hidden joints" section that lets
  Make settle hidden peg, socket, boss and collar geometry itself (done for
  Broken God; see below).
- **Q5 Docs:** write ADR 0076 and add glossary terms to `CONTEXT.md`:
  **Need** (the one condition a waiting run requires), **Answer** (the
  operator's reply, which may carry a Contract Amendment), and
  **Contract Amendment**.

## Where to look in the code

- CLI resume flags: `src/cli/main.py` (the `resume` subparser near line 2225)
  and `resume_native_run` in `src/workshop/workflow/native_run.py` (~10874).
- Precedent for a host-owned input rebind on resume: `MAKE-OPTIONS.json`, via
  `_adopt_resume_motion_policy` (native_run.py ~11026) and
  `refresh_domain_skill_tools(..., check_motion=...)` in
  `src/workshop/workflow/agent_run.py` (~1880). It writes a 0o400 file,
  records a `host-correction` in `host-corrections.jsonl`, and rebinds the
  session constitution. Model the answer input on this.
- Resume prompt assembly: native_run.py ~6680 to 6730 (where the motion
  policy and inspection-correction paragraphs are appended).
- Contract parsing: `workshop.wish.design_contract.parse_design_contract`;
  how the contract is sealed and bound to review rows is in ADR 0072
  (`docs/adr/0072-a-gate-that-verifies-nothing-refuses.md`). The finalizer
  that checks review rows against the contract is
  `.agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py`.
  It must read the amendment when one is active.
- Component evidence and round state: `src/workshop/make/skills/make-round/scripts/make_round`
  (ADR 0074/0075). Carry-forward identity: ADR 0073.
- Tests to model on: `tests/workflow/test_resume_inspection.py` (fake
  launcher, old-run fixture, host-correction ledger assertions).
- Read the ADRs listed in `AGENTS.md` before changing runtime or workflow.
- If `LOCK.json` fingerprints change (make skills), refresh them per
  `tools/verify_skill_locks.py`.
- Tests: pytest is not installed; use
  `PYTHONPATH=src uv run --with pytest python -m pytest -q <file>`. The full
  suite has pre-existing failures (34 at an earlier check; compare with a
  clean HEAD worktree before blaming a change).

## Broken God state

- Contract dir: `toys-spec/broken-god/` (untracked, never commit). Ledger:
  `toys-spec/broken-god/build-a-toy/ledger.json`, attempt 7 (round 0), with
  three aborted wishes recorded under `aborted_before`.
- Waiting run: `wish-20260928-142712-25fb17ef` (Codex, gpt-6-astra, effort
  medium, `--check-motion true`, `--no-publish`, `--turn-minutes 360`,
  `--max-tokens 100000000`). Need: the pelvis peg has no room because
  legs-pelvis spans exactly Z 20 to 133.3. Its proposal is in the run
  workspace, `design/proposed-contract-correction.md`.
- The fixed contract is `toys-spec/broken-god/CONTRACT.md` (identical to
  `build-a-toy/candidate-amend-c/CONTRACT.md` and, with the name line
  prepended, `build-a-toy/r00/CONTRACT.md`). What changed since the run's
  sealed copy (halo, base extents, envelope, foot pegs, neck collar, Hidden
  joints section) is listed at the end of
  `build-a-toy/drafts/amend-c-notes.md`. Note the run sealed the version
  before the joint audit, so its Wish contract differs from this file in
  envelope, base extents, foot pegs, neck collar and the new section.
  **Q7 keeps the envelope fixed**, but this fix changes the envelope (Y 134 to
  133.3, Z 246 to 245.5). Decide whether a measured correction of the
  envelope is allowed in an amendment, or start a new wish instead.
- Answer with `--check-motion true` on the resume (resume defaults it to
  false; see `.claude/skills/build-a-toy/SKILL.md`).

## Uncommitted work

- `.claude/skills/build-a-toy/DETECT.md`: a measured extent may exceed the
  contract by the hidden-joint allowance, on one axis, if `GEOMETRY-NOTES.md`
  names the joint. Commit it with the mechanism, or on its own if the owner
  asks. Commit or push only when the owner asks.
- This handoff file.

## Local machine state (never commit)

- `.venv/bin/python`, `python3`, `python3.13` are real files (hardlinks of the
  uv CPython 3.13.15 binary) and `.venv/pyvenv.cfg` `home` points at the
  versioned `cpython-3.13.15-linux-x86_64-gnu/bin`. This was needed because
  Codex's bwrap sandbox could not bind a symlinked venv interpreter. The
  original `pyvenv.cfg` was backed up in the old session's scratchpad, so it is
  gone. A `uv sync` that recreates the venv would bring the symlinks back and
  break Codex runs again.
- An http.server serving `toys-spec/broken-god/build-a-toy/review-amend-c/`
  on 127.0.0.1:8765 is still running (PID 1493782). Stop it when it is no
  longer needed.
- Review page artifact: https://claude.ai/artifact/FeLyUdirwnF82yM6vd5sLZ

## Suggested skills

- `mattpocock-skills:domain-modeling`, for the `CONTEXT.md` terms and ADR 0076.
- `build-a-toy`, to answer and carry the Broken God run after the mechanism
  lands, and to run DETECT when it completes.
- `design-a-toy`, only if an answer would need new or edited reference images
  (that is a `fix`, not an answer).
