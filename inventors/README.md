# Inventor specialists

Each immediate subfolder is one reusable source bundle for a standard native
subagent. “Inventor” is the Workshop's friendly role name, not a competing
agent abstraction or product category.

```text
inventors/<id>/
  inventor.json             schema-v8 source metadata and exact skill hashes
  TASTE.md                  human-owned creative judgment and selection boundary
  skills/<id>-inventor/     required primary Codex skill
    SKILL.md                specialist method and tool routing
    scripts/                optional tested deterministic tools
    references/             optional specialist reference material
    assets/                 optional templates and static inputs
  skills/<id>-<specialty>/  optional additional Codex skill
```

Daydream hands the Inventor only its `TASTE.md`: `workshop daydream <id>`
validates the bundle, puts the exact Taste bytes in front of the Inventor, asks for one brand-new idea
that fits it, and names the Inventor who dreamed it in the sealed brief.
`workshop start <id>` pins the run's roster to that one Inventor, exactly as
`workshop wish --inventor <id>` does, so Invent (Forge and Quest) or Make
(Spark) only confirms the pinned specialist instead of choosing one.

`inventor.json` contains only the stable id, status, source, and sorted
content-bound skill records. It does not decide what a person may Wish for or
which kinds of product the Inventor is allowed to make. Without a pinned
Inventor, the first active creative stage (Invent for Forge and Quest, Make for
Spark) compares the exact Wish with the full Taste and method of every
eligible Inventor and seals its selection together with that stage's
contract. There is no separate Match turn; the standalone Match stage exists
only for frozen older runs.

For each product run, the host validates these source bundles and
deterministically projects them into official project-scoped
`.codex/agents/<id>.toml` custom agents. `.codex/agents/*.toml` is the sole
Inventor identity, Taste, and skill roster inside that toy project; there is no
second run-local identity tree. One persistent native Codex session acts as
Workshop Manager and uses Codex's own subagent controls to spawn the selected
Inventor.

Each Invent, Make, Playtest, or Release attempt has one active native
Codex Goal. The Manager and its native children observe, act, evaluate, and
improve while pursuing that Goal. Inventor scripts do not implement this loop.
They may provide bounded deterministic specialist operations such as CAD
generation, simulation, parsing, or evaluation, but they must not launch
agents, schedule prompts, choose lifecycle transitions, waive gates, access
credentials, or perform external effects.

The bundled Inventors currently use one concise instructions-only primary
skill each. Shared CAD, simulation, and evidence tooling stays in Workshop.

| Inventor | Id | Native skill |
|---|---|---|
| Abstract Boardgame Oracle | `abo` | `abo-inventor` |
| Alice | `alice` | `alice-inventor` |
| Bob | `bob` | `bob-inventor` |
| Eve | `eve` | `eve-inventor` |
| Ivy | `ivy` | `ivy-inventor` |
| Kestrel Knot | `kestrel-knot` | `kestrel-knot-inventor` |
| Leo | `leo` | `leo-inventor` |
| Luma Vale | `luma-vale` | `luma-vale-inventor` |
| Mira Fold | `mira-fold` | `mira-fold-inventor` |
| Orin Shadow | `orin-shadow` | `orin-shadow-inventor` |
| Pico Press | `pico-press` | `pico-press-inventor` |
| Sonora Reed | `sonora-reed` | `sonora-reed-inventor` |
| Soren Voss | `soren-voss` | `soren-voss-inventor` |
| Tess Loop | `tess-loop` | `tess-loop-inventor` |
| Vela Bloom | `vela-bloom` | `vela-bloom-inventor` |

`TASTE.md` begins with the bounded `name` and `description` used for Inventor
selection.
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
