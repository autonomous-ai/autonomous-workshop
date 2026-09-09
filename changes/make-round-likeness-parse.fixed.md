- `make_round` read no likeness score from `render_views --json`, which prints
  one pretty-printed object with the per-label IoU under `views`, not a
  one-line object under `results`; every round reported `render_views exit 0`
  as an error while the gate itself had passed. The parser now reads the
  whole object and either key. Found on the first live run (goose, 2026-09-08).
