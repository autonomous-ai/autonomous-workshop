---
name: build-a-toy
description: Build a toy from a Design Contract until it conforms - run `workshop wish` as round 0, detect every nonconformance against the contract, and run `workshop fix` rounds until none remain, publishing only the conforming build. Can run unattended - one session launches, watches and diagnoses every attempt, fixes Contract Contradictions at the root and relaunches, resuming from the ledger alone. Use after `design-a-toy` produces a contract, when an existing toy drifted from its contract, or to run or resume a toy's unattended loop.
---

# Build a toy to its Design Contract

`design-a-toy` settles *what* the toy is. This skill owns everything after
that: it builds the toy, checks the build against the contract, and corrects
it until the two agree. The output is one published toy that conforms to its
contract, or a plain report of why no build conformed.

Use the vocabulary in `CONTEXT.md`: **Design Contract**, **Conformance**,
**Requirement Scope**, **Unique Geometry**, **Component** (not "part").

## The settled run parameters

Every run this skill starts, whether `wish` or `fix`, uses:

| Flag | Value | Why |
|---|---|---|
| `--contract` | always | Seals the Design Contract into the run (ADR 0072). The host refuses to complete the run unless its review carries every one of the contract's requirements, in order, each visibly matching — **conformance for requirements is established by the run itself, not by this skill re-deriving coverage from a Manager-written list** |
| `--no-publish` | always, round 0 included | Nothing reaches Factory until it conforms |
| `--turn-minutes` | `360` | The maximum. The clock is not the limit |
| `--max-tokens` | `100000000` | **This is the real backstop.** With 360-minute turns and unlimited resume, a run stops when its tokens run out |
| `--ref` | every contract reference, every run | The assembly round scores every sealed reference that no current component round already scored (ADR 0072). A description of an image is no substitute for the image |
| `--check-motion` | `true` when the contract has any moving part, on **every** `wish`, `fix` and `resume` | `workshop resume` reselects this option and defaults it to `false`. Broken God v01 was resumed without it, and its final verification skipped the motion check and shipped with its wings unverified |
| `--effort`, `--model` | only if the person passed them | Both are frozen for the run and cannot change on resume, so never raise them yourself |

## Step 1 - Load and validate the contract

Inputs: the path to `CONTRACT.md`, and optionally an existing toy (a
`toys/<slug>` directory or a wish id). Validate the contract against
[CONTRACT-FORMAT.md](CONTRACT-FORMAT.md). If the person has only a
`design-a-toy` spec and no block, draft the block from the spec, show it next
to the prose, and wait for explicit approval. The person approves the list of
requirements; you only transcribe it.

Create the ledger `<contract-dir>/build-a-toy/ledger.json` or resume from it.
It records each round's number, kind (`wish` or `fix`), wish id, run
workspace, toy directory, final status, brief path and finding ids, and, in
the unattended mode, the loop's own fields ([LEDGER.md](LEDGER.md)). Resuming
this skill in a later session starts from the ledger, not from memory.

Done when: the contract validates with no errors, and the ledger exists.

## Step 2 - Round 0: the wish

Skip this step when an existing toy was given. That toy is round 0: run
Step 4 on it.

`--contract` seals its file byte for byte as the objective, so the round's
name cannot be a line appended after the fact: copy `CONTRACT.md` to
`build-a-toy/r00/CONTRACT.md` with one line prepended, `Name this toy
exactly: <title> v01.`, ahead of the prose. This does not touch the fenced
`design-contract` block, only the prose above it. Every build in the chain
takes a suffixed name. A local, unpublished projection can never overwrite a
different `toys/<slug>`, so reusing a name strands the run at its last step.
Build the command:

```bash
uv run workshop wish --contract build-a-toy/r00/CONTRACT.md --inventor <inventor> \
  --ref <contract-dir>/ref-01-<slug>.png --ref ... \
  --no-publish --turn-minutes 360 --max-tokens 100000000 [--check-motion true]
```

**Show the person the exact command and wait for explicit approval.** Then run
it. When the receipt prints, check that its `References:` line reports as
many images as the contract lists. If the counts differ, stop: the likeness
gate will score the wrong set.

Done when: the run is started, the receipt's reference count matches, and
the wish id is in the ledger.

## Step 3 - Carry the run to completion

Poll `uv run workshop status <wish-id> --json`. Its `status` is `active`,
`waiting`, `failed` or `complete`.

