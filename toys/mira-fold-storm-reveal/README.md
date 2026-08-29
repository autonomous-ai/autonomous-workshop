# Storm Reveal

![Storm Reveal](make/product/cad/review/closed-top.png)

A pocket-size three-piece sleepy cloud puzzle whose single guided quarter-turn reveals a standing rainbow-and-lightning storm scene, then reverses to reset.

[View the verified public product page](https://www.autonomous.ai/factory/product/storm-reveal)

| Frozen on this run | Value |
|---|---|
| Manager | Codex (`--manager codex`) |
| Effort | Spark (`--effort spark`) |
| Inventor | [Mira Fold](../../inventors/mira-fold/) |
| Factory | https://www.autonomous.ai/factory/product/storm-reveal |

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Mira Fold) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## Run cost

| Measure | Value |
|---|---|
| Native Manager tokens | 44,802,977 (measured; 6/6 turns measured) |
| Wish to verified publication | 1h 34m 10s (2026-08-29T02:11:01Z to 2026-08-29T03:45:11.966018+00:00) |

| Stage | Tokens | Turns | Coverage |
|---|---:|---:|---|
| Match | 0 | 0 | folded |
| Invent | 0 | 0 | skipped |
| Make | 41,265,645 | 5 | measured |
| Playtest | 0 | 0 | not-run |
| Release | 3,537,332 | 1 | measured |

Tokens are best-effort input-plus-output counts reported by the native Manager;
no dollar cost is inferred. Elapsed time ends only after authenticated Factory
public readback.

## Reproduce

From a checkout of this repository, verify the host and run the same Manager and effort route. This command uses the public product summary; a later run follows the same route but does not replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --manager codex --effort spark --github 'A pocket-size three-piece sleepy cloud puzzle whose single guided quarter-turn reveals a standing rainbow-and-lightning storm scene, then reverses to reset.'
```

If a native turn stops before Release, continue the same Wish with `uv run workshop resume <wish-id>`.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- Invent was skipped by this effort route; its sealed compact concept is under `make/`.
- `make/` — the exact sealed Release facts, exact CAD source, models, product renders, verification, and sealed prior attempts.
- `release/MANUAL.pdf` — the exact sealed printable in-box manual.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `TOKENS.json` — Manager-reported total tokens by stage; no dollar estimate.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
