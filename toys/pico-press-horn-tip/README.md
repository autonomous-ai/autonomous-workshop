# Horn Tip

A tiny one-piece crescent desk rocker. Press a rounded horn with a fingertip and it tips, then gravity walks it back to rest on its outer curve.

[View the verified public product page](https://www.autonomous.ai/factory/product/horn-tip)

This snapshot is a Spark effort (`Wish -> Make -> Release`) produced by the
experimental Grok Build Manager. Pico Press was selected during Make. Playtest
was not run; Release records that omission explicitly.

| Frozen on this run | Value |
|---|---|
| Manager | Grok Build (`--manager grok`) |
| Native CLI | `grok` 1.0.5 (`5115b46bc909`) |
| Model | `grok-4.6` |
| Effort | Spark (`--effort spark`) |
| Inventor | Pico Press |
| Factory | https://www.autonomous.ai/factory/product/horn-tip |

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Pico Press) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## Reproduce

Install Grok Build TUI `grok` 1.0.5 or newer, sign in, and run the same
Workshop command from a checkout of this repository:

```bash
grok login
grok --version

uv run workshop doctor
uv run workshop wish --manager grok --effort spark \
  "I wish for a tiny one-piece crescent desk rocker that tips with a fingertip"
```

If the first native turn stops before Release, continue the same Wish with
`uv run workshop resume <wish-id>`. A later run of this Wish is the same
Manager and Spark route, not a replay of these exact CAD bytes.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- Invent was skipped by this effort route; its sealed compact concept is under `make/`.
- `make/` — the exact sealed Release facts, exact CAD source, models, and verification.
- `release/MANUAL.pdf` — the exact sealed printable in-box manual.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
