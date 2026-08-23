# text2game

> **Monorepo snapshot.** This folder contains the inventor code imported from
> `nohope88/text2game` at commit `9b007f6`. It is a human-checkpointed creation
> pipeline, not yet a Workshop-connected unattended inventor: several upstream
> failure/unknown paths continue by design. See [UPSTREAM.md](UPSTREAM.md) for
> provenance, licensing, and migration blockers. The original operating guide
> follows.

[`TASTE.md`](TASTE.md) is the root creative contract and points to the detailed
board-game taste used by DISCOVER and BRIEF.

Invents a board game nobody sells, writes its rules, models every piece, and
hands you plates to print. Every component is FDM printed — no cards, no
cardboard, no app.

## How it works

```
IN   today's trend digests  (HN morning + X scrape, from the brain)

     DISCOVER    3 lanes propose · 3 judges score · Python picks
        │        a judge who finds it for sale kills it
        │        the lane that keeps winning pays for it
        ▼
     PHASE 1     rules
        │        ──▶ gdd.md            every rule carries a number
        │        ──▶ components.json   the printable contract
        ▼
     ═══ you read them and approve ═══
        │
        ▼
     PHASE 2     geometry, one todo.md group at a time
        │        ──▶ fe_parts/*.stl    measured against the contract
        ▼
     PHASE 3     print
                 ──▶ *.gcode           plates, ready for the printer
                 ──▶ rulebook.md       changes no rule, no number
                 ──▶ howto_game.mp4    beats derived from the turn order
                 ──▶ print_kit.md      + everything the checks waived

OUT  a box you can print, and an honest list of what to watch for
     when four people finally sit down with it
```

One product per run. It stops at the checkpoint on purpose: a wrong rule costs
minutes here and a day of printing later.

Built on `text2cad` — same headless `claude -p` phase runner, same run.json
accounting.

## Why it is shaped this way

The rules half is a plain agentic build loop — write the game design
document, decompose it into TODO phases with exit criteria, loop. The
specialist split (mechanism → GDD → components → details → critic) follows
**GameGrammar**, which showed six narrow agents beating one broad one, and
which is also text2cad's own lesson from commit `eb5aec1`: an agent scoring its
own output rationalises instead of reviewing.

Where the two disagree, GameGrammar wins: it is right that *"no algorithm can
simulate the experience of four people around a table."* So the **referee here
never claims to playtest**. It is a rules *executor* hunting for states the
document cannot resolve — contradictions, dead states, turns that cannot legally
end. Whether the game is fun is decided upstream by the DISCOVER panel's
`desire` axis and by `taste_boardgame.md`.

The one thing GameGrammar has no equivalent of is `components.json`. It outputs
"48 celestial object tiles"; we have to output something a printer can make, so
every component carries a physical duty, a tolerance, a bounding box and its
mating partners.

## DISCOVER

```
3 PROPOSE lanes in parallel, blind to each other
(ONE GENRE since 2026-08-21: physical play, chosen for demonstrability -
 every rule must read in one camera shot; old coop/legacy/family lanes
 are in git history):
   aim     AIM & LAUNCH - the shot must CHANGE the next player's problem
   stack   STACK & BALANCE - placement is a DECISION, gravity is the referee
   time    RELEASE & RACE - commit, release, steer between releases
        -> 2 candidates each -> cand_<lane>.md
        each carries a NAME, a BOX-FACE line and a FIRST-LOOK object
3 JUDGE agents, each scoring EVERY candidate blind
        6 axes: novelty | desire | buildable | craft | teach | resonance
        + a required WebSearch -> EXISTS <slug> yes <url> | no none
pick_winner()  PLAIN PYTHON over medians
        one real listing URL kills a candidate whatever it scored
        objective = desire + buildable + craft + teach + resonance
                    - the lane penalty
        floors    = novelty, buildable, craft, and teach which never relaxes
        all dead -> re-propose ONCE with the listings as blacklist, then abort
```

`desire` is scored on the NAME, the BOX-FACE and the FIRST-LOOK and on nothing
else. A pitch is a sentence the proposer wrote about their own idea; those three
are what a stranger actually receives, and the difference between the two is the
whole reason this axis kept rewarding games nobody would pick up in a shop.

`resonance` asks whether the trend was READ or merely touched. Every candidate
cites a seed, `audit_seeds()` counts which digest files were cited, and until
2026-08-20 nothing ever asked whether the reading was right — `overcommit` was
seeded from *"Linux 7.3 improves performance when running out of vRAM"* and sold
to an adult in Munich choosing a Friday night.

