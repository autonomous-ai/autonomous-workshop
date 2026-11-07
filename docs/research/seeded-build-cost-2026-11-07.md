# Where a seeded build's cost goes: Sunset Slider Night Light, 2026-11-07

The owner asked why a seeded Workshop build costs so much when it only
re-seals an approved Contract Proof (ADR 0096). This note measures one case
from its native transcripts. It is the evidence for
[ADR 0098](../adr/0098-seeded-make-runs-its-checks-as-one-host-batch.md).

## Method

- **Unit.** One cost unit is 1M input-equivalent tokens, weighted by money:
  cached read 0.1, cache write 1.25, uncached input 1, output 5. Raw token
  counts are not used to rank anything; cached reads are cheap and output is
  expensive.
- **Sources** (all read-only; the run was still active, resumed by another
  agent):
  - Attempt 2, `wish-20261107-084342-533c8a5b`: the Claude Code transcript
    `~/.claude/projects/-home-loginuserxx--local-share-autonomous-workshop-runs-wish-20261107-084342-533c8a5b-workspace/2fb85bb1-….jsonl`
    and its four subagent transcripts, read up to 15:34 on 2026-11-07.
  - Attempt 1, `wish-20261106-170410-4499e889`: its transcript under the
    matching `~/.claude/projects/…-4499e889-workspace/` directory.
  - Design: the design-a-toy coordinator session `94ce0c59-…` under
    `~/.claude/projects/-home-loginuserxx-harnesses-autonomous-workshop/`
    and its subagents; `toys-spec/synthwave-arcade-lamp/NOTES.md`;
    `contract/proof/APPROVAL.json` (`design_cost_units: 56.04`);
    `contract/build-a-toy/ledger.json`.
  - `workshop status --json` (read-only) for the host's own observation.
- **Calls.** One model call is one assistant message id; Claude Code writes
  several lines per message, which are deduplicated. Average context is the
  call's cached read + cache write + uncached input.
- **Phases** are time windows cut at the transcript's own transitions (the
  first `make_round --component`, the first `check_power`, the first
  `--record-visual`, the finalizer, the host's rejection prompt, and so on).
- **Call kinds** come from each call's tool use:
  - *run-tool*: the call only ran a deterministic tool (make_round,
    check_motion, check_power, check_mount, verify_project, bought_model,
    the finalizer, `wait_for.py`, `sha256sum`/`cmp`, `pgrep`) and read its
    result.
  - *read/probe*: `cat`, `sed -n`, `grep`, `ls`, Read, ad-hoc Python probes.
  - *author*: Write, Edit, or a shell heredoc or `sed -i` that writes a file.
  - *agent*: spawning a subagent.
- **Reconciliation.**
  - The attempt-2 root transcript sums to 98.6M cached reads, 1.50M cache
    writes, 0.45M output: **13.98 units**. The host's status observation at
    100.0M tokens was 13.8 units; the transcript ran on a little after it.
  - Attempt 1's transcripts sum to 8.31 units, as NOTES.md records.
  - The design sessions sum to 56.1 units against the sealed 56.04.

## Seeded Make, attempt 2 (root session, 13.98 units)

| Phase | Calls | Avg context | Units | Share | Run-tool only | Read/probe | Author |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 Setup: STAGE, skill, make.md, make-round card, contract | 32 | 90K | 0.50 | 3.6% | 3 | 27 | 2 |
| 2 Toolchain fix (OCP loads the system libexpat; `LD_PRELOAD`) | 6 | 139K | 0.12 | 0.9% | 1 | 4 | 1 |
| 3 Shared Helper freeze + 24 component rounds, all carried exact | 25 | 156K | 0.45 | 3.2% | 25 | 0 | 0 |
| 4 Coupled Interfaces (5 of 6 pass) + reading motion docs | 15 | 182K | 0.33 | 2.4% | 8 | 7 | 0 |
| 5 Power: authoring `work/make_power.py`, `check_power` | 30 | 163K | 0.69 | 5.0% | 6 | 19 | 5 |
| 6 Motion: authoring `work/make_motion.py`, `check_motion` | 33 | 98K | 0.58 | 4.2% | 10 | 19 | 4 |
| 7 Bought Parts placements, `check_mount`, the drive-frame lead-hole deviation and its worker | 130 | 145K | 2.60 | 18.6% | 43 | 66 | 19 |
| 8a Assembly rounds + visual feedback | 46 | 187K | 1.09 | 7.8% | 23 | 15 | 6 |
| 8b Product renders, motion states, `spark-source.json`, carried assembly review | 81 | 100K | 1.15 | 8.2% | 17 | 57 | 2 |
| 8c Motion presentation + motion critic rounds 1-2 | 82 | 146K | 1.61 | 11.5% | 13 | 43 | 14 |
| 8d Part export, `bought_model --final`, `--full` verification | 63 | 126K | 1.03 | 7.4% | 21 | 31 | 11 |
| 9 First finalize (`stage_proposal.py make`) | 16 | 170K | 0.33 | 2.4% | 5 | 9 | 1 |
| 10a Host rejection `make-contract-invalid`: diagnosing the finalizer, colour-named occurrences | 135 | 139K | 2.56 | 18.3% | 30 | 97 | 8 |
| 10b Rejection: motion critic rounds 3-4 on regenerated evidence | 16 | 192K | 0.64 | 4.6% | 4 | 6 | 4 |
| 10c Rejection: `--full` verification again, twice | 21 | 81K | 0.29 | 2.1% | 12 | 9 | 0 |
| **Total** | **731** | **135K** | **13.98** | 100% | **221** | **409** | **77** |

