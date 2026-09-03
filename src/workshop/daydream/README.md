# Daydream

Owns the stage before a Wish exists: one Inventor dreams one brand-new toy
idea, the idea is linted for novelty, and the surviving idea is sealed as the
plain-text brief that becomes a Wish. Daydream also owns each Inventor's
persistent notebook of ideas already had.

Daydream contains no Match, Invent, Make, Playtest, or Release behaviour. It
hands a `Wish` to Workflow through `wish_from_daydream`, and from there a run
is keyed by an ordinary Wish id so `workshop status` and `workshop resume`
keep working unchanged.

Public API: `workshop.daydream`.

## The two criteria

The founder's rule set for the MVP is two sentences: the idea must be entirely
new, and it must fit what the Inventor's `TASTE.md` describes. Each is
enforced today as follows.

- **Entirely new.** The `DAYDREAM_CONSTITUTION` instructs the Inventor to
  search the web for anything similar, to name the two to five nearest things
  in `prior_art` with the concrete difference in mechanism or play, and never
  to repeat or re-skin any entry of `PRIOR-WORK.md` or `NOTEBOOK.md`. After
  the turn, `lint_novelty` deterministically compares the idea against the
  public toy catalog (`toys/<slug>/wish/wish.json`, falling back to the toy
  README) and against the notebook: an identical normalized title, or a
  Jaccard overlap of content words at or above `NOVELTY_MAX_SIMILARITY`, is
  `too-close`. A too-close idea is recorded as rejected and never sealed.
- **Fits the Taste.** The Inventor reads its exact `TASTE.md` bytes first and
  asserts the fit itself in `taste_fit.honors` and `taste_fit.steers_clear_of`.
  The sealed brief names the Inventor who dreamed it so Match binds the same
  Inventor unless the Taste rejects the final concept, and Invent reviews the
  fit again with the full Taste in hand.

## On-disk layout

    $WORKSHOP_HOME/daydreams/<inventor-id>/NOTEBOOK.jsonl
    $WORKSHOP_HOME/daydreams/<inventor-id>/<daydream-id>/workspace/
        TASTE.md  PRIOR-WORK.md  NOTEBOOK.md  .workshop-product-run-root  work/IDEA.json
    $WORKSHOP_HOME/daydreams/<inventor-id>/<daydream-id>/host-state/
        IDEA.json (sealed)  or  REJECTED.json

Daydream is one native Goal, like every product stage. The host also drops
the constitution into the workspace as `AGENTS.md` and copies the run-local
finalizer `finalize_daydream.py` beside it. The Inventor opens one Goal
(objective: one new, Taste-fitting idea in `work/IDEA.json`), runs the
finalizer, which validates the file's shape and hashes its exact bytes into
`agent-outcome.json`, and completes the Goal. The host passes that marker to
the runtime as the turn's finalization marker and refuses an idea whose
marker is missing or whose bytes no longer match it.

## The judge

Every sealed idea is judged before it is built. The Judge Goal is a second,
short native session in `<daydream-id>/judge-workspace/` with `IDEA.json`,
`TASTE.md`, `ROUTE.md`, the judge constitution as `AGENTS.md`, and the same
finalizer (`--role judge`). It reads the idea the way Make's blind critic
will see two still renders: held object, form, subject, action, relationship,
no exposed mechanism, no hidden signature, no promised feature a render
cannot show, and a size that fits the route. It answers seven questions about those two renders (silhouette changes,
moving part visible in both states, travel is large, body reads as a toy,
mechanism is not dominant, fits the route, worth owning), and writes
`work/VERDICT.json` with those checks, a decision, a confidence, named risks,
and advice. A `build` decision requires all seven checks true; the finalizer
and the host both reject a `build` that contradicts its own checks, so the
judge cannot wave through an idea while naming the reason it will fail. The
host seals the verdict into the idea record and `host-state/VERDICT.json`. The loop
builds only `build` verdicts; a `dream-again` idea is remembered as `judged`
so the Inventor does not repeat it, and `workshop start --idea` can still
build it on purpose.

Every directory is created 0700 with no symlinks; every host file is 0600.
The native Manager session (Codex by default) may write only inside
`workspace/`; under Codex the network is off and web search is on. The
session must write exactly `work/IDEA.json`. The host reads that file,
lints it, and seals a
`SealedDaydream` (idea, seed, Taste identity, Manager id, lint verdict,
redacted session outcome, and the rendered brief) into `host-state/IDEA.json`.

## The loop

`workshop start <inventor>` dreams, builds, and dreams again until it is
stopped. `loop.py` owns the two files that make that safe:

    $WORKSHOP_HOME/daydreams/<inventor-id>/LOOP.json   one lease per Inventor
    $WORKSHOP_HOME/daydreams/<inventor-id>/STOP        stop marker

`acquire_loop` refuses a second loop while the recorded pid is alive, and a
stale record from a dead process is replaced. `request_stop` writes the
marker (and sends SIGINT with `--now`); the loop checks the marker between
steps, so a stop lands after the current daydream or build, never inside one.
The daydream session and each build session stay separate by design: the
idea is sealed and hashed before any build exists.

## Deliberately not in the MVP

No judge or scoring model: the novelty lint is a deterministic floor, not
taste. No outcome feedback: sales, playtests, and reviews do not yet flow back
into the notebook.
