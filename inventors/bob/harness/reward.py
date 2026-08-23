"""Bob's frozen reward function — the evaluator core.

THIS FILE IS FROZEN. `harness/integrity.py` pins its sha256 (with
docs/REWARD.md) in state/REWARD_BASELINE.json; a drifted hash fails
`bob audit` and halts all ticks. Only a human commit may change it —
every self-improving system that worked was an evaluator story
(FunSearch, AlphaEvolve, Ludi); every one that failed edited its own
judge (DGM removed the hallucination markers).

Generator agents must NEVER see this file: METR measured reward hacking
43x more common when the model can see the scoring function. Agents get
lens *reports* (qualitative feedback) — never weights, never thresholds.

Spec: docs/REWARD.md. API pinned by docs/CONTRACTS.md §2.
"""

# Gate ids in cost order (cheapest first) — the gate order IS the
# economics (Armillary receipt: 6 CAD repair rounds + 2 owner amendments
# were spent on rules that later failed the playtest; nothing expensive
# may run before the cheap gates have had their chance to kill).
HARD_GATES = [
    "g1_completeness",   # L0 lint (free): rules doc complete + schema-valid
    "g2_sim_integrity",  # L1 sim (cheap): engine builds, 500 games terminate
    "g3_degeneracy",     # L1 sim: no policy dominates, no forced draw, seat balance
    "g4_novelty",        # L2 judge: no confusable existing game (kill needs a URL)
    "g5_safety",         # L0 + human: 14+ only, no CPSIA class, no third-party IP
    "g6_buildable",      # L1 build gate: watertight, bed-fit, printable (once parts exist)
]

# Score weights per lane. Both sum to 100 so R stays in [0, 100].
# Invention: the full pipeline judges fun and depth from executed games.
# Edition: the classic already proved fun/depth over centuries (fun_sim
# and depth are inherited, weight 0) — the edition is judged as an
# OBJECT: physical_hook and novelty-of-the-edition carry the score.
# Weights live here and not in REWARD.md so generators can't learn them.
WEIGHTS = {
    "invention": {
        "fun_sim": 20.0,        # Ludi-lineage sim metrics: executed games, not opinion
        "fun_table": 25.0,      # 3+ LLM tables, would-play-again per seat
        "depth": 15.0,          # policy ladder: skill gradient without solvability
        "clarity": 15.0,        # blind cold-read Q&A, teach-time <= 5 min
        "novelty_margin": 15.0, # distance from 3 named nearest neighbors
        "physical_hook": 10.0,  # dies as cardboard/PDF? then 0 — print the wound
    },
    "edition": {
        # 2026-08-22 human re-cut (pre-launch verify finding): the edition
        # pipeline skips LLM tables (the classic proved play), so a nonzero
        # fun_table weight made the lane mathematically unpublishable
        # (max R was 65 < 70 with fun_table forever 0). Editions ARE read
        # by the fresh reader (clarity is real evidence); everything else
        # rides on the object.
        "fun_sim": 0.0,         # inherited from the classic (skip L1 engine build)
        "fun_table": 0.0,       # inherited from the classic (tables skipped)
        "depth": 0.0,           # inherited from the classic
        "clarity": 25.0,        # faithfulness + teachability of THIS rules sheet
        "novelty_margin": 35.0, # no confusable existing SET — the edition is the invention
        "physical_hook": 40.0,  # the object is the whole product; sales receipts say so
    },
}

# Publish bar (docs/REWARD.md "Shape"):
PUBLISH_THRESHOLD = 70.0       # R >= 70 to be publish-eligible
MIN_COMPONENT_FRACTION = 0.4   # every component >= 40% of its max — no
                               # component may buy its way past another
                               # (a hilarious-but-unbuildable game must not ship)
MIN_DELTA = 2.0                # keep iterating only while dR >= 2 (or a gate
                               # flipped false->true); below that, park —
                               # text2cad receipt: 58% of $430 went to grinding
                               # designs that were never going to clear


