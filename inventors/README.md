# Inventor specialists

Each immediate subfolder is one reusable source bundle for a standard native
subagent. “Inventor” is the Workshop's friendly role name, not a competing
agent abstraction or product category.

```text
inventors/<id>/
  inventor.json             schema-v8 source metadata and exact skill hashes
  TASTE.md                  human-owned creative judgment and Match boundary
  skills/<id>-inventor/     required primary portable agent skill
    SKILL.md                specialist method and tool routing
    scripts/                optional tested deterministic tools
    references/             optional specialist reference material
    assets/                 optional templates and static inputs
  skills/<id>-<specialty>/  optional additional portable agent skill
```

`inventor.json` contains only the stable id, status, source, and sorted
content-bound skill records. It does not decide what a person may Wish for or
which kinds of product the Inventor is allowed to make. Match compares the
exact Wish with the full Taste and method of every eligible Inventor.

For each product run, the host validates these source bundles and
deterministically projects them into the selected Manager's official
project-scoped agent and skill layout. `MANAGER.json` names that exact layout;
the selected projection is the sole Inventor identity, Taste, and skill roster
inside the toy project. There is no second run-local identity tree. One
persistent native coding-agent session acts as Workshop Manager and uses its
own subagent controls to spawn the selected Inventor.

The same canonical bundle becomes `.codex/agents/*.toml` plus
`.agents/skills/**` for Codex, `.claude/agents/*.md` plus `.claude/skills/**`
for Claude Code, or `.grok/agents/*.md` plus `.grok/skills/**` for Grok Build.
The formats differ, but identity, full Taste, and declared skill-tree bytes do
not. One Wish materializes exactly one of those projections and remains bound
to that Manager; runtimes do not concurrently mutate a Wish or resume one
another's native sessions.

Each Match, Invent, Make, Playtest, or Release attempt has one active native
Goal. The Manager and its native children observe, act, evaluate, and
improve while pursuing that Goal. Inventor scripts do not implement this loop.
They may provide bounded deterministic specialist operations such as CAD
generation, simulation, parsing, or evaluation, but they must not launch
agents, schedule prompts, choose lifecycle transitions, waive gates, access
credentials, or perform external effects.

For procedural 3D craft, any selected Manager—including Grok Build—may invoke
the same declared Blender, CadQuery, OpenSCAD, rendering, and measurement
resources. A plausible render or model-authored assessment is not a trustworthy
solid, mesh, print, or physical fit; Workshop's deterministic gates and
authenticated physical evidence remain authoritative.

The bundled Inventors currently use one concise instructions-only primary
skill each. Shared CAD, simulation, and evidence tooling stays in Workshop.

| Inventor | Native skill |
|---|---|
| Alice | `alice-inventor` |
| Bob | `bob-inventor` |
| Eve | `eve-inventor` |
| Ivy | `ivy-inventor` |
| Leo | `leo-inventor` |

`TASTE.md` begins with the bounded `name` and `description` used for Match.
Verified run evidence may motivate a proposed Taste or skill revision, but only
a human changes the reusable source bytes.

Create a base specialist from the repository root using an existing Taste:

```bash
uv run workshop create inventor \
  --taste ./TASTE.md \
  --root .
```

Or generate the initial Taste and skill from explicit identity text:

```bash
uv run workshop create inventor pocket-orreries \
  --name Ada \
  --description "Choose Ada for personalized orbit models with legible motion; not generic decor." \
  --root .
```

Reusable Workshop-wide deterministic tools belong to the stage that owns them
under `src/workshop/`; genuinely Inventor-specific tools may remain in the
source bundle. Product artifacts belong to the private toy project and are not
stored under `inventors/`.