- `complete`: go to Step 4.
- `waiting` with a receipt `needs` entry naming a **Reference Camera
  mismatch** (schema 3 contracts, ADR 0083): the Component Reviewer saw the
  model from a different side than the reference shows. Answer it yourself;
  do not ask the person. Open the named reference image, check the landmarks
  the need names against it, and estimate the camera again by eye in the
  Display Pose frame, rounded to 15 degrees. Then resume with
  `uv run workshop resume <wish-id> --reference-camera <file>=AZ,EL --turn-minutes 360 --json`,
  adding `--check-motion true` whenever the run was started with it. This changes only that
  reference's camera: never edit the image, a requirement or the contract
  file to answer it. Record the old and new camera and the cue in the ledger.
- Anything else means the run is **incomplete**, which is not a design
  result. Read the receipt's `stop_category` (present whenever `status` is
  not `complete`) to decide what to do next, rather than guessing from
  `status`, `stage` or token counts:
  - `transport` or `inspection-in-progress`: the stop is resumable and, for
    `inspection-in-progress`, still converging. Resume it:
    `uv run workshop resume <wish-id> --turn-minutes 360 --json`, adding
    `--check-motion true` whenever the run was started with it, because a
    resume without it turns the motion check off. Leave
    `--max-tokens` out, because a resume keeps the saved budget. Resumes are
    unlimited and never count as a round.
  - `usage-limit` (status `waiting`): the Claude Code or Codex account hit
    its provider usage limit, so the session could not start or continue.
    It is resumable, but not until the limit resets: a resume before then
    fails the same way. Wait, then resume with the same command as
    `transport`; if it stops at `usage-limit` again, wait an hour and retry.
    It is not a budget stop, so leave `--max-tokens` out.
  - `budget`: report plainly that **the token budget, the run's only
    backstop, is exhausted**. Hand the decision to the person. A resume
    without a new `--max-tokens` cannot proceed past it. In the unattended
    mode the loop diagnoses it instead (see below). The loop raises the cap
    on its own at most once per attempt (`budget-progressing`, recorded
    `budget_raised: true`); any other raise is the owner's. Record an
    owner-approved raise on the stop it answers as `budget_raised: "owner"`
    with `owner_decision: {"at": <stop time>, "limit_before": <tokens>,
    "limit_after": <tokens>}`, and resume with `--max-tokens <limit_after>`.
  - `gate-refusal` or `unclassified`: stop and show the person the receipt.
    A host gate refusal will not be resolved by resuming unchanged, and an
    unclassified stop is not safe to guess about. Ask the person how to
    proceed.

Done when: the status is `complete`, and the ledger records the run
workspace and toy directory. The workspace is
`$(uv run python -c "from workshop.runtime.package_data import default_workshop_home as h; print(h())")/runs/<wish-id>/workspace`.
The toy directory is the `toys/<inventor>-<slug>/` whose `wish/wish.json`
carries this wish id.

## Step 4 - Detect nonconformance

Follow [DETECT.md](DETECT.md) for this round. It writes
`build-a-toy/r<NN>/findings.json`, with every contract check listed once, as
either a finding or a pass.

Done when: `findings.json` is complete and in the ledger.

## Step 5 - Decide

Compare this round's finding ids with the previous round's:

1. **No findings** means the toy conforms. Go to Step 7.
2. **Five fix rounds already spent** means stop. Round 0 does not count.
   Publish nothing, and report the remaining findings for each round. The
   person decides whether to publish the closest build.
3. **This fix round removed no finding id** that the previous round had, so it
   did not converge. Stop and report the same way.
4. Otherwise go to Step 6.

## Step 6 - A correction round

Write `build-a-toy/r<NN>/brief.md`:

- Its first line is `Name this revision exactly: <title> v<NN+1>.` Round 0
  is `v01`, so fix round 1 is `v02`. Every build in the chain has a different
  name.
- Each finding follows, as the contract value, the measured value, and the
  evidence. Give a concrete repair only where the fix is unambiguous.
  Otherwise state the target and leave the method to Make.
- Then this line: *every other requirement of the Design Contract still
  holds; a correction may not trade one requirement for another.*
- Then a size budget, so the next round can still chain: `assembled.step`
  under 12 MB, and the heaviest Component under 4 MB.

`fix --contract` seals `CONTRACT.md` into the correction separately from the
brief (it does not replace `--prompt-file`), so the brief itself only needs
the findings, not a second copy of the whole contract. The brief becomes part
of the correction run's Wish objective, which is limited to 50,000
characters; if it is over the limit, shorten the findings and show the
person, rather than cutting anything the run is judged against.

**Show the person the brief and the exact command, and wait for explicit
approval.** Then run the correction from the previous round's **run
workspace**, not from `toys/`. The workspace is smaller than the published
archive, and it stays within `fix`'s 128 MiB source limit.

