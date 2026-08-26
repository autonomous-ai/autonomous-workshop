# Inventor specialists

Each immediate subfolder is one specialist bundle for a standard native
subagent. “Inventor” is the Workshop's friendly role name, not a competing
agent abstraction. Taste, the catalog record, and one primary extension skill
are required; additional extensions are optional and must be declared by
`inventor.json`:

```text
inventors/<id>/
  inventor.json  identity, eligibility, capabilities, extension inventory
  TASTE.md       exact human-owned creative judgment
  skills/<id>-inventor/     required primary Codex skill
    SKILL.md     required specialist workflow and tool routing
    scripts/     optional tested deterministic tools
    references/  optional specialist reference material
    assets/       optional templates and static inputs
  skills/<id>-<specialty>/  optional additional Codex skill
```

An optional concise `README.md` may explain the bundle. For a product run, the
host deterministically projects every eligible bundle into an official
project-scoped `.codex/agents/<id>.toml` custom agent. One root native Codex
session acts as Workshop Manager and spawns the selected Inventor through Codex;
it does not start a profile subprocess, second root session, or Python loop.

Inventor scripts may implement tested deterministic specialist operations such
as CAD generation or evaluation. Each additional skill has an Inventor-prefixed
name and a manifest-bound tree hash. Scripts never auto-run and must not launch
agents, schedule prompts, choose lifecycle transitions, waive gates, access
credentials, or perform external effects. Static validation proves structure
and bytes, not arbitrary-code semantics; the runtime sandbox and host gates
remain authoritative.

The five bundled schema-v7 Inventors each declare exactly one minimal
instructions-only skill. They add no scripts or custom code; shared CAD,
simulation, and evidence tooling remains in Workshop.

| Inventor | Lane | Native skill |
|---|---|---|
| Alice | classics made yours | `alice-inventor` |
| Bob | moving machines | `bob-inventor` |
| Eve | little worlds | `eve-inventor` |
| Ivy | holdable science | `ivy-inventor` |
| Leo | invented games | `leo-inventor` |

`TASTE.md` begins with the bounded `name` and `description` used for Match.
The complete exact declared bundle is materialized into a private product-run
workspace under a content-bound manifest. Verified outcomes may justify a
proposed Taste or skill revision, but only a human changes the catalog bytes.

Create a base specialist from the repository root:

```bash
workshop create inventor pocket-orreries \
  --name Ada \
  --description "Choose Ada for personalized orbit models; not games or decor." \
  --lane holdable-science \
  --root .
```

Reusable Workshop-wide deterministic tools belong to the stage that owns them
under `src/workshop/`; genuinely Inventor-specific tools may remain in the
declared specialist bundle. Product artifacts belong to the private run
workspace and are never checked into this catalog.
