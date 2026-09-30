# Antisol Caelus Companion

![Antisol Caelus Companion](make/verification/renders/iso.png)

Jungle Chess played with the solar system. Every piece is a planet, and a planet's size on the board is the fifth root of its real measured diameter, so rank is something you can see rather than learn: Mercury is the smallest world in play and Jupiter the largest, and the traditional rules are followed exactly as written. Matter faces antimatter. One army's worlds lean their poles one way and the other army's lean the other, by each planet's own true axial tilt, and the bases say it again in white against black. Four of the eight wear a real map -- Earth its coastlines, Mars its dark continents, Mercury its smooth plains with the Caloris basin in them, and Venus the radar surface no eye has seen. Three more wear their weather. One wears nothing at all: Uranus is a bare cyan sphere under a white hoop. This edition adds one small thing to Neptune, and nothing else. Neptune's Great Dark Spot has its bright companion cloud back: one small white oval, 10 by 5 degrees of arc, sitting just south of the dark spot, on both Neptune pieces. The owner asked for it about 8 degrees south of the spot's centre at the same longitude. At 8 it would overlap the spot's own rim, and directly under the spot's centre the lean of one army's piece would tuck part of it under the collar the globe stands on, so it sits 11.5 degrees south and 10 degrees toward the spot's western end -- still under the spot, fully visible on both pieces, with a strip of bare blue between them wider than the printer's nozzle. It prints in the same white spool as Neptune's three cloud bands. The dark spot, the three bands, the globe, the base and every other piece in the box are unchanged, and every printed part's solid is the same shape it was in the last edition.

**Not published.** This run was sealed locally with `--no-publish`: no Factory listing, no public product page, and no external effect of any kind was created.

| Frozen on this run | Value |
|---|---|
| Agent | Claude Code (`--agent claude`) |
| Workflow | Spark (`--workflow spark`) |
| Model | claude-opus-5-5 (`--model claude-opus-5-5`) |
| Effort | Medium (`--effort medium`) |
| Inventor | [Ad Astra](../../inventors/ad-astra/) |
| Factory | not published (`--no-publish`) |

## Workflow

Spark: `Wish -> Make -> Release`. The accepted Inventor assignment is preserved under `match/`. Release is host-owned publication of Make output, with no native Release turn or new manual.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Ad Astra) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | host | accepted |
| Publication | host | unreleased |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

### 1. Wish — freeze the request

**Input:** the creator's request. **This toy's input:** Jungle Chess played with the solar system. Every piece is a planet, and a planet's size on the board is the fifth root of its real measured diameter, so rank is something you can see rather than learn: Mercury is the smallest world in play and Jupiter the largest, and the traditional rules are followed exactly as written. Matter faces antimatter. One army's worlds lean their poles one way and the other army's lean the other, by each planet's own true axial tilt, and the bases say it again in white against black. Four of the eight wear a real map -- Earth its coastlines, Mars its dark continents, Mercury its smooth plains with the Caloris basin in them, and Venus the radar surface no eye has seen. Three more wear their weather. One wears nothing at all: Uranus is a bare cyan sphere under a white hoop. This edition adds one small thing to Neptune, and nothing else. Neptune's Great Dark Spot has its bright companion cloud back: one small white oval, 10 by 5 degrees of arc, sitting just south of the dark spot, on both Neptune pieces. The owner asked for it about 8 degrees south of the spot's centre at the same longitude. At 8 it would overlap the spot's own rim, and directly under the spot's centre the lean of one army's piece would tuck part of it under the collar the globe stands on, so it sits 11.5 degrees south and 10 degrees toward the spot's western end -- still under the spot, fully visible on both pieces, with a strip of bare blue between them wider than the printer's nozzle. It prints in the same white spool as Neptune's three cloud bands. The dark spot, the three bands, the globe, the base and every other piece in the box are unchanged, and every printed part's solid is the same shape it was in the last edition.

**Output:** an immutable, hash-bound Wish plus its frozen effort route. The exact wording is withheld; this is the sanitized public summary in [the Wish binding](wish/wish.json).

### 2. Invent — choose an Inventor and define the concept

