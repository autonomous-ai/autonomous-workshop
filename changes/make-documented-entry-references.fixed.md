- Make final and print-preflight verification refuse a project whose README or
  spec names a `<name>.step.py` entry that does not exist, so a delivered file
  map or rebuild command cannot cite a removed entry and fail on first use.