### The shelf

`catalog.json` is the only thing in DISCOVER that remembers yesterday. A panel
judges one shortlist in isolation and cannot see what it has been doing all
week: the first four games this pipeline picked were all `legacy`, and inside a
single panel five of six candidates opened with a blind draw. So the shelf is
measured in Python. Each consecutive previous pick from the same lane costs
`LANE_PENALTY` (2) off the objective, capped at `LANE_PENALTY_CAP` (2) repeats —
a lane can still win twice running, it just has to be better — and the proposers
are handed the catalogue as territory that is already taken.

Migrated out of text2cad on 2026-08-19, where it had been living as 260
uncommitted lines in a dirty working tree - one `git checkout` from gone.
text2cad went back to its 3D-print lanes.

Run `./discover.py`; it seeds `out/<slug>/{discover.md,seed.md}` and prints the
phase 1 command.

### Concept video (2026-08-22)

After the winner is seeded, `concept_video.py` renders a **12-second clip of
the game being played** (MiniMax-H3 t2va on the self-hosted 2x4090 gateway —
facts and failure modes in `/root/docs/minimax-h3-gateway.md`), caches it as
`out/<slug>/concept_video.mp4`, publishes it to `/root/shared-reports/` and
sends it to Telegram. **The human gates phase 1 on it**: watch the concept
move before spending a build on it. The prompt is a deterministic template
over the winner block (no LLM); never fatal to the panel; skip-if-exists like
every phase; kill switch `CONCEPT_VIDEO=off`; hand-run
`./concept_video.py out/<slug> [--force|--dry-run]`.

## Phase 1

```
1.0 mechanism   -> mechanisms.json   2-4 ids from mechanisms.md, zero COLLIDE pairs
1.1 gdd         -> gdd.md            the panel's NAME, then fixed sections,
                                     every rule numbered
1.2 manifest    -> components.json   the printable contract, and exactly one
                                     part flagged `"signature": true`
1.3 todo        -> todo.md           build order by mate-dependency
1.4 loop  (K rounds, default 3)
      consistency.py  machine checks, no LLM
      referee         plays N games (default 3) move by move
      critic          severity-rated balance issues + fixes, each
                      naming a `symptom` id, and reading what every
                      PREVIOUS design already broke on
      revise          applies the fixes, logs what it refused to change
1.5 priorart    -> priorart.json     WebSearch; one real listing URL kills it
==> CHECKPOINT   telegram + checkpoint.md, stop
```

Exit clean requires: zero `high` from consistency, zero `high` from the critic,
and the referee completing all N games with no findings.

## Setup on another machine

`git clone` + the owner's `.env` is the contract. **SETUP.md** is the list of
what the repo cannot carry (secrets, the text2cad sibling checkout, two CLI
logins), and `./doctor.py` checks every line of it — run it after cloning and
after dropping in `.env`; the red rows are the to-do list. `.env.example` is
the complete config contract: section A secrets, section B machine paths
(defaults = the panda VM), section C dials and models.

## Run

```bash
./discover.py                                    # panel -> a winner, seeded
./text2game --slug keep-the-light-relay          # phase 1, stops at the checkpoint
./text2game --slug keep-the-light-relay --phase 2
./text2game --slug keep-the-light-relay --phase 3
./watchdog.py logs/run.log --slug keep-the-light-relay &   # stall + death alerts
```

Phases skip when their artifact already exists; `--force` reruns them.
`--games` and `--max-rounds` override `REFEREE_GAMES` / `MAX_ROUNDS` in `.env`.

## Checks that fail a document

`consistency.py` is plain Python on purpose — an agent asked to check its own
work reports it clean. Fixtures in `tests/test_consistency.py`.

- **unbound** — a rule using *some / several / limited / enough / roughly …*
  instead of a number. This is the single check that separates a GDD from a
  wish list.
- **decoration** — a component that appears only in Setup and never in Turn
  structure, Action economy, Win/lose or Legacy. `taste_boardgame.md`: if
  removing it costs the game no decision, it was decoration.
- **signature** — not exactly one component carrying `"signature": true`. A
  shopper remembers one object, not a well-balanced set of thirteen: Monopoly's
  rules were overtaken decades ago and the little metal dog still sells it.
  `signature-idle` (medium) is the follow-up — a signature part no rule in
  `## Turn structure` touches is a mascot, and the box is being sold on
  something the game is not played with.