The four subagents add 0.83 units: the drive-frame Component Worker (9 calls,
37K context, 0.10), and three motion critic rounds (7, 11 and 27 calls, 32-49K
context, 0.73 together). The host's status observation lists one thread, so
these may not be in its 100M; this is not verified.

### What the money is

- **Cached reads are 70% of the cost** (9.86 of 13.98 units). Output is 16%
  (2.24); cache writes 13% (1.87). Cost is the number of calls times the
  context each call re-reads, not what the model writes.
- **Each root call costs about 0.019 units** at an average context of 135K.
  The same model with a 32-49K context, in the subagents, cost 0.011-0.021
  per call; the drive-frame worker cost 0.011 per call.
- **Six compactions** kept the context near 100-190K. Each compaction
  summary is a cache write, and the turns after it re-read the summary.

### How much was deterministic

- **221 of 731 calls (30%, 4.11 units) only ran a deterministic tool and
  read its result.** 26 of them (0.47 units) were `wait_for.py` polls on a
  long check. The 25 component-round calls cost 0.018 units each to say
  "locked, exact" 24 times.
- **131 calls (2.26 units) read the source of a host tool** (`make_round`,
  `verify_project`, `check_motion`, `check_power`, `check_mount`,
  `bought_model.py`, `stage_proposal.py`) to learn what a gate or the
  finalizer wanted. Another 70 calls (1.19 units) re-read skill docs. In the
  rejection loop alone, 97 of 135 calls were reads.
- **Only 77 calls (1.88 units) authored anything.** None of them changed the
  approved shape except the drive-frame lead-hole repair.

### What the seed did not carry

The run did not only re-seal. The Approved Proof lacked the inputs that
final verification needs, so the Manager wrote them in the run:

| Input the gates need | Written in the run by | Phase |
|---|---|---|
| `measure/power.json`, `measure/mounts.json`, `measure/electrical/`, `ref/validation/*.step` | `work/make_power.py` | 5, 7 |
| `measure/bought-placements.json` (the tilted switch) | `work/make_power.py` | 7 |
| `measure/motion.json` (15 conditions; design ran 14, outside the seal, in `/tmp/swl_motion.json`) | `work/make_motion.py` | 6, 8b |
| production occurrences in `proof.step.py` (colour-named) | hand edits, then again after the rejection | 7, 10a |
| `snap/iso.png`, `snap/signature.png`, motion states and animation | `work/states/`, `render_review` | 8b, 8c |
| `spark-source.json`, `product.json` title and summary | `work/make_source.py` | 8b |
| exported parts | `work/export_parts.py` | 8d, 10a |

Design already ran `check_motion` 14/14 and `check_power` on the Proof, but
sealed neither manifest. Issue #227 (design-a-toy's Proof should run
`bought_model`) is the same gap for Bought Parts.

### Real defects the checks found

- **The drive-frame lead hole** met the switch wire's envelope. This is a
  genuine seed defect. A Component Worker repaired it within `proof_diff`
  tolerance in 9 calls and 0.10 units. The Manager's diagnosis around it
  (probes, `check_mount`, the unlock record) cost far more, inside phase 7.
