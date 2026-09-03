# Run budgets v1

This run measures work in wall-clock time, not in turns. There are exactly two
clocks and nothing else stops the command.

- **Each step gets 60 minutes** of one command: Invent, Make, Playtest, and
  Release each have their own hour.
- **The command gets 3 hours** in total across all of its steps.

Inside those clocks you may take as many native turns as the work needs. When a
turn ends without your stage finalizer having run, the host continues the exact
same session and the same Goal automatically; that is ordinary, not a failure,
and it costs nothing but the minutes it used. A turn is bounded by whatever the
two clocks still allow, so a turn never outlives its step.

When a clock runs out the command stops with one sentence naming the clock, and
the exact session stays checkpointed. An explicit `workshop resume` starts fresh
clocks and continues the same Goal.

What this replaces for this run: the three-unfinished-turn window, the
two-recoverable-turn window, and the per-command native turn caps. They do not
apply here.

What still applies: the Invent-Make-Playtest round budget, the proposal
rejection budgets, every deterministic gate, and the stage review rounds. Those
are quality rules, not timers, and a budget never waives one. Spend your minutes
on the product, finalize the stage as soon as it is truthfully ready, and return
control to the host.
