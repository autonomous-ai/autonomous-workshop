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
| `run_log.py` | `check-trends`, `start`, `append`: the run's `run.json` |
| `draw_personalities.py` | the seeded draw and its replacements |
| `generate_image.py` | one image via OpenRouter, reading `.env` |
| `gate_contract.py` | format limits, both prose sections, a coupled Interface |
| `round_robin.py` | `schedule` and `score` |

Log every step as it happens with `run_log.py append`; the step names and
fields are in [schemas/run.schema.json](schemas/run.schema.json). `run.json`
never holds a credential: never read `OPENROUTER_API_KEY` yourself and never
pass it to a subagent.

## Step 1 - Choose the Trend

If the human named a Trend, it is `given`: take it as stated and go to the
next paragraph. Otherwise research one shortlist of five Trends with
`WebSearch`, each a `{name, summary, sources}` with every source's `url` and
`published` date (YYYY-MM-DD). A Trend is eligible when:

- at least two sources on different sites are dated within the last 30 days;
- it carries something to be inspired by beyond its brand: a shape, a
  creature, a motion, an event, a feeling;
- it is suitable for a children's toy: no politics, tragedy, real living
  person, or adult-only subject.

Write the shortlist to the scratchpad and run `run_log.py check-trends` on
it; replace every candidate that fails until all five pass. Show the human
the five as one line each, name and why it is trending, and wait for their
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
  Taste would decide in `design-a-toy`. There is no Inventor Taste; the
  contract's `inventor` is `trend-lab`.
- Run `.claude/skills/design-a-toy/SKILL.md` Stages 1 and 2 only. Answer
  every Stage 1 question yourself, in the personality; ask the human
  nothing.
- The toy is a motion toy with one Signature Motion made by a coupled
  Interface, inspired by the Trend and owning its expression (the scope
  paragraphs above, verbatim).
- Write `CONTRACT.md` in `brainstorm-trend/<run>/<slot>/` with two prose
  sections the gate looks for: `## Trend Hook`, the one countable or
  pointable feature that makes the toy read as this Trend's, and
  `## Signature Motion`, what moves, what drives it, and what the child does.
- Generate one hero image: the assembled toy in its Display Pose, one
  subject fully inside the frame, by writing a prompt to `<slot>/prompt.txt`
  and running `generate_image.py --prompt-file <slot>/prompt.txt --out
  <slot>/hero.png`. Report the path it prints.
- Return the contract path, the hero path, and one sentence on the toy.

Log `contract_generated` for each as it returns.

## Step 4 - Gate

For each draft, run `gate_contract.py <slot>/CONTRACT.md`, then read the
contract and judge three things the script cannot:

- the Trend Hook is genuinely countable or pointable in the hero image;
- the Signature Motion is the toy's play, not decoration;
- the contract and hero carry none of the Trend owners' names, characters,
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
directory. For every match, launch a **fresh** judge subagent, so no judge sees two
matches; judges of independent matches may run in parallel. Each judge gets
the match's two drafts as A and B, in the scheduled order, with each
contract's prose and hero image, and nothing about the personalities or the
other drafts. It judges on three criteria:

- **originality**: how unlike existing toys it is;
- **beauty**: how good it looks on a shelf and in the hand;
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
`inventor: trend-lab`. The hero image may become the assembly reference if
it passes Stage 3b. Stage 4 is the human's one approval gate: wait for it,
then log `human_approval`. Stage 5 hands the `CONTRACT.md` to `build-a-toy`.

Done when: the human approved the images, `run.json` holds every step from
the header to `human_approval`, and `build-a-toy` has the contract path.
