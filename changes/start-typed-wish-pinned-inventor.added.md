- `workshop start <inventor> --wish BRIEF [--ref IMAGE ...] [--max-rounds N]`
  builds a typed brief as the named Inventor: the Inventor is sealed into the
  Wish context, the run materializes only that Inventor, Match can bind
  nobody else, and Release publishes with that Inventor's own credential.
  Daydream builds under `workshop start` are pinned the same way. See ADR
  0046.
