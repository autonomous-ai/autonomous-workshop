- Raise the native turn boundary to 60 minutes for new Spark runs (was 20)
  and for the normal Forge and Quest turn (was 30). Healthy Spark Make turns
  took 17 to 35 minutes on a quiet machine and timed out whenever several
  sessions shared one host; two timeouts in a row stopped the command. The
  short first-turn handoffs (Invent 20/10, Make proof 16, final Make 15) and
  the 15-minute Daydream turn are unchanged. Runs frozen before this change
  keep their original boundaries.
- Give each budgeted step 120 minutes and each command 6 hours, so one
  maximum-length turn can never exhaust its own step. The first live budgeted
  run lost an hour of finished Make work to a step budget that equalled the
  turn boundary; a step now has room for the resume that would have finalized
  it. A step with under 10 minutes left is treated as spent rather than
  starting a turn that cannot finish.