- **gdd-orphan / manifest-orphan** — the two documents disagree about what
  exists.
- **The lid budget (2026-08-22, after dead-stop)** — `first-minute-long` (high)
  when `## First minute` exceeds `FIRST_MINUTE_MAX_WORDS` (220), `turn-steps`
  (medium) over `TURN_MAX_STEPS` (4); `.env` ships GDD_MAX_WORDS=900 and
  GDD_MAX_RULE_NUMBERS=40. Behind it, **physics-first balance** in
  `taste_boardgame.md` and the critic/reviser prompts: for a physical game a
  rule that prices a physical choice is a smell — change the part or file
  `physics_untested` for the table; the reviser never adds a subsystem.
- **The shelf contract (2026-08-22)** — from the market read in
  `text2game-ops/findings/yt-easy-games-vs-pipeline-20260822.md`: printed
  games are judged at the shelf before the table, and the recurring market
  verdict is "where do you put the rules?". Every component now names its
  home (`stores_in`: another id or `"self"` — `homeless-part` /
  `stores-unknown`), exactly one part carries the rules (`rules_carrier` —
  engraved or a slot for the one printed rules plate), the GDD needs a
  `## First minute` section the referee cold-opens game 1 from
  (`first-minute`), and setup over `SETUP_MAX_STEPS` (6) steps is
  `setup-drag`. External parts: ONLY spec'd disc magnets and rubber bands
  (`external-banned` / `external-unspecified`) — the D1 whitelist, decided
  from the same market read. Phase 3's kit now ends with a `table_notes.md`
  template; `harvest.py` reads those bullets at `table` provenance,
  weight 4, above every generated source. `taste_boardgame.md` gained the
  **fifteen-second test** the same day: the signature part must do something
  visibly satisfying in one continuous shot, or `desire` is scored as a still life.
- **mech-collide / mech-no-legacy / mech-unknown** — the mechanism combination
  is redundant, has nothing permanent, or was invented outside the vocabulary.
- **sculpt-budget** — more than `SCULPT_MAX` parts routed to the image→TRELLIS
  branch, which runs on HF ZeroGPU at ~2-3 runs a day.
- **plate** — a footprint over 160mm.

## The evidence loop

Until 2026-08-20 this pipeline had no memory. `catalog.json` remembered a slug,
a lane and a sentence; everything else a run learned died with it. Four designs
produced 22 critic findings and 7 referee findings and nothing counted them, so
the critic started from a blank page every time and the same failures came
back: a speech restriction reached for twice to fix `alpha_solve` and rejected
by the critic both times, three designs `decided_early`, two shipping a
`duplicate_state` part that `decoration` cannot catch because the part IS named
in the rules.

```
./harvest.py     out/*/critic.json + referee.md  ->  evidence.jsonl
                 29 rows, tagged with the run's locked mechanism ids

prompts.critic() harvest.recall(chosen)          ->  the top 10, in the prompt
                 rows sharing a mechanism first, then anything that has hit
                 two or more designs, each with the fix tried and its COST
```

The vocabulary is `## SYMPTOM` in `mechanisms.md` - 22 ids, `PLAY` and
`DOCUMENT` - and `## MITIGATE` is the table that did not exist anywhere:
a fix, and **what it costs**. REINFORCE and COLLIDE say how mechanisms sit
beside each other; neither says what happens when you fix something, and the
price of a fix is the part that lives in a designer's head and never gets
written down. A row with an empty `costs` cell is not accepted.

Four rules keep this from becoming the machine agreeing with itself, which is
the failure `consistency.py` exists to prevent:

- **A design never sees its own findings.** Round 2 would otherwise be handed
  round 1's output as though another game had produced it.
- **Provenance is ranked and a critic never outranks a table.** `table` 4 >
  `referee` 3 > `critic` 2 > `reading` 1. The critic PREDICTS failures from a
  document; it does not observe them. Nothing at weight 2 should ever be read
  back as though four people had confirmed it.
- **The block is capped at 10.** A critic handed the same ten edges every run
  will find those ten things and stop looking. `--recall` prints exactly what
  the prompt will get.
- **Nothing is dropped silently.** A finding the classifier cannot place is
  written with `"symptom": null` and counted on stdout; an id the critic
  invents is named on stdout too. Both are holes in the vocabulary, not rows
  to discard. `./harvest.py --strict` exits 1 on either.