```bash
uv run workshop fix "<previous-run-workspace>" --prompt-file build-a-toy/r<NN>/brief.md \
  --contract <contract-dir>/CONTRACT.md \
  --ref <contract-dir>/ref-01-<slug>.png --ref ... \
  --no-publish --turn-minutes 360 --max-tokens 100000000 [--check-motion true]
```

Check the receipt's `References:` line against the contract's reference
count, exactly as in Step 2, and stop if they differ. Record the new wish id in
the ledger, then return to Step 3.

## Step 7 - Publish the conforming build

Only a build with zero findings is published. It carries a suffixed title
such as `<title> v03`. Publish it under the clean `<title>` with
`uv run workshop publish <wish-id> --title "<title>"`. This re-seals only the
host's own Release; Make's sealed bytes are untouched, no correction run is
spent, and no detection needs to run again. Omit `--title` to publish under
the exact suffixed name Make sealed instead.

Its summary line can report `effect.factory failed` after the listing
actually went live. Before concluding anything, read the effect ledger in
`<workshop-home>/state/<wish-id>/factory-effects.sqlite3` and fetch the live
page. Rows marked `factory-publish|unknown` mean the publication went out, so
do not publish again.

## Unattended mode

The person can hand a toy's whole loop to one supervising session ("run
Broken God unattended"). That session launches each attempt, watches it,
diagnoses every stop, fixes what it found, and launches the next attempt. It
writes no handoff file: `build-a-toy/ledger.json` is its only memory, and
its fields are in [LEDGER.md](LEDGER.md). A new session resumes the loop by
reading the ledger alone:

```bash
python3 .claude/skills/build-a-toy/scripts/ledger.py next <contract-dir>/build-a-toy/ledger.json
```

It does what that prints: `launch`, `watch`, `diagnose`, `fix`,
`resume-budget`, `resume-amendment`, `ask-owner`, or `migrate` for a ledger
that predates this mode. A `diagnose` that carries `then_ask_owner` is still done first, so the
owner is asked once, with the diagnosis in hand. Write every decision into the ledger **before** acting on it, then run
`ledger.py check` on it. The tools are under `scripts/`, run from the
Workshop checkout with `uv run python`; none assumes a platform or a home
directory.

Starting the loop is the person's approval of every Step 2 command and Step 6
brief it builds with the settled run parameters. What still waits for the
person is listed under "When the loop stops and asks".

### One loop pass

1. **Launch.** Make a fresh detached worktree at `origin/main` (`git fetch
   origin && git worktree add --detach <dir> origin/main`) and run Step 2's
   command from it. The round's name takes the next suffix (`<title> v<NN>`).
   Record the attempt in `rounds`, set `loop.attempt`, `loop.wish_id`,
   `loop.source_commit` and `loop.state: watching`.
2. **Watch.** Run `scripts/watch.sh <wish-id>`; it prints a line whenever the
   run's state changes and exits when the run stops. Answer a Reference
   Camera need, resume a `transport` or `inspection-in-progress` stop and
   wait out a `usage-limit` stop exactly as Step 3 says, and keep watching.
   A `complete` run goes to Step 4 as usual.
3. **Diagnose** every other stop (`loop.state: diagnosing`). Gather the
   evidence, never guess it:
   - the receipt: `uv run workshop status <wish-id> --json` (`stop_category`,
     `needs`, `blocked_reports`, `reference_conflicts`,
     `contract_amendments`);
   - progress: `scripts/tally.py <wish-id> --json` (`locked`,
     `repeated_print_defects`) against the previous attempt's;
   - cost: `scripts/tokens.py <wish-id> --json` (`cost_units`), added to
     `cost_units.by_attempt`;
   - the Component Workers' and the root's transcripts and the component
     rounds, for what a worker reported blocked and what a repeated print
     defect is made of.

   Write the evidence to `build-a-toy/r00/attempt<N>-<id>/evidence.json`,
   classify it with `ledger.py classify` on that file, and record one `stops`
   entry with the class, the evidence and the progress.
4. **Fold in-run amendments** into the contract, whatever the class (below).
5. **Fix** by class (the table below), then run `ledger.py next`. It
   prints `resume-amendment` when the stopped run can take the fix as an
   owner amendment (below); otherwise set `loop.state: launch` once nothing
   is pending.
6. **Check the stop conditions** with `ledger.py next`. It prints
   `ask-owner` with every reason that holds; otherwise the next pass
   starts at 1.

### Diagnosis classes

