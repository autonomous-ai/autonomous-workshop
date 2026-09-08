- `make_round` resolves a reference path the way the Manager wrote it:
  absolute, project-relative, cwd-relative, or relative to the run workspace
  (the directory holding `WISH.json`). A workspace-relative path used to
  score as "reference missing" and cost the round its likeness number.
