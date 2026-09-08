- `workshop resume <wish> --decide "TEXT"` records the person's decision on a
  run's open need (an explicit likeness acceptance below the 0.90 floor, an
  authorization, a component choice) in the run's private host state
  (`host-decisions.jsonl`, owner-only) and lists it in every later
  `STAGE.json` as `inputs.host_decisions`, with the checkpoint, stage, round
  and needs it answers. The stage subject is untouched, so the Manager
  continues the same Goal with the answer in hand. New public helper
  `workshop.workflow.record_native_run_decision`. See ADR 0060.
