# anchors — judge-drift detection set

Fixed reference games. Whenever a judge prompt or model changes, every anchor
is re-scored; movement on anchors is judge drift, not game quality, and blocks
the change (docs/REWARD.md §Judge discipline).

Required set (to be generated in Bob's real game schema at first integration
run, then FROZEN — the improve loop may never touch this directory):

| anchor | kind | what it calibrates |
|---|---|---|
| `hex-classic/` | known-good | depth + clarity ceiling (a proven deep abstract) |
| `crokinole-style/` | known-good | physical_hook ceiling (dexterity that needs the object) |
| `first-wins-race/` | known-bad | degeneracy gate (seat 1 always wins by construction) |
| `no-decisions-walk/` | known-bad | agency floor (roll-and-move with zero choices) |
| `azul-reskin/` | plagiarism trap | novelty gate (a known modern game re-themed; judge must kill with the BGG URL) |

Status: **not yet generated** — `bob.py seed` creates them from the templates
the first time it runs with a working schema. Until then, integrity.audit()
reports the missing set as a warning, not a failure.
