- `--ref` on `workshop wish` and `workshop start --wish` now also takes an
  `http(s)` link. The CLI downloads it once at Wish time (12 MB cap, 30 s
  timeout, redirects only within http(s)), runs the same PNG/JPEG/WebP checks
  as a file, names it from the link's path, and seals the bytes by SHA-256
  like any reference; `WISH.json` records the link under
  `context.reference_sources`. The run itself never fetches anything. New
  public helpers `is_reference_url` and `wish_reference_sources` in
  `workshop.wish`. See ADR 0058.
