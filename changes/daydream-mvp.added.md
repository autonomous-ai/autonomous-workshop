- Add the Daydream stage before Wish and `workshop start <inventor-id>` as the
  one front-door command: an Inventor dreams one brand-new toy idea through the native Manager
  runtime, obeying its exact `TASTE.md`, searching the web for prior art, and
  writing a strict `work/IDEA.json`. The host lints the idea against the
  public toy catalog and the Inventor's persistent notebook, rejects
  near-duplicates, and seals the survivor with its provenance under
  `$WORKSHOP_HOME/daydreams/`.
- `workshop start` seals the idea as the run's brief (internally still a Wish,
  so `status` and `resume` are unchanged) and starts Invent -> Make -> Release
  by default; `--effort spark` takes the fast Make -> Release route and
  `--idea <daydream-id>` builds a previously saved idea. `workshop daydream
  <inventor-id>` dreams and prints the card without building.
- Under `workshop start`, the daydream prompt names the route budget (Spark: one to
  three parts, one action, one payoff a before/after render proves) so the
  Inventor dreams to the size Make can prove on that route.
