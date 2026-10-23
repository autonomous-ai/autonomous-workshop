- Add the model half of the Print Sheet gate (ADR 0091 decision 7).
  print-details gains `print_recess`, `print_slot`, `print_block`,
  `print_sphere` and `print_fold`, which read each Print Piece's sizes from
  the installed contract (`--install-print`) and tag what they make;
  `check_print_pieces.py` fails a hosted piece with no feature, a recess or
  slot filled again, a block or ball no longer in the part, a stale entry
  and a piece on the wrong part. `make_round` runs it on every hosting part
  as the `paper` gate, and final verification runs it and lays out the
  sheets into `print/sheets/`. The Component Reviewer judges a printed
  area's place, never its picture.