**Input:** the frozen Wish, eligible Inventor roster with each bound Taste/skill bundle, and the product blueprint. **Output:** **Ad Astra** was selected and produced **Antisol Caelus Companion** — Jungle Chess played with the solar system. Every piece is a planet, and a planet's size on the board is the fifth root of its real measured diameter, so rank is something you can see rather than learn: Mercury is the smallest world in play and Jupiter the largest, and the traditional rules are followed exactly as written. Matter faces antimatter. One army's worlds lean their poles one way and the other army's lean the other, by each planet's own true axial tilt, and the bases say it again in white against black. Four of the eight wear a real map -- Earth its coastlines, Mars its dark continents, Mercury its smooth plains with the Caloris basin in them, and Venus the radar surface no eye has seen. Three more wear their weather. One wears nothing at all: Uranus is a bare cyan sphere under a white hoop. This edition adds one small thing to Neptune, and nothing else. Neptune's Great Dark Spot has its bright companion cloud back: one small white oval, 10 by 5 degrees of arc, sitting just south of the dark spot, on both Neptune pieces. The owner asked for it about 8 degrees south of the spot's centre at the same longitude. At 8 it would overlap the spot's own rim, and directly under the spot's centre the lean of one army's piece would tuck part of it under the collar the globe stands on, so it sits 11.5 degrees south and 10 degrees toward the spot's western end -- still under the spot, fully visible on both pieces, with a strip of bare blue between them wider than the printer's nozzle. It prints in the same white spool as Neptune's three cloud bands. The dark spot, the three bands, the globe, the base and every other piece in the box are unchanged, and every printed part's solid is the same shape it was in the last edition. **Concept parts:** Board panel southwest, Board panel southeast, Board panel northwest, Board panel northeast, Asteroid belt tile, Sol star, Sol prominences, Anti-Sol star, Anti-Sol prominences, Sol corona cell, Anti-Sol corona cell, Orbit tray, Orbit tray, Sol disc, Sol rank numeral, Anti-Sol disc, Anti-Sol rank numeral, Mercury globe, Mercury smooth plains, Mercury Caloris rim, Mercury Caloris floor, Mars globe, Mars albedo, Mars north cap, Venus globe, Venus highlands, Earth globe, Earth land, Earth dryland, Earth ice, Neptune globe, Neptune spot, Neptune bands, Neptune companion cloud, Uranus globe, Uranus ring, Saturn globe, Saturn light bands, Saturn dark band, Saturn north cap, Saturn ring, Jupiter globe, Jupiter belts, Jupiter spot, Jupiter zones, Jupiter spot collar, Venus lowland plains. The complete compact concept is in [make/invented.json](make/invented.json). Spark has no separate Invent Goal; the accepted Inventor assignment and compact Make concept are preserved separately.

### 3. Make — turn the concept into exact product bytes

**Input:** the accepted concept, selected Inventor identity/Taste, blueprint, and any bounded revision evidence. **Output:** Jungle Chess played with the solar system. Every piece is a planet, and a planet's size on the board is the fifth root of its real measured diameter, so rank is something you can see rather than learn: Mercury is the smallest world in play and Jupiter the largest, and the traditional rules are followed exactly as written. Matter faces antimatter. One army's worlds lean their poles one way and the other army's lean the other, by each planet's own true axial tilt, and the bases say it again in white against black. Four of the eight wear a real map -- Earth its coastlines, Mars its dark continents, Mercury its smooth plains with the Caloris basin in them, and Venus the radar surface no eye has seen. Three more wear their weather. One wears nothing at all: Uranus is a bare cyan sphere under a white hoop. This edition adds one small thing to Neptune, and nothing else. Neptune's Great Dark Spot has its bright companion cloud back: one small white oval, 10 by 5 degrees of arc, sitting just south of the dark spot, on both Neptune pieces. The owner asked for it about 8 degrees south of the spot's centre at the same longitude. At 8 it would overlap the spot's own rim, and directly under the spot's centre the lean of one army's piece would tuck part of it under the collar the globe stands on, so it sits 11.5 degrees south and 10 degrees toward the spot's western end -- still under the spot, fully visible on both pieces, with a strip of bare blue between them wider than the printer's nozzle. It prints in the same white spool as Neptune's three cloud bands. The dark spot, the three bands, the globe, the base and every other piece in the box are unchanged, and every printed part's solid is the same shape it was in the last edition. The sealed snapshot contains 26 STEP and 42 product render PNGs, together with [CAD source](make/source/), [models](make/models/), and [deterministic verification](make/verification/). [The Made contract](make/made.json) binds those exact bytes.

### 4. Playtest — challenge the made product

**Input:** the sealed Made product, blueprint-required checks, and exact evidence. **Output:** not run on this effort route; Release preserves the explicit [omission record](release/PLAYTEST-NOT-RUN.json).

### 5. Release — make the customer package

