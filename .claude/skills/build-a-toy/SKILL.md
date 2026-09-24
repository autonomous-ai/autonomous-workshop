---
name: build-a-toy
description: Build a toy from a Design Contract until it conforms - run `workshop wish` as round 0, detect every nonconformance against the contract, and run `workshop fix` rounds until none remain, publishing only the conforming build. Use after `design-a-toy` produces a contract, or when an existing toy drifted from its contract.
---

# Build a toy to its Design Contract

`design-a-toy` settles *what* the toy is. This skill owns everything after
that: it builds the toy, checks the build against the contract, and corrects
it until the two agree. The output is one published toy that conforms to its
contract, or a plain report of why no build conformed.

Use the vocabulary in `CONTEXT.md`: **Design Contract**, **Conformance**,
**Requirement Scope**, **Unique Geometry**, **Component** (not "part").

## Legacy mode

This skill runs in **legacy mode** until batch 2 of ADR 0072 adds
`workshop wish --contract`. That has two consequences. State them in every
report:

- The contract travels as the text of the Wish objective. The host does not
  seal it as a contract, and nothing in the run binds its review to it.
  **Conformance is established by this skill, not by the run.**
- The run's `SIGNATURE-REVIEW.json` lists only the requirements the Manager
  chose to write. [DETECT.md](DETECT.md) treats that list as a record of what
  was checked, not of what should have been checked.

## The settled run parameters

Every run this skill starts, whether `wish` or `fix`, uses:

| Flag | Value | Why |
|---|---|---|
| `--no-publish` | always, round 0 included | Nothing reaches Factory until it conforms |
| `--turn-minutes` | `360` | The maximum. The clock is not the limit |
| `--max-tokens` | `100000000` | **This is the real backstop.** With 360-minute turns and unlimited resume, a run stops when its tokens run out |
| `--ref` | every contract reference, every run | The assembly round scores every sealed reference that no current component round already scored (ADR 0072). A description of an image is no substitute for the image |
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
workspace, toy directory, final status, brief path and finding ids. Resuming
this skill in a later session starts from the ledger, not from memory.

Done when: the contract validates with no errors, and the ledger exists.

## Step 2 - Round 0: the wish

Skip this step when an existing toy was given. That toy is round 0: run
Step 4 on it.

Write the objective. Its first line is `Name this toy exactly: <title> v01.`,
and the full `CONTRACT.md` follows. Every build in the chain takes a
suffixed name. A local, unpublished projection can never overwrite a
different `toys/<slug>`, so reusing a name strands the run at its last step.
Build the command:

```bash
uv run workshop wish "$(cat <objective-file>)" --inventor <inventor> \
  --ref <contract-dir>/ref-01-<slug>.png --ref ... \
  --no-publish --turn-minutes 360 --max-tokens 100000000
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
- Anything else means the run is **incomplete**, which is not a design
  result. Read the receipt's `stop_category` (present whenever `status` is
  not `complete`) to decide what to do next, rather than guessing from
  `status`, `stage` or token counts:
  - `transport` or `inspection-in-progress`: the stop is resumable and, for
    `inspection-in-progress`, still converging. Resume it:
    `uv run workshop resume <wish-id> --turn-minutes 360 --json`. Leave
    `--max-tokens` out, because a resume keeps the saved budget. Resumes are
    unlimited and never count as a round.
  - `budget`: report plainly that **the token budget, the run's only
    backstop, is exhausted**. Hand the decision to the person. A resume
    cannot proceed past it.
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
- Then this line: *every other requirement of the Design Contract below still
  holds; a correction may not trade one requirement for another.*
- Then a size budget, so the next round can still chain: `assembled.step`
  under 12 MB, and the heaviest Component under 4 MB.
- Then the full `CONTRACT.md`. A correction run reviews against its brief
  (ADR 0065), so the whole contract has to be in the brief.

The brief becomes the correction run's Wish objective, which is limited to
50,000 characters. If it is over the limit, stop and show the person. Cutting
the contract to fit would remove exactly the requirements the run is judged
against. Shorten the findings instead.

**Show the person the brief and the exact command, and wait for explicit
approval.** Then run the correction from the previous round's **run
workspace**, not from `toys/`. The workspace is smaller than the published
archive, and it stays within `fix`'s 128 MiB source limit.

```bash
uv run workshop fix "<previous-run-workspace>" --prompt-file build-a-toy/r<NN>/brief.md \
  --ref <contract-dir>/ref-01-<slug>.png --ref ... \
  --no-publish --turn-minutes 360 --max-tokens 100000000
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

## The report

End every stop, whether it conformed, hit the cap, did not converge or ran
out of budget, with:

- each round's wish id, toy directory, and finding ids;
- which findings were **unverified** rather than failed;
- that the contract was supplied in **legacy mode** and is not hash-bound to
  any run;
- what was published, if anything, and how it was confirmed.
