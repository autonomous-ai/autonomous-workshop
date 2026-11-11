# ADR 0100: Domain skills have their own input budget

- **Status:** Accepted on 2026-11-11 (owner decision, option A).
- **Scope:** `AgentRun` input budgets in `src/workshop/workflow/agent_run.py`
  for runs created from now on. Frozen and running runs are unchanged.
- **Relates to:** issue #281 (the follow-up: a run-local wiki index with
  pages read on demand).

## Context

Each run copies its installed inventory into the run root, and the
tamper-checked input manifest binds it by hash. Before this ADR, everything
except Wish references, a revision input and a seed shared one combined cap,
`MAX_AGENT_INPUT_BYTES`, set at 6 MiB.

On 2026-11-11 the installed inventory was 6,061,623 bytes in 515 files, just
over that cap:

- Vendored domain skills: 5,120,848 bytes. The `wiki` skill alone is
  1,822,368 bytes.
- Everything else: 940,775 bytes (the `autonomous-workshop` skill, the
  Inventor skills, `.codex/`, AGENTS.md and the root files).

The domain skills grow with every upstream resync. The run's own files grow
slowly. Because both shared one cap, a wiki resync could refuse every new run
and push an unrelated host correction over the limit.

## Decision

New runs have two installed-inventory budgets, both checked on exact bytes:

- **Domain skills: 8 MiB** (`MAX_DOMAIN_SKILL_BYTES`). This covers every file
  under `.agents/skills/<name>/` for each domain skill the run selected.
- **Everything else: 2 MiB** (`MAX_RUN_OWN_INPUT_BYTES`). This covers the
  workshop skill, the Inventor skills and agents, `.codex/`, AGENTS.md and the
  root inputs.

The total ceiling is 10 MiB. Wish references, the revision input and the seed
keep their own budgets, as before. The 768-file limit and the 6 MiB
single-file limit are unchanged.

The checkpoint records the sorted names of the selected domain skills as
`domain_skills`. That list decides which files count against which budget, so
neither the agent nor a stray path can move bytes between budgets:

- On open, every named skill must have its `SKILL.md` among the bound inputs.
- The list must be sorted, unique and made of valid domain skill names. It
  never contains `autonomous-workshop`.

Every check applies the split budgets. That means creation, every open and
resume, and every host rebind: host corrections and
`refresh_domain_skill_tools`. Each refusal names the budget it broke, for
example:

- `agent run domain skills exceed their 8 MiB byte budget (N > 8388608 bytes; ADR 0100)`
- `agent run inputs other than domain skills exceed their 2 MiB byte budget (N > 2097152 bytes; ADR 0100)`

A refused creation leaves no run root. A refused refresh writes nothing.

## Frozen and running runs

A checkpoint without `domain_skills` was created before this ADR. It keeps the
single combined 6 MiB rule on open, resume and refresh, with the same message
as before. Its checkpoint hash is unchanged. No migration adds the field. A
refresh that would push such a run past 6 MiB is still refused.

## Consequences

- A wiki resync that would cross 6 MiB no longer refuses every new run. The
  domain skills have about 3 MiB of room. The rest has about 1.1 MiB, which
  is held to its own 2 MiB.
- `test_complete_installed_inventory_can_materialize_and_reopen` checks the
  real installed inventory. It fails, naming the budget, when domain skills
  leave less than 1 MiB of headroom or the rest less than 512 KiB.
- Nothing becomes hermetically weaker. The agent can still read only what
  the hash-bound manifest records. Issue #281 is how the wiki should stop
  growing the run root; this ADR only separates the budgets.
