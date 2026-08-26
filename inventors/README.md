# Inventor personas

Each immediate subfolder is one native-agent persona and contains exactly:

```text
inventors/<id>/
  inventor.json  bounded catalog identity and one plaything lane
  TASTE.md       exact human-owned creative constitution
```

An optional concise `README.md` is accepted for contributor explanation, but
the bundled catalog does not need one. Inventor folders contain no Python
entrypoint, profile subprocess, prompt loop, tests, configuration, credentials,
runtime state, or generated toys. One product run uses the shared native Codex
session; the selected persona supplies Taste, not a second agent framework.

| Inventor | Lane |
|---|---|
| Alice | classics made yours |
| Bob | moving machines |
| Eve | little worlds |
| Ivy | holdable science |
| Leo | invented games |

`TASTE.md` begins with the bounded `name` and `description` used for Match.
The complete exact file is materialized into a private product-run workspace
only after the persona becomes a finalist. Verified outcomes may justify a
proposed Taste revision, but only a human changes the catalog bytes.

Create a persona from the repository root:

```bash
workshop create inventor pocket-orreries \
  --name Ada \
  --description "Choose Ada for personalized orbit models; not games or decor." \
  --lane holdable-science \
  --root .
```

Reusable deterministic tools belong to the stage that owns them under
`src/workshop/`; product artifacts belong to the private run workspace and are
never checked into this catalog.
