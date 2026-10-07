---
name: brainstorm-trend
description: Invent an original motion toy inspired by a current Trend - shortlist Trends with dated evidence, run a contest of six personality designers through design-a-toy Stages 1-2, gate and round-robin judge their drafts, then finish the winner and hand it to `build-a-toy`. Use when the human wants a new toy from what is trending now, with or without naming the Trend.
---

# Brainstorm a toy from a Trend

This skill runs a **contest**: six designers, each a personality drawn from
[personalities.json](personalities.json), three leaning on mechanism and
three on form, invent six different toys from one Trend; a gate removes drafts that cannot go forward; blind judges compare
every pair; the winner is finished through `design-a-toy` and handed to
`build-a-toy`. The vocabulary is `CONTEXT.md`'s: **Trend**, **Trend Hook**,
**Signature Motion**, **Design Contract**, **Interface**.

Every toy is a **motion toy**: its play centres on one Signature Motion made
by a coupled Interface (a crank that flaps wings, a pull that walks legs, a
spring that pops). Board games, puzzle games and toys whose only motion is
decorative are out of scope.

Every toy is **inspired by** its Trend and owns its expression: the Trend
reaches the toy through its Trend Hook, never through the Trend owners'
names, characters, logos or trade dress.

Python here is deterministic tooling only. You, the orchestrator, do every
judgement; subagents do the designing and the judging. Run every script with
`uv run python` from the repository root, so `gate_contract.py` can import
`workshop`.

The scripts live in `.claude/skills/brainstorm-trend/scripts/`:

| Script | Does |
| --- | --- |
| `run_log.py` | `check-trends`, `rank-trends`, `start`, `append`: the run's `run.json` |
| `draw_personalities.py` | the seeded draw and its replacements |
| `generate_image.py` | one image via OpenRouter, reading `.env` |
| `gate_contract.py` | format limits, the three prose sections, a coupled Interface |
| `blind_packets.py` | the judges' A/B packets, refusing a named personality |
| `round_robin.py` | `schedule` and `score` |

Log every step as it happens with `run_log.py append`; the step names and
fields are in [schemas/run.schema.json](schemas/run.schema.json). `run.json`
never holds a credential: never read `OPENROUTER_API_KEY` yourself and never
pass it to a subagent.

## Step 1 - Choose the Trend

If the human named a Trend, it is `given`: take it as stated and go to the
next paragraph. Otherwise research one shortlist of exactly five Trends with
`WebSearch`, each a `{name, keyword, summary, sources}` with every source's
`url` and `published` date (YYYY-MM-DD). The `keyword` is the narrow search
term Google Trends measures the Trend by: the event's own name ("iPhone Duo"),
never a broad word that also means other things ("Zelda"). A Trend is
eligible when:

- at least two sources on different sites are dated within the last 30 days;
- it carries something to be inspired by beyond its brand: a shape, a
  creature, a motion, an event, a feeling;
- it is mainstream: covered widely, beyond one niche community;
- it speaks to the Buyer and suits a toy on their desk: no politics,
  tragedy, or real living person.

Write the shortlist to the scratchpad and run `run_log.py check-trends` on
it; replace every candidate that fails until all five pass. Then rank it:

    uv run --with pytrends --with "urllib3<2" python \
      .claude/skills/brainstorm-trend/scripts/run_log.py rank-trends SHORTLIST.json

It prints the shortlist highest Google Trends interest first, each with its
`interest` (mean over the last month, 0 to 100, on one shared scale); save
that output as the shortlist. When Google blocks the lookup it warns and
leaves every `interest` null; go on without it. Show the human the five as
one line each, name, interest and why it is trending, and wait for their
pick. That pick is `human`.

Done when: the Trend is chosen.

## Step 2 - Draw the designers and start the log

Run `draw_personalities.py` with no seed. It prints the seed and six
personalities, three `mechanism` then three `form`. Give each a slot,
`candidate-1` to `candidate-6`.
Replacements in Step 4 come from this seed, never from a new draw.

Create the run directory `brainstorm-trend/<trend-slug>-<YYYY-MM-DD>/`, read
the image model with `grep '^OPENROUTER_IMAGE_MODEL=' .env` (or from the
environment), and write the header with `run_log.py start`: `trend`,
`chosen_by`, `shortlist` (the checked shortlist, or null for a given Trend),
`seed`, and `image_model`. Then log `personalities_drawn`.

## Step 3 - Six drafts in parallel

Launch six subagents in one message, one per slot, each with this brief:

- The Trend, its summary, and its sources.
- The personality's name and `method`, which decides every trade-off the
  Taste would decide in `design-a-toy`, inside `inventors/trend-lab/TASTE.md`:
  the toy is for the Buyer and meets the print floor. The contract's
  `inventor` is `trend-lab`. The personality stays out of the contract: never
  name it, its lean or the contest there, so the judges stay blind.
