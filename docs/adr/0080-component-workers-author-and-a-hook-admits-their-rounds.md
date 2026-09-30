# ADR 0080: Component Workers author their Components, and a hook admits their rounds

- Status: Accepted as an experiment on branch `rein/remove-likeness`;
  implemented and deterministically tested; not yet validated by a live run
- Date: 2026-09-30
- Owners: product-run Make instructions (`references/make.md`, product-run
  `AGENTS.md`, `SKILL.md`), Make role agents (`src/workshop/make/agents/`),
  `make-round` skill, the make_round guard (`make/make_round_guard.py`,
  `make/role_guard.py`, `runtime/make_round_hook.py`), Workshop host run creation and Make acceptance
  (`agent_run.py`, `native_run.py`), native launchers (`runtime/claude.py`,
  `runtime/codex.py`), `design-a-toy` skill
- Amends: ADR 0077 (who authors a Component, who views which image) and
  ADR 0063 step 1 (the root no longer authors Spark Components)

## Context

Broken God attempt 9 (`wish-20260930-080047-caa9d7af`, Claude Code) was
stopped after about 64 minutes in Make round 1. About 38 minutes went to the
Manager's thinking before any CAD, including one turn of about 100k output
tokens. Three causes showed in its transcript and notes:

1. **The Design Contract contradicted itself.** The chest cage and spine
   housing printed on their mating faces, but four pegs joined those faces.
   The spine housing's neck collar stood in front of it, so in that print
   stance it printed over air. A "Hidden joints" section, added after an
   earlier attempt stopped on a peg, handed all joint geometry to Make.
   Make had no route for a contradiction: `SKILL.md` forbade `need` for an
   engineering choice, so the Manager resolved it alone, at length.
2. **Nobody was assigned the first draft.** ADR 0063 left every
   `part_<id>.step.py` to the root; ADR 0077 moved only the repair loop to
   workers. The Manager spawned six selected-Inventor agents to author
   Components, which the delegated-design rule allowed, and kept four
   Components itself.
3. **Restricting spawns would not fix it.** The Manager legitimately spawns
   Inventors, a blind critic and research agents. The fix is to decide who
   may run which `make_round` call, not who may spawn whom.

## Decision

1. **The Component Worker authors.** In Spark Make the root writes only the
   shared `params.py` and `features/` files. It fixes every interface there
   before spawning: each joint's peg, socket or collar dimensions, their
   positions on both mating Components, and each Component's print stance,
   all from the Design Contract. Each `component-worker` then writes its
   Component's first draft and repairs it (ADR 0077). The root keeps no
   Component. An Inventor's design notes stay optional; an Inventor never
   authors a Component or runs `make_round`.
2. **Who views what.** The worker may view its own sealed `geometry:<id>`
   reference once, when it starts, and keep it in mind. It never views the
   rendered rounds (front, top, iso, `compare-NN.png`, the visual packet);
   only the Component Reviewer does.
3. **A hook admits each `make_round` call by role.** A new run's host state
   holds a `PreToolUse` hook, `make_round_guard.py`, outside the workspace.
   A component round (`--component` without `--record-review`) runs only
   from `agent_type == component-worker`. `--record-review`,
   `--record-visual` and assembly rounds run only from the root, which has no
   `agent_type`. Anything else naming `make_round` passes unchanged, except a
   command the hook cannot parse, with two calls, with a caller-supplied
   `--worker-nonce`, or with a quoted script path the nonce cannot follow,
   which it refuses.
4. **A nonce binds each component round to a worker.** For an admitted
   worker call the hook appends a one-time nonce, the Component and the
   caller to a host-side nonce table and rewrites the command to pass
   `--worker-nonce`. `make_round` records it in the round's `summary.json`.
   At Make acceptance the host refuses output holding any component round
   whose nonce it did not issue to a worker for that Component, or that
   reuses a nonce. In Spark every `part_<id>.step.py` must also have at
   least one such round. This catches calls the hook cannot see, such as
   `python -c`. A round whose exact summary bytes the revision source sealed
   was carried forward by a correction and keeps its evidence.
5. **Both runtimes, one script.** Claude Code receives the hook with
   `--settings <json>` on every turn. Codex receives
   `--enable hooks` and `--config hooks.PreToolUse=[...]` with
   `--dangerously-bypass-hook-trust`: Workshop launches Codex with
   `--ignore-user-config`, so a project hooks file is never read, and the
   host itself wrote the hook it trusts. The checkpoint binds the hook's
   sha256 and every snapshot refuses a changed or missing guard.
6. **A contract contradiction is a `need`.** When two Design Contract
   statements cannot both hold, Make returns `waiting` quoting both. A
   detail the contract leaves open, or a freedom it grants, stays with Make.
7. **The contract pins joints and print stances.** `design-a-toy` decides
   every joint's geometry and every Component's print stance, and its
   printability check reads each hidden joint against the Component's print
   bed face and overhangs. A contract no longer delegates hidden joints to
   Make.

## Consequences

- The root's Make context holds shared files and assembly only; Component
  authoring and its reads move to short-lived workers.
- A root or Inventor that runs a component round is refused at once, with a
  reason naming the worker. An indirect call costs its rounds: they are
  refused at acceptance and must be rerun by a worker.
- **Tamper-resistant, not tamper-proof.** Claude Code runs with
  `bypassPermissions` and no sandbox, so an agent can reach host state with
  its own tools and forge the nonce table. The guard makes a wrong-role
  round deliberate rather than accidental; it is not a security boundary.
- Grok has no verified hook naming the calling subagent, so a Grok run gets
  no guard. Forge and Quest receive it but do not run component rounds.

## Compatibility and migration

Frozen runs keep what they materialized: a run created before this change has
no guard in host state, launches without a hook, and its Make acceptance skips
the nonce check. Only new Codex and Claude Code runs receive the guard and the
new wording.

## Verification

Deterministic tests cover the hook's parsing and decisions, the nonce table,
host acceptance (missing, unknown, wrong-Component, wrong-role, reused and
carried nonces), the checkpoint binding and tampered guard, both launchers'
arguments and the new instruction text. Probes on 2026-09-30 showed that a
Claude Code 2.1.285 `PreToolUse` hook names a subagent's `agent_type`, and
that `--settings` delivers a hook that can deny and rewrite a call. For
Codex 0.158.0 a probe showed the same hook fields and deny; a hook passed by
`--config` did not run without hook trust, and the trust bypass flag was not
probed. A live run on each runtime must confirm the hook runs, that Codex
runs it where it can write host state, and that workers author Components.

## Rejected alternatives

- **Restrict which agent types the root may spawn.** Blocks legitimate
  Inventor, critic and research agents and still lets the root run rounds.
- **A hook alone.** It cannot see a round run through another program.
- **A nonce alone.** A wrong-role call would run to completion and be
  refused only at acceptance, after its cost was paid.
- **A hooks file in the workspace.** The agent can edit it; the host state
  copy is out of its way, and Codex would not read it anyway.