**Input:** the sealed product and the passed Playtest evidence or truthful not-run record. **Output:** the existing Make files and hash-bound publication metadata, with no new manual, PDF, review, or native Release turn; [the existing README](release/README.md) was reused from Make; see [the Release contract](release/release.json).

### 6. Publication — not performed

**Input:** the exact sealed Release package. **Output:** none. This run was sealed locally with `--no-publish`, so no Factory effect was created, no listing exists, and [the publication record](publication/PUBLICATION.json) says `unreleased`.

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | 10,254,642 (partial; 1/4 turns measured) |
| Native Manager cached input tokens | 10,221,826 (partial; 1/4 turns measured) |
| Native Manager uncached input tokens | 32,816 (partial; 1/4 turns measured) |
| Native Manager cache-write input tokens | 32,764 (partial; 1/4 turns measured) |
| Native Manager output tokens | 15,521 (partial; 1/4 turns measured) |
| Native Manager reasoning output tokens | 3,023 (partial; 1/4 turns measured) |
| Wish to verified publication | 3h 46m 59s (2026-09-26T04:02:06Z to 2026-09-26T07:49:05+00:00) |

| Stage | Input tokens | Cached input | Uncached input | Output tokens | Turns | Coverage |
|---|---:|---:|---:|---:|---:|---|
| Match | 0 | 0 | 0 | 0 | 0 | folded; economics folded |
| Invent | 0 | 0 | 0 | 0 | 0 | skipped; economics skipped |
| Make | 10,254,642 | 10,221,826 | 32,816 | 15,521 | 4 | partial; economics partial |
| Playtest | 0 | 0 | 0 | 0 | 0 | not-run; economics not-run |
| Release | 0 | 0 | 0 | 0 | 0 | pending; economics pending |

Input and output tokens are best-effort separate counts reported by the native Manager; they are not added together. Cached plus uncached input equals the input covered by the economic breakdown, while cache writes and reasoning are reported as subsets rather than added again. No dollar cost is inferred. Elapsed time ends only after authenticated Factory public readback.

## Reproduce

From a checkout of this repository, verify the host and run the same agent and workflow. This command uses the public product summary; a later run follows the same route but does not replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --agent claude --model claude-opus-5-5 --effort medium --workflow spark 'Jungle Chess played with the solar system. Every piece is a planet, and a planet'"'"'s size on the board is the fifth root of its real measured diameter, so rank is something you can see rather than learn: Mercury is the smallest world in play and Jupiter the largest, and the traditional rules are followed exactly as written. Matter faces antimatter. One army'"'"'s worlds lean their poles one way and the other army'"'"'s lean the other, by each planet'"'"'s own true axial tilt, and the bases say it again in white against black. Four of the eight wear a real map -- Earth its coastlines, Mars its dark continents, Mercury its smooth plains with the Caloris basin in them, and Venus the radar surface no eye has seen. Three more wear their weather. One wears nothing at all: Uranus is a bare cyan sphere under a white hoop. This edition adds one small thing to Neptune, and nothing else. Neptune'"'"'s Great Dark Spot has its bright companion cloud back: one small white oval, 10 by 5 degrees of arc, sitting just south of the dark spot, on both Neptune pieces. The owner asked for it about 8 degrees south of the spot'"'"'s centre at the same longitude. At 8 it would overlap the spot'"'"'s own rim, and directly under the spot'"'"'s centre the lean of one army'"'"'s piece would tuck part of it under the collar the globe stands on, so it sits 11.5 degrees south and 10 degrees toward the spot'"'"'s western end -- still under the spot, fully visible on both pieces, with a strip of bare blue between them wider than the printer'"'"'s nozzle. It prints in the same white spool as Neptune'"'"'s three cloud bands. The dark spot, the three bands, the globe, the base and every other piece in the box are unchanged, and every printed part'"'"'s solid is the same shape it was in the last edition.'
```

If a native turn stops before Release, continue the same Wish with `uv run workshop resume <wish-id>`.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- Invent was skipped by this effort route; its sealed compact concept is under `make/`.
- `make/` — the exact sealed Release facts, exact CAD source, models, product renders, verification, and sealed prior attempts.
- `release/README.md` — the existing Make README, reused without rewriting.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — local `unreleased` record; no readback identities, because nothing was published.
- `TOKENS.json` — separate Manager-reported gross/cached/uncached input and output/reasoning tokens by stage; no combined total or dollar estimate.
- `TIMING.json` — Wish intake to locally sealed Release elapsed time, plus a per-stage timing breakdown.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- `SANITIZATION.json` — source/public hashes for host-local path prefixes replaced by stable placeholders.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
