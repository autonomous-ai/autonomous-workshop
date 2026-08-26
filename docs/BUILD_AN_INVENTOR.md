# Build an Inventor

An Autonomous Workshop Inventor is a standard native subagent specialized by a
declared source bundle and used by the root Codex Workshop Manager. “Inventor”
is the friendlier product-language role name; it is not another agent runtime,
a product category, a subprocess, or a stage owner.

Every Inventor contributes Taste, a schema-v8 source manifest, and one primary
skill. Additional Inventor-prefixed skills and resources are optional:

```text
inventors/<id>/
  TASTE.md                  required creative judgment
  inventor.json             required source metadata and exact skill hashes
  skills/<id>-inventor/     required primary Codex skill
    SKILL.md                specialist method and tool routing
    scripts/                optional tested deterministic tools
    references/             optional specialist reference material
    assets/                 optional immutable templates or references
  skills/<id>-<specialty>/  optional additional Codex skill
```

Workshop supplies the root Manager, lifecycle, contracts, gates, shared skills,
and effect boundaries. At run creation the host validates reusable Inventor
sources and materializes each eligible one as an official project-scoped
`.codex/agents/<id>.toml` custom agent. Those files are the sole Inventor
identity, Taste, and skill roster in the toy project. The Manager delegates
through Codex's native controls; it does not launch another OS-level Codex
process or a Python worker.

## 1. Write `TASTE.md`

The frontmatter exposes a stable name and a short matching boundary. The body
describes a recognizable creative point of view.

```markdown
---
name: Ada
description: Choose Ada for hand-cranked creatures; not static models or games.
---

# Ada's taste

I love mechanisms whose motion tells the story. I reject decoration without play.
I prefer visible cams, linkages, and constraints over hidden electronics.
```

Good Taste helps the native agent make hard choices. Include:

- what this Inventor loves;
- what it rejects;
- what makes a result unmistakably theirs;
- a clear “not for” boundary;
- truthful domain constraints that affect product decisions.

Taste guides Match; it does not restrict what users may Wish for. Do not put
credentials, effect authority, Python entry points, fixed prompts, customer
data, or instructions for bypassing Workshop gates in Taste.

## 2. Create the source bundle

Use the CLI so identifiers, the primary skill, and content hashes are generated
by the shared contributor tooling. With an existing Taste:

```bash
uv run workshop create inventor \
  --taste ./TASTE.md \
  --root .
```

Or generate a starting Taste from explicit identity text:

```bash
uv run workshop create inventor ada \
  --name Ada \
  --description "Choose Ada for hand-cranked creatures; not static models or games." \
  --root .
```

`inventor.json` records only stable source metadata and exact skill-tree
bindings:

```json
{
  "schema_version": 8,
  "id": "ada",
  "status": "experimental",
  "source": {"kind": "local"},
  "extensions": [
    {
      "kind": "codex-skill",
      "name": "ada-inventor",
      "path": "skills/ada-inventor",
      "artifact_sha256": "<sha256 of the exact skill tree>"
    }
  ]
}
```

Keep this file small. Match reasoning comes from the exact Wish, full Taste,
and specialist method rather than a predeclared product class. The host binds
the manifest, Taste, and complete skill bytes into the generated custom-agent
file; do not maintain a second hand-written run identity.

## 3. Add specialist craft only when it is truly Inventor-owned

The primary skill must be named `<id>-inventor`. Use it for the specialist's
core method: how it approaches its craft, when it invokes a declared tool, and
what evidence it leaves. Additional skills must also be prefixed by the
Inventor id so they cannot collide with a shared Workshop skill. Keep each
`SKILL.md`, referenced script, reference, and asset inside that exact tree.

The manifest binds every complete skill tree by content hash; no script
auto-runs. Optional code must be a bounded, tested deterministic operation such
as a CAD generator, geometry evaluator, simulator, parser, or domain checker.
It may accept files and produce files or measurements. It must not:

- launch Codex, Claude Code, Grok Build, or another model/agent;
- schedule prompts or subagents;
- create or control a Goal;
- choose a lifecycle transition or report its own gate passed;
- read credentials or call credential-bearing effects;
- hide reusable Workshop-wide behavior inside one Inventor.

Each active Match, Invent, Make, Playtest, or Release attempt has one native
Codex Goal owned by the root Manager. The selected Inventor may contribute
bounded specialist work inside that Goal. Codex observes, acts, evaluates, and
improves; Inventor Python never implements the reasoning or feedback loop. The
root Manager reviews the work and submits the stage proposal, and the host
independently reruns trusted checks and decides the gate.

Static contribution validation proves bundle structure and exact hashes, not
the meaning or safety of arbitrary code. Keep repository tests for every
script; runtime sandboxing, deterministic stage checks, and host gates remain
authoritative.

## 4. Validate the specialist bundle

Run the checked-in source and secret checks before committing:

```bash
uv run workshop inventors --root inventors
uv run workshop check inventors/ada
python tools/scan_secrets.py
git diff --check
```

Then start a representative private Wish and inspect the Match evidence:

```bash
uv run workshop wish \
  "I wish for a hand-cranked creature that climbs the edge of my bookshelf"
```

The root Codex Manager compares every exact custom agent supplied in the
`STAGE.json` Inventor roster, records an evidence-based ranking, and selects
one. Where useful, it delegates bounded candidate analysis to native
subagents. It then uses the selected `.codex/agents/<id>.toml`, whose
instructions bind the exact manifest, full Taste, and skill resources. There
is no profile launch, custom Python worker, or second root session to test.

## Shared craft belongs to Workshop stages

If many Inventors or products need reusable making knowledge, add or improve a
domain skill under `src/workshop/make/skills/` and its deterministic checker
under the component that owns the contract. Inventor-owned resources are for
genuinely specialist craft; do not duplicate shared CAD, simulation, or
validation logic inside every Inventor folder.

If one Inventor needs a stricter creative standard, express it in `TASTE.md`.
If the standard must be mechanically enforced for Release, implement a narrow
deterministic contract or gate in Workshop. Do not implement it as a model
self-score or Python reward function.

## Review checklist

- The description distinguishes when this Inventor should and should not match.
- The Taste body contains real choices rather than generic quality advice.
- The schema-v8 manifest binds every skill tree exactly.
- Any Inventor-owned code is deterministic, tested, and cannot orchestrate
  agents, Goals, lifecycle, or effects.
- Shared tools remain in Workshop rather than being copied into a specialist.
- A private representative Wish can Match without weakening any host gate.