The critic now names its own `symptom`, and that beats the regex - the author
of a finding knows what it is better than a pattern does. The patterns stay for
the four runs that predate the field, and `labelled` on every row says which of
the two produced the id.

Kill switch: `CRITIC_EVIDENCE=off`.

What this does NOT do yet is close the other half of the loop. Phase 3 still
ends in a kit plus the open questions, and what four people actually find at
the table is still not recorded anywhere. That is the `table` provenance the
weights already reserve a slot for.

## Phase 2 — assets

```
2.0 art_direction  agent  -> art_direction.md   one palette, one silhouette
    concept              -> concept.png         reuses text2cad concept_image.py
2.1 scaffold.py    NO LLM -> parts/<id>.py      contract numbers become constants
2.2 build loop            per ### group of todo.md, NOT one giant session
      build-gN   cadcode, only that group's parts
      measure    scripts/measure --gaps -> fit.judge vs contract tolerances
      gate       gate.py --no-slice     -> printability, mesh only
      repair-gN  up to 2 attempts, then STOP (later groups mate with this one)
2.5 coherence      agent  -> lens_coherence.md  VERDICT: n/10, visual only
```

The visual gate is **coherence, not likeness**. text2cad compares the build to
`concept.png` because there the look IS the product; a board game is a system,
and `concept.png` was drawn by t2i from a one-line pitch before the game had
rules or a part list. Letting it block a build that satisfies the contract is
backwards. The lens scores against `art_direction.md` instead — the palette and
silhouette this pipeline derived from `gdd.md` and `components.json` — and asks
the questions a box actually has to pass: does it read as one product, can a
player tell the parts apart at a glance, did the locked palette survive.
`concept.png` stays as a one-line note that cannot outrank it.

One bounded session per group is the whole point. text2cad builds an assembly
in one 250-turn session; on 2026-08-18 that died at 5174s with *"Prompt is too
long — automatic compaction failed"*, and on 08-13 the kernel OOM-killed a
15.4GB boolean chain and took the cycle with it. Thirteen parts in one session
repeats both.

## Phase 3 — print

```
3.0 gate      text2cad gate.py, per PART       watertight/overhang/bridge/160mm
              FAIL -> stop, name the parts and the groups that built them,
                      and print the --groups command to rebuild just those
3.1 fit       fit.py: measure --gaps vs the tolerance each part DECLARED
3.2 plates    plates.py bin-pack -> plates.json
3.3 rulebook  agent -> rulebook.md             changes no rule, no number
3.4 video     storyboard.py (gdd.md ## Turn structure -> beats)
              -> agent writes howto.json -> gen_howto_video.py
              SKIPPED if no assembled render exists
3.5 kit       print_kit.md: plates, assembly order from mates_with,
              and everything the automated gates WAIVED
```

Phase 3 does not end in "shipped". It ends in a kit plus the open questions —
every referee finding nobody fixed, every `medium` the reviser refused, every
`too-loose` fit warning. The last gate is four people at a table, so the
pipeline's job is to arrive there with the doubts written down.

## What happens when a gate fails

Phase 3 never repairs geometry. On a gate failure it stops before slicing —
a print kit for unprintable parts is worse than no kit, because it looks
finished — reads the failing STLs out of `gate.json`, maps them back to the
`todo.md` groups that built them, and prints the command to rebuild only those:

```
GATE FAIL on beam_disc, ship
rebuild group(s) [2, 3]:
  ./text2game --slug keep-the-light-relay --phase 2 --groups 2,3
```

Phase 2 now checks printability itself, per group, with `gate.py --no-slice`.
It used to repair on FIT alone, which is half the question: a part can mate
perfectly at 0.3mm and still be non-manifold, or carry a 70% overhang. Those
failures survived every group and only surfaced at the end, with no path back
except a full rebuild. Phase 3 still runs the full gate WITH slicing — that is
the authoritative one — but it should no longer be the first time anyone asks.

## Publish — hand-run, box-bound

`./publish.py <slug>` imports a finished game into Panda Social as a **DRAFT**
design and telegrams a human; the draft->public flip is a person's decision in
admindash, always. The driver never calls it. `./publish_report.py <slug>`
renders the phase-1 result to `/root/shared-reports` for phone reading.

It runs on the panda VM only — it leans on the text2cad toolchain and the
platform secrets, none of which live in this repo:

