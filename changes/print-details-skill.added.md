- Add the Workshop-owned `print-details` Make skill (issue #79): a library of
  printable decorative detail -- rivets, round bosses, low domes, raised bands
  and rims, half-round pipe ribs, inset panels with an optional lancet arch,
  windows and grille slits. Every feature refuses a size below the wiki's
  limit for the run's nozzle, naming the limit and its page; grows a root
  into the host so it never stands on a feather edge; gives every face that
  would look down a 52 deg slope in the declared print direction (a support
  swept under a wall rivet, a drafted low flank on a band, a sloped roof over
  a recess, a pointed top on a window) and checks its own tessellated faces
  for it; and returns one valid solid. `--self-check` builds every feature at
  its minimum and default sizes on a top face and on a wall and runs the real
  `check_thickness` and `check_overhang` on each; the test suite runs it.
- It joins `PRODUCT_RUN_DOMAIN_SKILLS` and `LOCK.json`, and its name is
  reserved against Inventor extensions. The Manager copies it into the CAD
  project (`--install` writes `features/print_details.py`) before spawning
  workers; the Component Worker definition and the product-run Make
  reference name it for decorative detail, and the Component Reviewer's
  print limits now match the library's (relief height, cut depth and the web
  between cut copies added). The vendored `cad` and `wiki` trees are
  unchanged.
- **Materialized instruction bytes changed** for new runs: one more skill,
  and new Make reference and role-agent text. Frozen runs keep the bytes they
  materialized.
