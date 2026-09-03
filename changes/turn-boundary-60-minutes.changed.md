- Raise the native turn boundary to 60 minutes for new Spark runs (was 20)
  and for the normal Forge and Quest turn (was 30). Healthy Spark Make turns
  took 17 to 19 minutes on a quiet machine and timed out whenever several
  sessions shared one host; two timeouts in a row stopped the command. The
  short first-turn handoffs (Invent 20/10, Make proof 16, final Make 15) and
  the 15-minute Daydream turn are unchanged. Runs frozen before this change
  keep their original boundaries.
