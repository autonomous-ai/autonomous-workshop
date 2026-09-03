- Add the Daydream stage before Wish: `workshop daydream <inventor-id>` lets
  one Inventor dream one brand-new toy idea through the native Manager
  runtime, obeying its exact `TASTE.md`, searching the web for prior art, and
  writing a strict `work/IDEA.json`. The host lints the idea against the
  public toy catalog and the Inventor's persistent notebook, rejects
  near-duplicates, and seals the survivor with its provenance under
  `$WORKSHOP_HOME/daydreams/`.
- `--run` seals the liked idea as the run's brief (internally still a Wish,
  so `status` and `resume` are unchanged) and starts Invent -> Make -> Release
  by default; `--effort spark` takes the fast Make -> Release route and
  `--idea <daydream-id>` runs a previously saved idea.
- With `--run`, the daydream prompt names the route budget (Spark: one to
  three parts, one action, one payoff a before/after render proves) so the
  Inventor dreams to the size Make can prove on that route.
