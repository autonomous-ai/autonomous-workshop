# Horn Tip

![Horn Tip](../../docs/images/horn-tip.jpg)

A tiny one-piece crescent desk rocker. Press a rounded horn with a fingertip and it tips, then gravity walks it back to rest on its outer curve.

[View the verified public product page](https://www.autonomous.ai/factory/product/horn-tip)

This snapshot is a Spark effort (`Wish -> Make -> Release`) produced by the
experimental Grok Build Manager. [Pico Press](../../inventors/pico-press/) was
selected during Make. Playtest was not run; Release records that omission
explicitly.

| Frozen on this run | Value |
|---|---|
| Manager | Grok Build (`--manager grok`) |
| Native CLI | `grok` 1.0.5 (`5115b46bc909`) |
| Model | `grok-4.6` |
| Effort | Spark (`--effort spark`) |
| Inventor | [Pico Press](../../inventors/pico-press/) |
| Factory | https://www.autonomous.ai/factory/product/horn-tip |

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted ([Pico Press](../../inventors/pico-press/)) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

1. **Wish.** Input: “I wish for a tiny one-piece crescent desk rocker that tips with a fingertip.” Output: the immutable, exact [Wish binding](wish/wish.json).
2. **Invent.** Input: that Wish, the eligible Inventor roster, Taste, and blueprint. Output: Pico Press was selected and defined *Horn Tip*: one crescent rocker whose rounded horn accepts the press and whose outer curve lets gravity walk it back to rest. Spark folded this one-part compact concept into Make; see [the concept](make/invented.json).
3. **Make.** Input: the accepted concept and Pico Press's bound craft context. Output: the sealed one-piece rocker, with 1 STEP, 2 STL, 1 GLB, no archived render PNG, exact [CAD source](make/source/), [models](make/models/), and [verification](make/verification/), all bound by [made.json](make/made.json). This historical run is exactly why current Make now requires and archives a standardized product render.
4. **Playtest.** Input: the sealed Made product. Output: not run on the Spark route, recorded explicitly in [PLAYTEST-NOT-RUN.json](release/PLAYTEST-NOT-RUN.json).
5. **Release.** Input: the sealed product plus the truthful Playtest omission. Output: the hash-bound package and printable [customer manual](release/MANUAL.pdf), bound by [release.json](release/release.json).
6. **Publication.** Input: the exact Release package plus host-held Factory authorization. Output: the verified [Factory product](https://www.autonomous.ai/factory/product/horn-tip) and sanitized [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager tokens | unavailable — this run predates token telemetry |
| Wish to verified publication | unavailable — the archived snapshot has no trustworthy Wish-start timestamp |

No dollar cost is inferred.

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