- Run `.claude/skills/design-a-toy/SKILL.md` Stages 1 and 2 only. Answer
  every Stage 1 question yourself, in the personality; ask the human
  nothing.
- The toy is a motion toy with one Signature Motion made by a coupled
  Interface, inspired by the Trend and owning its expression (the scope
  paragraphs above, verbatim).
- Write `CONTRACT.md` in `brainstorm-trend/<run>/<slot>/` with three prose
  sections the gate looks for:
  - `## Trend Hook`: the one countable or pointable feature that makes the
    toy read as this Trend's;
  - `## Signature Motion`: what moves, what drives it, and what the player
    does;
  - `## Palette`: one line per Unique Geometry, its id and the one filament
    colour every Component of it prints in.
- Generate one Preview Image: the assembled toy in its Display Pose, one
  subject fully inside the frame, in the Palette's colours, by writing a prompt to `<slot>/prompt.txt`
  and running `generate_image.py --prompt-file <slot>/prompt.txt --out
  <slot>/preview.png`. Report the path it prints.
- Return the contract path, the Preview Image path, and one sentence on the toy.

Log `contract_generated` for each as it returns.

## Step 4 - Gate

For each draft, run `gate_contract.py <slot>/CONTRACT.md`, then read the
contract and judge three things the script cannot:

- the Trend Hook is genuinely countable or pointable in the Preview Image;
- the Signature Motion is the toy's play, not decoration;
- the contract and Preview Image carry none of the Trend owners' names, characters,
  logos or trade dress.

A draft that fails any check is rejected. Log `gate_rejected` with every
reason and draw its replacement with `draw_personalities.py --seed <seed>
--lean <the rejected personality's lean> --replacement <K>`, K counting that
lean's replacements, so the contest keeps three of each lean. The
replacement runs Step 3's brief alone in `<slot>-r<K>/` and is gated in
turn. The contest allows five replacements in all; after the fifth, a
rejection gets `replacement_personality: null` and its slot stays empty.

Done when: every slot holds a passing draft or is empty. With one survivor,
it wins outright: go to Step 6. With none, tell the human what failed and
stop.

## Step 5 - Round robin

Write the surviving slot ids to a JSON list and run `round_robin.py schedule
--contestants <list>`; save its output as `schedule.json` in the run
directory. Build the judges' packets:

    uv run python .claude/skills/brainstorm-trend/scripts/blind_packets.py \
      --schedule <run>/schedule.json --run-dir <run> --out <run>/packets

Each `packets/match-NN/` holds the match's two drafts as A and B, in the
scheduled order: the contract's title, Trend Hook, Signature Motion and
Palette, and its Preview Image. The script refuses, writing nothing, when a
draft names its personality; send that designer back to reword the named
section, gate the draft again, and rebuild.

For every match, launch a **fresh** judge subagent on Sonnet (`model:
sonnet`), so no judge sees two matches; judges of independent matches may
run in parallel. Give each judge only its packet directory and the Buyer:
the tech and office workers who visit autonomous.ai, buying a toy for their
desk. It judges on three criteria:

- **originality**: how unlike existing toys it is;
- **beauty**: how good it looks on a desk and in the hand;
- **motion**: how satisfying the Signature Motion is to play with, again and
  again.

It answers `a`, `b`, or `split` when it cannot separate them, with one
sentence why. The Trend Hook is pass/fail at the gate and is never scored.

Log each `judgment`: `pair` is the two slots in the order the schedule first
shows them, `ordering` is `ab` for that match and `ba` for its swap, and
`winner` is the winning slot or null for a split. Collect the verdicts as
`{"<match index>": "a" | "b" | "split"}`, run `round_robin.py score
--schedule schedule.json --verdicts <verdicts>`, and log `standings` as
`{agent_id, points}` rows.

## Step 6 - Winner

The highest points wins; `score` already breaks ties by head-to-head. If it
reports an unresolved tie, choose between the tied drafts yourself and log
`tie_break` with why. Log `winner`.

## Step 7 - Finish and hand off

Continue the winning draft through `design-a-toy` Stage 3 to Stage 5, in its
directory, with the winning personality still deciding trade-offs and
`inventor: trend-lab`. The Preview Image may become the assembly reference
only if it passes Stage 3b. Stage 4 is the human's one approval gate: wait for it,
then log `human_approval`. Stage 5 hands the `CONTRACT.md` to `build-a-toy`.

Done when: the human approved the images, `run.json` holds every step from
the header to `human_approval`, and `build-a-toy` has the contract path.