| needs | where |
|---|---|
| `ADMIN_TOKEN`, `PANDA_OWNER_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_DM` | this repo's `.env` (gitignored; see `.env.example`) |
| `MONGODB_URI`, `MONGODB_DBNAME`, `GCS_BUCKET`, `GCS_CDN_URL` | `/root/panda-secrets/.env` — read LINE BY LINE, never `source`d |
| GCS service account | `/root/panda-secrets/gcs-sa.json` |
| `bin/importdesign` (Go, from panda-social-backend), `gcs_upload_project.py` + `/root/gcsvenv`, `fe_colors.py` + node + `render_three43_fe.mjs` | `/root/text2cad/`, `/root/aibatch/` |
| `/root/panda-social-backend` checkout, admindash on `:8090` | the box |

Overrides: `ADMINDASH_URL`, `BACKEND_DIR`, `TEXT2CAD_DIR`. Deliberately NOT
uploaded: the rulebook (7x over the product-page content contract — it belongs
in the print bundle, not wired yet, Tam 2026-08-20).

## Models

`.env.example` is the record. Two things worth knowing:

- **A model resolves from the JOB name, never from the run label.** `build-g3`
  and `revise-r1` cannot be env var names, so a label used to fall through to
  the sonnet default: it cost phase 2 and 3 their configured models once, and
  phase 1's two revise rounds a second time (`run.json` says sonnet, `.env`
  said opus). `harness.job_of()` normalises the label, and `model_for` goes
  through it.
- Sonnet on build/repair today is a **choice**, not that default. Each of the
  seven sessions is measured against the contract and gated for printability
  with two repairs before it stops, so a weak build is caught by a machine.

Both phases print their model plan on entry.

### Providers

A phase runs on `claude -p` or on `codex exec`, chosen **per job**:

```
./text2game --slug my-game --codex phase1        # the eight rules jobs
./text2game --slug my-game --codex referee,critic
./text2game --slug my-game --codex all
CODEX_JOBS=judge ./discover.py                   # discover has no argv of its own
```

`harness.run_phase` is the only place that knows: same signature, same
`run.json` entry shape, same return value, so no phase, loop or check above it
changes. Aliases: `phase1`, `all`, `none`. Defaults live in `.env`.

`all` deliberately spares **build** and **repair** — their prompts say *"Use
the cadcode skill"* and codex has no skills. Naming one anyway is allowed and
prints a warning.

What a codex row in `run.json` cannot tell you, and why:

| field | codex | reason |
|---|---|---|
| `cost_usd` | always `0.0` | ChatGPT Pro subscription — no marginal per-token price. Recording a made-up figure would poison the ledger both lanes share. |
| `num_turns` | always `null` | codex has no turn budget. The phase timeout is the only bound, so `postmortem` reports a failed codex phase as CRASHED and never STARVED. |
| `codex_items` | count of completed items | the only runaway signal a capless session has. |

Verified on this box 2026-08-19 (codex-cli 0.148.0, `gpt-5.6-sol`): web search
is **off** by default and is turned on per call, reasoning effort ships at
`none` and is raised to `CODEX_EFFORT`, and the subprocess must close stdin or
codex waits on it until the phase times out.

## Instrumentation

| what | where |
|---|---|
| per-phase ledger | `out/<slug>/run.json` — model, wall_s, turns/max_turns, subtype, cost, cache read/write, is_error. A re-run never deletes the attempt it replaced. |
| prompt in / reply out | `out/<slug>/trace/NNNN-<phase>.{in,out}.md` + `index.jsonl` |
| postmortem | `harness.postmortem()` — names the phase that died, on which provider, and whether it was STARVED (turns at cap) or CRASHED |
| stall + death alert | `./watchdog.py <log> --slug <slug>` — telegram, never restarts anything |
| quota death | any phase, regex on the CLI error → telegram → `SystemExit(4)` |
| cross-run memory | `evidence.jsonl` - every critic and referee finding ever produced, one row each, with the run's mechanism lock. Derived, never hand-edited: rebuild with `./harvest.py`. COMMITTED, like `catalog.json` and for the same reason - `out/` is gitignored, so a fresh clone has nothing to rebuild it from and would start with no memory again. |
| unit tests | `tests/test_consistency.py` (38) + `tests/test_harvest.py` (38) + `tests/test_phase23.py` (29) + `tests/test_provider.py` (66) |
