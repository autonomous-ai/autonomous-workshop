- New host-owned domain skill `make-round`: `scripts/make_round` runs one
  Make iteration as one command (export, wall-check changed parts, likeness
  per reference with pose replay, motion gate, optional final verify) and
  prints a short summary; its `SKILL.md` is the tool card with the exact
  invocation of every cad and image-to-cad gate. The product-run
  constitution routes each repair round through it, forbids reading skill
  scripts for flags, and limits image viewing to once per round. Aimed at
  the 925 requests and 39M tokens the first microduck cost. See ADR 0057.
