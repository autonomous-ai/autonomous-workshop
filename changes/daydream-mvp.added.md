- Add the Daydream stage before Wish and `workshop start <inventor-id>` as the
  one front-door command: an Inventor dreams one brand-new toy idea through the native Manager
  runtime, obeying its exact `TASTE.md`, searching the web for prior art, and
  writing a strict `work/IDEA.json`. The host lints the idea against the
  public toy catalog and the Inventor's persistent notebook, rejects
  near-duplicates, and seals the survivor with its provenance under
  `$WORKSHOP_HOME/daydreams/`.
- `workshop start` seals the idea as the run's brief (internally still a Wish,
  so `status` and `resume` are unchanged) and starts Make -> Release (Spark)
  by default; `--effort forge` adds Invent and `--effort quest` adds Playtest;
  `--idea <daydream-id>` builds a previously saved idea. `workshop daydream
  <inventor-id>` dreams and prints the card without building.
- `workshop start` is a loop: after each build it dreams the next idea, until
  `workshop stop <inventor-id>` (after the current step; `--now` interrupts),
  Ctrl-C, `--max-ideas N`, or three consecutive failures. One loop per
  Inventor at a time (`LOOP.json` lease, `STOP` marker).
- Daydream is one native Goal like every product stage: the workspace carries
  the constitution as `AGENTS.md` and the run-local `finalize_daydream.py`,
  which validates `work/IDEA.json` and writes the bound `agent-outcome.json`
  that completes the Goal; the host requires that marker.
- An independent Judge Goal bets on every sealed idea before a build: it
  answers seven questions about the two still renders the idea would produce
  (does the silhouette change, is the moving part visible in both states, is
  the travel large, does the body read as a toy, is the mechanism not
  dominant, does it fit the route, is it worth owning) and writes a `build`
  or `dream-again` verdict with named risks. `build` requires all seven true;
  the run-local finalizer and the host both reject a `build` that contradicts
  its own checks. The loop builds only `build` verdicts and stops after five
  judged-out ideas in a row.
- Ideas now carry `before_after`, the two states a fixed camera must show,
  and the constitution asks for a visible change: a different outline, travel
  of at least a third of the toy's longest dimension or 45 degrees, the
  moving part visible in both states, and nothing that matters hidden inside.
- Under `workshop start`, the daydream prompt names the route budget (Spark: one to
  three parts, one action, one payoff a before/after render proves) so the
  Inventor dreams to the size Make can prove on that route.