- **The gear-mesh contradiction** stopped attempt 1 (the `driven` pose
  against 0.2 mm backlash). It was settled at the root with `amend-a`.
- **Two `bought_model` harness defects** stopped attempt 1 (issues #225 and
  #228).

Every one of these is reported by a deterministic check in its own words.
None needed a model to find it.

## Attempt 1 (8.31 units)

Attempt 1 passed every component round, `check_power`, `check_mount` and
`check_motion` 14/14, then stopped three times: twice on harness defects and
once on the gear-mesh contradiction. Its 340 root calls cost 7.55 units:

- 40% run-tool (137 calls, 2.90 units);
- 43% read/probe (157 calls, 3.27 units);
- 17% author (42 calls, 1.28 units).

Two subagents add 0.76 units.

**Make for this toy so far:** 8.31 + 13.98 = **22.3 units**, before the
attempt that is running now. That is 40% of the design's 56 units, for a
build whose shape the owner had already approved.

## Design (56.04 units, coarser)

The design-a-toy coordinator (`94ce0c59`) is one long session from
2026-11-02 to now. It also supervises the builds after the seal, so it is cut
at the first `workshop wish` (2026-11-06 17:03).

| Part of the design | Who | Calls | Avg context | Units |
|---|---|---:|---:|---:|
| Concept brainstorm, Concept Gate rounds 1-7, final concept, three views | coordinator | 759 | 161K | 21.81 |
| Concept research (layered scenes, motif inventory, synthwave references) | 3 subagents | 122 | 57-116K | 2.32 |
| Diagnosing the window colour loss | fork | 56 | 175K | 1.85 |
| Concept Checklists (three versions) | 3 subagents | 38 | 46-48K | 0.56 |
| Contract draft, reference and guide image passes, Proof coordination | coordinator | 284 | 169K | 7.58 |
| **Contract Proof** (all rounds) | 1 subagent | 507 | 152K | **15.37** |
| Proof Critic rounds 1-2, round 3 (the carrier notch) | 2 subagents | 41 | 54-116K | 1.14 |
| Critic follow-up, reference re-edits, Stage 3c/3d, Stage 4 page | coordinator | 129 | 165K | 3.15 |
| Owner amendments, notch, reseal | coordinator | 112 | 153K | 2.32 |
| **Design total** | | | | **56.1** |

After the seal, the same coordinator spent 4.63 units supervising both build
attempts, and a subagent spent 3.02 units fixing the harness (#225). Neither
is design or Make cost.

- **The Proof itself** cost 15.37 units over 507 calls:
  - 35% author (153 calls, 5.40 units);
  - 53% read/probe (294 calls, 8.19 units);
  - 10% run-tool (48 calls, 1.54 units).
- **The coordinator is 62% of design cost** (34.9 of 56.1), mostly before
  the contract existed (Concept Gate, 21.8 units). This matches the
  "coordinator, not the Proof" finding of ADR 0096's context.

### What could not be measured

- **Image generation.** It runs through OpenRouter (`gen_image.py`,
  `gpt-image-2.5-sunburst`), outside the model transcripts. No billing record
  for it is in the repo or the toy folder. Only the coordinator's calls
  around it are counted.
- **Owner time** at the Concept Gate and Stage 4.
- **Wall-clock compute of the checks.** Motion sweeps and `--full` ran for
  tens of minutes each. The `wait_for` polls are counted, but not the CPU.
- **Whether the host counted subagent usage.** See above.
- **The current resumed attempt.** It was still running when this was
  measured.

## Conclusions for the ADR

1. **The seed does not carry every check's input.** Make's model cost on a
   seeded run is mostly writing and debugging those inputs: power, motion,
   placements, occurrences, renders, source. Re-running the checks is
   cheap. The inputs belong in the Approved Proof, written and gated in
   design, where the Proof already ran the same checks.
2. **A third of the calls only ran a tool.** Every one of them re-read a
   ~135K context to do it. Run as one host batch, these cost compute and no
   tokens.
3. **Reading host source to infer what a gate wants is the largest single
   waste** (131 calls, 2.26 units, across the run; the rejection loop is 97
   reads of 135 calls). A failing check should hand the model its exact
   report, not a vague code.
4. **A focused turn is cheap because it is short, not only because its
   context is small.** The drive-frame repair cost 0.011 units a call
   against the root's 0.019, and needed 9 calls, not 130. It is the model
   of the turn that should remain.