Each stop is classified from evidence into exactly one class. The order is the
precedence: a budget stop whose evidence also shows a contradiction is a
Contract Contradiction (Broken God attempt 15 stopped on `budget` with a
worker blocked on two rows).

| Class | Evidence | What the loop does |
|---|---|---|
| Camera need | a Reference Camera mismatch `need` | Step 3's path, unchanged |
| `contract-contradiction` | a `need` quoting contradicting statements, a Blocked Report open or waiting (except at a progressing attempt's first budget stop with no other such evidence: the raise gives the root its turn to answer), a Component Worker's report quoting rows that cannot both hold, or a repeated print defect that a contract row forces | Fix it at the root (below); resume the stopped run with an invisible fix as an owner amendment, else relaunch |
| `reference-mismatch` | an image contradicts the contract or the camera beyond what a Reference Conflict absorbs | Fix the image with `design-a-toy` Stage 3b; it is a visible change |
| `harness-defect` | Workshop itself went wrong: a false stop, a miscount, a guard or tool refusing valid work | Open an issue, fix and merge it (below) |
| `budget-progressing` | `stop_category` `budget`, and more Components locked or fewer repeated print defects than the previous attempt, with no raise yet in this attempt | Resume once with the cap raised by 100M tokens: `uv run workshop resume <wish-id> --max-tokens <limit + 100000000> --turn-minutes 360 --json`, with `--check-motion true` when the run has it; record `budget_raised: true` |
| `other` | anything else, including a second budget stop in one attempt | Ask the owner; when the owner raises the token cap, record `budget_raised: "owner"` and `owner_decision` `{at, limit_before, limit_after}` (never `true`: that is the loop's one raise), then resume with `--max-tokens <limit_after>`. A later budget stop in the attempt is still `other` |

### Fixing a Contract Contradiction at the root

Never answer it inside the run, and never pick one statement over the other
in a brief. (A contradiction the run's own Contract Amendment removed is not
one of these: fold it as above.) Fix the contract:

1. **Amend the contract** with the smallest change that removes the
   contradiction, in `design-a-toy`'s resolution order (Stage 3c and 3d).
   Back up the current contract and references, write
   `build-a-toy/drafts/amend-<x>-notes.md`, add `amend-<x>` to
   `contract_versions`, and record a `contract_contradictions` entry: both
   rows verbatim, a `signature` of `<check>:<component>` (the
   `design-a-toy` check that covers this class, and the Component), and the
   amendment.
2. **Re-audit the whole contract** with `design-a-toy` Stages 3b (for every
   image the amendment touches), 3c and 3d: every Component and every check,
   not only the changed row. Record the notes' path in `reaudit`. A new
   contradiction the re-audit finds goes into the same amendment.
3. **Give `design-a-toy` a check that would have caught it**, when it has
   none: open a harness issue and fix it like any harness defect, and record
   it in the entry's `design_check`. The swept-volume-over-ceiling check in
   Stage 3c is the first such check (attempt 15).
4. **Apply it, or batch it for the owner**, by the approval rule below.
5. **Resume the stopped run with it when it is invisible.** Once every
   Contract Contradiction of the attempt is applied, invisible (`visible:
   false`) and nothing else is pending, `ledger.py next` prints
   `resume-amendment`. Resume the run that stopped instead of relaunching,
   so its locked Components keep their locks:

   ```bash
   uv run workshop resume <wish-id> --amend-contract <contract-dir>/CONTRACT.md \
     --turn-minutes 360 --json [--check-motion true]
   ```

   The host records it as an Owner Contract Amendment (issue #100): it
   refuses anything beyond requirement text, Interface text and prose, keeps
   the run's sealed name line (so the root file's own `Name this toy
   exactly` line, or none, is fine) and unlocks only the Components whose
   own rows changed. Fold the run's applied in-run amendments into
   `CONTRACT.md` first, as `ledger.py next` requires, or the file would undo
   them. On success set each entry's `resume: resumed` and
   `loop.state: watching`, and keep watching the same attempt. A run
   materialized before #100 refuses it ("materialized before owner contract
   amendments") and nothing is recorded: set `resume: refused` and launch
   the next attempt. A visible change redraws an image, which only a new
   attempt seals, so it is always relaunched.

### Folding in-run Contract Amendments back

A run may amend its own contract when a Contract Contradiction's fix is
invisible: the Workshop Manager proposes it and a fresh Contract Reviewer
confirms it (ADR 0085). The run builds to the amended rows, but the toy's
`CONTRACT.md` does not change, so the next attempt would meet the same
contradiction. After every attempt, complete or not, fold each applied
amendment back:

```bash
uv run workshop status <wish-id> --json > build-a-toy/r00/attempt<N>-<id>/status.json
python3 .claude/skills/build-a-toy/scripts/ledger.py fold <contract-dir>/CONTRACT.md \
  build-a-toy/r00/attempt<N>-<id>/status.json --attempt <N> --out build-a-toy/drafts/amend-<x>.md
```

It replaces each amended row's text inside the `design-contract` block and
leaves every other byte of the contract as it is; a change already in the
contract is skipped. Back up `CONTRACT.md`, review the draft, then copy it
over `CONTRACT.md` and add `amend-<x>` to `contract_versions`. Append each
printed entry to `in_run_amendments` with `contract_version: amend-<x>`. It
needs no owner approval (the run's Contract Reviewer found it invisible) and
no separate re-audit beyond Stage 3c and 3d on the rows it changed. A change
`fold` refuses (the row no longer reads as the run quoted it, because an
outer-loop amendment changed it since) is folded by hand, leaving `folded:
false` until it is; `ledger.py next` lists it as pending. A refused
in-run amendment is a `need` like any other and is diagnosed by class.

### Approval: only visible changes wait for the owner

A change is **visible** when a reference image would have to be redrawn
because of it. A visible change waits for the owner: all of a loop pass's
visible changes go on **one** review page,
`toys-spec/<toy>/review-amend-<x>/index.html` in the main checkout, laid out
as `design-a-toy` Stage 4 lays out its review (old and new image side by side,
one plain line each). The loop then stops with `loop.state: awaiting-owner`.
On approval, set the entry's `approved` to `owner <date>`, apply it, and set
`applied: true`.

An **invisible** change (a clearance, a print stance, hidden geometry, a value
the images do not show) is applied without asking: set `approved` to
`not-needed`, apply it, and set `applied: true`.

### Harness defects: fixed and merged automatically

1. Open the issue with `gh issue create` and record it in `harness_issues`
   with `opened_by_loop: true`. The loop implements and merges **only** issues
   it opened itself.
2. Implement it in a subagent, in a fresh worktree from `origin/main`
   (`status: implementing`), following the repository's `AGENTS.md`.
3. Run the full test suite:
   `PYTHONPATH=src uv run python -m unittest discover -s tests -t . -p 'test_*.py'`.
4. `git fetch origin && git rebase origin/main`, run the suite again, and
   push the result to `main` as a fast-forward. Never force-push. Record
   `status: merged` and the `merge_commit`.
5. A conflict with someone else's change on `main` (`status: conflict`), or a
   test failure it cannot fix (`status: failed`), stops the loop.

The next attempt then runs from a fresh worktree at the new `origin/main`.

### When the loop stops and asks

`ledger.py next` prints `ask-owner`, with every reason that holds, when:

- a Contract Contradiction it already fixed comes back: a later entry has the
  `signature` of one already applied;
- 3 consecutive attempts made no progress: none locked more Components or had
  fewer repeated print defects than the attempt before it;
- the cumulative cost passed `cost_units.cap`, 100 cost units for the toy
  unless the owner set another cap;
- a harness fix fails tests the loop cannot fix, or meets a merge conflict;
- a visible change awaits approval.

Set `loop.state: awaiting-owner` with those reasons in `loop.awaiting`, and
tell the owner in a few plain lines, with the review page's link when there is
one. Record the owner's answer where it clears its reason: `approved` on the
visible change, `recurrence_acknowledged` on the contradiction that came back,
a new `cost_units.cap`, `loop.no_progress_cleared_through`, or the harness
issue's new status. Then clear `loop.awaiting` and run `ledger.py next`
again.

Done when, for each pass, the ledger shows:

- every stop of the attempt in `stops`, with a class from evidence;
- every Contract Contradiction in `contract_contradictions` with its rows, its
  amendment, its re-audit and its `design-a-toy` check;
- every applied in-run Contract Amendment in `in_run_amendments`, folded
  into `CONTRACT.md`;
- every harness issue the loop opened in `harness_issues`, merged or stopping
  the loop;
- the attempt's cost in `cost_units`;
- `ledger.py check` valid, and `ledger.py next` printing either the next
  attempt's `launch` or `ask-owner` with its reasons.

The loop ends when an attempt conforms and is published by Step 7 (`loop.state:
done`), or when the owner stops it (`stopped`).

## The report

End every stop, whether it conformed, hit the cap, did not converge or ran
out of budget, with:

- each round's wish id, toy directory, and finding ids;
- which findings were **unverified** rather than failed;
- what was published, if anything, and how it was confirmed.
