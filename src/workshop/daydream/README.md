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

Every directory is created 0700 with no symlinks; every host file is 0600.
The native Manager session (Codex by default) may write only inside
`workspace/`; under Codex the network is off and web search is on. The
session must write exactly `work/IDEA.json`. The host reads that file,
lints it, and seals a
`SealedDaydream` (idea, seed, Taste identity, Manager id, lint verdict,
redacted session outcome, and the rendered brief) into `host-state/IDEA.json`.

## Deliberately not in the MVP

No always-on loop: one call dreams one idea. No judge or scoring model: the
novelty lint is a deterministic floor, not taste. No outcome feedback: sales,
playtests, and reviews do not yet flow back into the notebook.
