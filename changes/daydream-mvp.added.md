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
- Under `workshop start`, the daydream prompt names the route budget (Spark: one to
  three parts, one action, one payoff a before/after render proves) so the
  Inventor dreams to the size Make can prove on that route.