def hard_gates(evidence):
    """Map an evidence dict to {gate_id: bool}. Absent evidence = FAIL.

    Verdicts are seeded FAIL before any lens runs ("an absent lens
    verdict is not a passing one" — the one-way-newsreel lesson: it
    shipped with gate PASS and an EMPTY panel). Only explicit evidence
    flips a gate True.

    Evidence keys (all optional; missing => the gate stays False):
      lint_pass        bool  -> g1. L0 deterministic rules lint.
      lane             str   'invention' (default) or 'edition'.
      sim_report       dict  -> g2/g3 with boolean fields
                       'integrity_pass' (engine built, 500 seeded games
                       terminated, no crash, win reachable) and
                       'degeneracy_pass' (no policy >=85% from seat 1,
                       greedy-vs-greedy not a forced draw, 2p first-player
                       winrate 40-60%). lane=='edition' SKIPS g2/g3 (both
                       True): the classic proved itself over centuries,
                       there is no engine to build.
      novelty_verdict  dict  -> g4: {'pass': bool, 'evidence_url': str|None}.
                       Gate passes only on an explicit pass=True. A FAIL
                       becomes a KILL elsewhere only when evidence_url is
                       a URL the judge actually opened (BGG/marketplace);
                       here any non-pass is simply a failed gate.
      safety_pass      bool  -> g5. CPSIA class / IP check; hard-refuse
                       happens at spark, this is the belt to that suspender.
      build_gate       bool or None -> g6. None means parts don't exist
                       yet: G6 reads "when parts exist" (docs/REWARD.md),
                       so a not-yet-built game passes g6 vacuously — the
                       queue state machine (built -> build_gated ->
                       reviewed -> published) guarantees a real boolean
                       exists before any publish. An explicit False fails.
    """
    if not isinstance(evidence, dict):
        raise ValueError(
            "hard_gates() needs an evidence dict; got %r. Pass {} to get "
            "the all-FAIL seed." % type(evidence).__name__)
    lane = evidence.get("lane", "invention")

    sim = evidence.get("sim_report")
    if lane == "edition":
        # Edition lane: fun/depth inherited from the classic; there is no
        # engine, so the sim gates cannot produce evidence and must not
        # be able to block. docs/REWARD.md "Two lanes, one pipeline".
        g2 = True
        g3 = True
    elif isinstance(sim, dict):
        g2 = sim.get("integrity_pass") is True
        g3 = sim.get("degeneracy_pass") is True
    else:
        g2 = False
        g3 = False

    nov = evidence.get("novelty_verdict")
    g4 = isinstance(nov, dict) and nov.get("pass") is True

    bg = evidence.get("build_gate", None)
    g6 = True if bg is None else bg is True

    return {
        "g1_completeness": evidence.get("lint_pass") is True,
        "g2_sim_integrity": g2,
        "g3_degeneracy": g3,
        "g4_novelty": g4,
        "g5_safety": evidence.get("safety_pass") is True,
        "g6_buildable": g6,
    }


def score(components, lane="invention"):
    """Sum clamped components -> R in [0, 100].

    Components arrive already scaled 0..max (the judges score against
    the rubric's max, not a fraction). We clamp to [0, weight] — a judge
    that returns 30/25 is a judge bug, and letting it through would let
    one lens buy the threshold — and we REFUSE unknown keys instead of
    ignoring them: a silently dropped component is exactly how a scoring
    bug hides (run.json under-reported spend by 12% in text2cad because
    repeated keys overwrote instead of erroring).

    Missing keys count as 0 (seeded-FAIL discipline: an unscored
    dimension contributes nothing).
    """
    if lane not in WEIGHTS:
        raise ValueError(
            "Unknown lane %r; use one of %s." % (lane, sorted(WEIGHTS)))
    weights = WEIGHTS[lane]
    unknown = sorted(set(components) - set(weights))
    if unknown:
        raise ValueError(
            "Unknown score component(s) %s; valid keys are %s. Fix the "
            "caller — score() never silently drops a component."
            % (unknown, sorted(weights)))
    total = 0.0
    for key, w in weights.items():
        raw = float(components.get(key, 0.0))
        total += min(max(raw, 0.0), w)
    return total


def publish_eligible(gates, components, lane="invention"):
    """Publish-eligible <=> ALL gates pass AND R >= 70 AND every
    component >= 40% of its max (docs/REWARD.md "Shape").

    Zero-weight components (edition fun_sim/depth) are exempt from the
    fraction floor — 40% of 0 is 0, there is nothing to demand.
    Gates missing from `gates` count as FAIL (seeded-FAIL discipline).
    """
    for gate_id in HARD_GATES:
        if gates.get(gate_id) is not True:
            return False
    if score(components, lane=lane) < PUBLISH_THRESHOLD:
        return False
    for key, w in WEIGHTS[lane].items():
        if w <= 0.0:
            continue
        raw = min(max(float(components.get(key, 0.0)), 0.0), w)
        if raw < MIN_COMPONENT_FRACTION * w:
            return False
    return True
