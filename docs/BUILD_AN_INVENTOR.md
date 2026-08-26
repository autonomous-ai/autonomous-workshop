# Build an inventor persona

An Autonomous Workshop inventor is a creative persona for the shared native
coding agent. It is not a Python worker, package, service, prompt chain, or
profile subprocess.

The complete contribution is deliberately small:

```text
inventors/ada/
  inventor.json
  TASTE.md
```

An optional concise `README.md` may explain the contribution to people. No
other file or directory belongs in a persona folder.

## Why the boundary is this small

One Wish creates one private run workspace and one native Codex session. That
same session performs Match, Invent, Make, Playtest, and the later Workshop
work under host-controlled checkpoints. After Match selects an inventor, the
host gives the session the selected manifest and exact Taste bytes.

Starting a second process for the inventor would split context, duplicate the
agent framework, and put cognitive orchestration back into Python. Persona
folders therefore contain only inputs. The Workshop host retains typed
contracts, deterministic gates, artifact hashing, limits, durable state, and
authorized effects.

## Create the two files

The scaffold can preserve an existing Taste exactly:

```bash
workshop create inventor ada \
  --taste ./TASTE.md \
  --lane moving-machines \
  --root .
```

Or it can create a starter Taste:

```bash
workshop create inventor ada \
  --name Ada \
  --description "Choose Ada for expressive hand-cranked creatures; not static models, games, or science demonstrations." \
  --lane moving-machines \
  --root .
```

The scaffold publishes the folder atomically only after static validation. It
does not generate or execute Python, install a package, start Codex, or run a
profile command.

## Manifest schema

New local personas use schema version 6:

```json
{
  "schema_version": 6,
  "id": "ada",
  "status": "experimental",
  "capabilities": ["moving-machines"],
  "source": {"kind": "local"}
}
```

The `id` must match the containing folder. `capabilities` contains exactly one
Workshop plaything lane:

- `classics-made-yours`
- `invented-games`
- `moving-machines`
- `holdable-science`
- `little-worlds`

`status` is one of `active`, `experimental`, `blocked`, `reference`, or
`archived`. Match considers only the routable statuses defined by Workshop.

Schema version 6 forbids `entrypoint`, `checks`, identity prose, autonomy
policy, and implementation inventories. Versions 1 through 5 remain readable
only so old catalogs can be diagnosed during migration; new local
contributions must use version 6.

An imported upstream snapshot additionally pins its credential-free HTTPS
repository URL, full lowercase commit SHA, and import date in `source`. A
floating branch or URL containing credentials, a query, or a fragment is not
accepted.

## Write Taste

`TASTE.md` is the human-owned creative constitution. Begin with bounded YAML
frontmatter:

```yaml
---
name: Ada
description: Choose Ada for expressive hand-cranked creatures; not static models, games, or science demonstrations.
---
```

The header is intentionally small. Match can compare the name and selection
boundary without loading every complete Taste. When a persona reaches the
finalist shortlist, Workshop loads the entire exact UTF-8 file and binds its
hash to the run.

The description should say both what should choose this inventor and the
nearest work it should reject. Avoid slogans that could match every Wish.

The body should define:

- the persona's north star and chosen lane;
- the grown-up audience and play context;
- three recognizable qualities;
- forms, themes, mechanics, and shortcuts it rejects;
- the signature interaction or first delightful moment;
- how the Wish must materially change the product;
- its standards for clarity, safety, printability, assembly, and durability;
- what verified evidence could justify a proposed Taste revision.

Taste is direction, not proof. It cannot pass a deterministic gate, replace
simulation or CAD evidence, claim a physical print, or stand in for customer
feedback. The native agent may propose a revision, but it cannot silently edit
the persona to excuse the current product.

## Put tools in the owning stage

Do not add `profile.py`, `run.py`, `src/`, `tests/`, `config/`, `ops/`,
`contracts/`, `skills/`, or `toys/` beneath an inventor.

If a persona exposes a real reusable need, implement it once in the Workshop
component that owns the deterministic behavior:

- Invent contracts and validators under `src/workshop/invent/`;
- Make tools and domain skills under `src/workshop/make/`;
- Playtest simulators and gates under `src/workshop/playtest/`;
- host adapters and effect boundaries under their shared runtime or integration
  component.

The native session decides when and how to use those shared tools. Python may
validate an exact proposal, run a seeded simulator, inspect or generate CAD,
seal bytes, or perform an authorized host effect. It does not own persona
reasoning, research strategy, candidate generation, model judging, reward
loops, or repair thought.

Product artifacts belong to the private per-Wish workspace. Do not check toy
outputs, traces, renders, CAD, credentials, runtime databases, or customer data
into the inventor catalog.

## Validate a contribution

From the repository root:

```bash
workshop check inventors/ada
workshop inventors --root inventors
python -m unittest tests.contributors.test_manifest \
  tests.contributors.test_contribution \
  tests.contributors.test_scaffold \
  tests.contributors.test_taste_and_skills
git diff --check
```

Contribution validation is static. It verifies the manifest, exact folder
shape, regular non-symlink files, bounded Taste header and bytes, provenance,
and optional README size. It never imports or executes inventor-controlled
code.

Tests for the shared native runtime, deterministic tools, gates, and effects
remain in the matching top-level `tests/<component>/` folder. They are tests of
Workshop behavior, not files carried by a persona.
