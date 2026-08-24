# Boardgame Science — what is actually known about making board games fun

_Research for Bob (autonomous board-game inventor). 2026-08-22._
_Purpose: ground Bob's evaluators (the reward function) and his scholar loop (the taxonomy he studies) in named sources, exact numbers, and the one commercially proven precedent for what Bob is: a computer that invented a good game._

TLDR for the synthesizer:
- **The precedent exists.** Cameron Browne's LUDI (PhD 2008) evolved 1,389 games from 79 seed games, scored them with a weighted sum of **57 self-play aesthetic criteria narrowed to 17 that correlated with human preference**, and produced **Yavalath** — the first computer-invented game commercially published (nestorgames), top-#100 abstract on BGG by Oct 2011, GECCO "Humies" gold 2012. Bob is LUDI + LLMs + a 3D printer + a marketplace. GAVEL (2024) is the modern LLM version and gives the exact 5-metric fitness Bob should start from.
- **Fun is measurable by proxy, decidable only by humans.** Self-play metrics (balance, decisiveness, drama, policy-ladder depth, decision density, duration) filter out the 95% of designs that are broken. The last 5% — "is it fun" — is Koster's pattern-learning and Rosewater's emotion, and only a table of humans (or a very honest LLM table-simulation plus the house "can we play again?" gate) can score it.
- **The house thesis is validated by the literature.** "Print the wound" (print only the load-bearing mechanism) matches the field's finding that 3D printing wins when the print is *mechanically necessary* (mechanism, tolerance, hidden geometry), not decorative — decorated-dice 3D-print games stayed a novelty for exactly the reason `ten-new-games-2026.md` says.

---

## 1. Design wisdom, named sources

### 1.1 Mark Rosewater — "Twenty Years, Twenty Lessons" (GDC 2016)

Head designer of Magic: The Gathering. Talk: GDC 2016, also a 3-part column on magic.wizards.com ("Twenty Years, Twenty Lessons," Parts 1–3, May 30 / Jun 6 / Jun 13, 2016). The full list, with the lines that matter to Bob:

| # | Lesson | Load-bearing quote / gist |
|---|--------|---------------------------|
| 1 | Fighting against human nature is a losing battle | "You shouldn't change your players to match your game; you should change your game to match your players." |
| 2 | Aesthetics matter | "Aesthetics aren't just a decorative issue. They affect how your players perceive your game." Components must *feel* right — direct license for Bob to care about print quality and piece feel. |
| 3 | Resonance is important | "Your audience has a huge pool of emotional equity that you can tap into." Theme should borrow pre-loaded emotion (orbits, bridges, clocks — the house ten all do this). |
| 4 | Make use of piggybacking | Use pre-existing knowledge to front-load learning. A new game should reuse one known convention (turns, capture, drafting) so only the novel mechanism must be taught. |
| 5 | Don't confuse "interesting" with "fun" | "When you speak to a player on an emotional level, you're more likely to create player satisfaction." **Bob's biggest personal risk**: LLMs generate *interesting* systems; the evaluator must ask what the player *feels*. |
| 6 | Understand what emotion your game is trying to evoke | "No scene is worth a movie, no line is worth a scene." Every rule serves the one emotion; cut rules that don't. |
| 7 | Allow the players the ability to make the game personal | "Knowledge equals quality" — familiarity breeds preference. |
| 8 | The details are where the players fall in love with your game | Small touches carry the emotional bond (Soul's birth certificates are this lesson). |
| 9 | Allow your players to have a sense of ownership | "When their deck wins, *they* win… it's an extension of themselves." Axis B (per-copy AI content) is this lesson industrialized. |
| 10 | Leave room for the player to explore | Discovery > exposition. INTERLOCK's "the law is in the edges, discover it" is this. |
| 11 | If everyone likes your game but no one loves it, it will fail | "Your players don't need to love everything, but they need to love something." **Evaluator consequence: optimize for a spike of love, not a high mean.** A 7.0-average-no-variance design should lose to a polarizing 6.5. |
| 12 | Don't design to prove you can do something | Guard against "look what the printer can do" games where the mechanism doesn't serve play. |
| 13 | Make the fun part also the correct strategy to win | "What it takes to succeed at your game is the very thing that makes the game fun." **Testable**: the optimal policy found by search must route through the marquee mechanism. If the AI wins GYRE while ignoring the dip, the game is broken. |
| 14 | Don't be afraid to be blunt | Rules writing: clarity over subtlety. |
| 15 | Design the component for its intended audience | Psychographics: Magic's Timmy/Johnny/Spike. Every Bob game names its audience before design starts. |
| 16 | Be more afraid of boring your players than challenging them | "The greatest risk is not taking risks." Prunes the bandit toward bold arms. |
| 17 | You don't have to change much to change everything | "Instead of asking 'How much do I need to add?' I ask 'How little do I need to add?'" Yavalath is chess-grade proof: one rule (lose on 3-in-a-row) makes the whole game. **Iteration consequence: mutations should be minimal — one-rule deltas.** |
| 18 | Restrictions breed creativity | Bob's constraints (one 200 mm bed, one printed mechanism, $40–80) are assets. |
| 19 | Your audience is good at recognizing problems and bad at solving them | "Your players have a better understanding of how they feel about your game than you do." **Playtest ingestion rule: trust reported symptoms, discard proposed fixes.** |
| 20 | All the lessons connect | — |

Sources: [GDC Vault](https://gdcvault.com/play/1023186/Twenty-Years-Twenty), [Part 1](https://magic.wizards.com/en/news/making-magic/twenty-years-twenty-lessons-part-1-2016-05-30), [Part 2](https://magic.wizards.com/en/news/making-magic/twenty-years-twenty-lessons-part-2-2016-06-06), [Part 3](https://magic.wizards.com/en/news/making-magic/twenty-years-twenty-lessons-part-3-2016-06-13).

### 1.2 Reiner Knizia — the mathematician's philosophy

PhD in mathematics; 700+ published games (Tigris & Euphrates, Ra, Modern Art, Lost Cities, Ingenious). Canonical quote: **"When playing a game, the goal is to win, but it is the goal that is important, not the winning."** ([ludobits.com](https://ludobits.com/quotes/reiner-knizia-on-winning/)) — the win condition is scaffolding for tension, not the product.

Operable Knizia principles:
- **The scoring system IS the game.** "How you score shapes how you play more profoundly than any amount of flavour text" (Think Like a Game Designer podcast #52 with Justin Gary, 2023-09-26). Bob should design the scoring function *first* and derive rules from it.
- **Score the weakest, not the sum.** Tigris & Euphrates: your final score is your *lowest* color. One aggregation choice forces balanced play and constant tension. A library of aggregation functions (min, max, product, median, set-collection thresholds) is a cheap, high-yield design axis for Bob.
- **Tension from tight economies and forced tradeoffs**, not from content volume. Knizia games are famously "simple rules, profound play" — the same target as a printable one-mechanism game.
- Knizia playtests relentlessly with target-audience groups and cuts anything that doesn't earn its complexity ("Creation of a Successful Game" lecture, reported by critical-hits.com, 2008-07-03).

### 1.3 Raph Koster — A Theory of Fun for Game Design (2004, 2nd ed. 2013)

The one workable *theory* of fun:
- **"Fun is just another word for learning."** Games are pattern-teaching machines; the pleasure is the moment of grokking a pattern.
- **"Boredom is the opposite of learning."** A game dies when the pattern is exhausted (mastered) or unreachable (noise). Two distinct failure modes Bob's evaluator must separate: *solved* (dominant strategy exists → greedy ≈ optimal) and *illegible* (no learnable pattern → random ≈ skilled).
- "Games are just exceptionally tasty patterns to eat up."
- Consequence for per-copy AI content (Axis B): regeneration resets the pattern-learning curve — Koster is the theoretical justification for why "no two boxes alike" adds replay fun rather than gimmick. But the *pattern family* must stay learnable across copies (skill must transfer between two GYRE orbital tables, or there's no mastery arc at all).

### 1.4 Playtesting methodology (the practitioner consensus)

The serious-designer protocol, consistent across Stonemaier Games (Jamey Stegmaier), the BackerKit/Stonemaier crowdfunding literature, and GDC playtesting talks — and already encoded in the house `PLAYTEST.md`:

1. **Staged testing:** self-play → internal/local table → **blind** external (BackerKit: "The 3 stages of playtesting — Internal, Local, and Blind"). Stegmaier ships digital files to strangers worldwide; feedback comes back without him in the room. Rules ambiguity found this way counts as a bug ("hints count as bugs" — house rule, same doctrine).
2. **One change at a time.** Tweak → test → keep. Never two mechanics at once (house rule #4; standard practice — otherwise attribution of the delta is lost). This is Bob's A/B discipline: each iteration is a single named rule-delta with a before/after metric diff.
3. **Watch behavior, don't collect opinions.** Rosewater #19: symptoms yes, fixes no. Measure re-play requests, dead-spot minutes, rules questions per session, who disengaged.
4. **Fun over theme-accuracy.** Stegmaier: if thematically accurate but boring, cut the accuracy (nerdsonearth.com interview, 2017-06).
5. **The exit gate is behavioral:** house metric — **FUN = a player asks to play again without being asked; 3 consecutive voluntary "can we play again?"s from different groups = 10/10, ship-eligible** (`PLAYTEST.md`). This is the ground-truth label Bob's proxy metrics are trained against.

---

## 2. Computable proxies of fun (game AI / automated game design)

### 2.1 The lineage: LUDI → Ludii → GAVEL

**Cameron Browne, "Automatic generation and evaluation of recombination games," PhD thesis, QUT 2008** ([QUT ePrints 17025](https://eprints.qut.edu.au/17025/)); book form: *Evolutionary Game Design*, Springer 2011. The exact pipeline Bob is a descendant of:

- A **game description language** of *ludemes* (board shape, placement/movement rules, end/win conditions) so games can be crossed and mutated — e.g., "turn a win condition of 3-in-a-row into a *lose* condition of 3-in-a-row" (that mutation literally is Yavalath).
- **79 seed games** played by human subjects in A/B preference pairs; the same games played by AI self-play while **57 aesthetic criteria** were logged (names include: Convergence, Uncertainty, Drama, Stability, Momentum, Coolness — "the degree to which players are forced to moves that harm their position" — Completion, Duration, Killer moves, Permanence, Clarity, plus boolean win-condition descriptors). Fitness = weighted sum.
- Correlation of self-play criteria vs. human preference narrowed **57 → 17 criteria** that actually predict human liking — including **Duration, Completion, Uncertainty (late), Killer moves, Clarity (variance), Permanence**, and grouping-type win conditions. ("Puzzle quality" correlated but was cut for compute cost.) Source: James Nathan's thesis read-through, [Opinionated Gamers, 2018-04-23](https://opinionatedgamers.com/2018/04/23/james-nathan-cameron-brownes-automatic-generation-and-evaluation-of-recombination-games/).
- LUDI evolved **1,389 new games**, auto-filtered to a **top 19**, human-validated in a second survey. #1 was **Ndengrod** (now Pentalath); #2 was **Yavalath**: hex board side-5, place a piece each turn, **win with 4-in-a-row, lose if you make 3-in-a-row first**. Published by nestorgames — "the first — and still only [as of that writing] — computer-generated game to be commercially published"; **top-#100 abstract games on BGG (Oct 2011); GECCO Humies gold medal 2012** ([cambolbro.com/games/yavalath](http://cambolbro.com/games/yavalath/)).
- Key thesis insight for Bob's architecture (Nathan's summary): the hard problem was never *generating* 1,389 games — it was **"how will you playtest them? How will you skim the cream?"** The generator is cheap; the evaluator is the product.

**Ludii** (Browne's ERC follow-up, Maastricht) — ludemic general game system with **1,000+ games** implemented; the standard research substrate for measuring game quality at scale ([arXiv:1907.00240](https://arxiv.org/abs/1907.00240)). Bob need not use Ludii, but should copy its metric definitions (below) into his own simulator.

**GAVEL — "Generating Games via Evolution and Language Models" (Todd, Padula, Stephenson, Piette, Soemers, Togelius; NeurIPS 2024, arXiv:2407.09388)** — the current state of the art and the closest published system to Bob: a fine-tuned code LLM (CodeLlama-13b trained on 1,000+ Ludii games) proposes rule mutations; **MAP-Elites** keeps an archive diverse (novelty axes = PCA over Ludii concept vectors); fitness is the **harmonic mean** (so one bad dimension tanks the score) of five self-play metrics:

1. **Balance** — variance/difference in win rates between seats.
2. **Decisiveness** — proportion of non-draw games.
3. **Completion** — proportion of playouts reaching an end state (within move cap).
4. **Agency** — proportion of turns with more than one legal move.
5. **Coverage** — proportion of board sites used during playouts.

Produced novel playable games (Havabu, YavaGo, HopThrough). **Bob's v1 fitness should be exactly these five as the "not broken" floor, with Browne's aesthetic tier on top.**

### 2.2 The proxy metrics, one by one (with thresholds Bob can code)

All measured over N self-play games (Browne used dozens per game; use ≥1,000 fast playouts for balance stats, ≥100 for search-agent stats).

**Decision density / agency.** Sid Meier: "a game is a series of interesting decisions" (GDC 2012). Floor metric: GAVEL's *agency* = % of turns with >1 legal move (target ~100%; forced-move chains are dead time). Better: a turn is a *real* decision only if legal moves differ in value — measure value-spread of moves under a search agent. Browne's *clarity* is the flip side: a player should be able to *tell* moves apart; pure noise (all moves equal value) and pure solvedness (one move obviously best every turn) both kill fun. Healthy branching for abstracts: roughly 3–80 meaningful options; what matters is not raw branching factor but **branching-factor relevance** — how many of the options a competent player would ever consider, and how often the top choice is non-obvious.

**Dominant-strategy detection via policy ladders.** The standard trick is **Relative Algorithm Performance Profiles** (Nielsen, Barros, Togelius, Nelson, "General Video Game Evaluation Using Relative Algorithm Performance Profiles," EvoApplications 2015): run a ladder of agents — **random < greedy(1-ply) < shallow search < deep search/MCTS** — and demand a monotone win-rate staircase with real gaps.
- random ≈ deep search → the game is noise (no skill).
- greedy ≈ deep search → the game is shallow / has a dominant strategy (solved by myopia).
- A fixed opening policy (e.g., "always play the same column") beating adaptive play → degenerate strategy; kill or patch.
Formalized as **depth = length of the skill chain**: Lantz, Isaksen, Jaffe, Togelius, Nealen, "Depth in Strategic Games" (AAAI-17 workshop) — a game is deep if there's a long chain of agents, each investing more (compute/learning), each beating the last. Bob's ladder: `random → greedy → 2-ply αβ → MCTS-100ms → MCTS-1s`, plus one "degenerate specialist" per suspected exploit. Every rung should score 60–75% vs. the rung below; >90% gaps mean the game punishes weakness too brutally for a table of mixed skill.

**First-player advantage / balance.** Measure seat win-rates directly (Ludii/GAVEL *balance*). Calibration from real games: chess White scores ~54–56% in master databases; Go's first-move edge was so persistent that komi rose historically 4.5 → 5.5 → 6.5 (Japanese) → 7.5 (Chinese rules); Hex is a first-player win with perfect play (Nash's strategy-stealing argument), which is why serious play uses the **pie rule** (one player sets up, the other chooses sides). Bob's gate: seat win-rate within **45–55%** at the strongest ladder rung, else auto-apply a standard fix (pie rule, komi/points handicap, staggered resources, simultaneous turns) and re-measure. Also check *all* seats in 3+ player games, and kingmaking (can a losing player choose the winner? — Elias/Garfield/Gutschera, *Characteristics of Games*, MIT Press 2012, treats kingmaker as a first-class defect).

**Drama, lead changes, closeness.** Browne's definitions: **drama** = degree to which the eventual winner was behind ("suffers a negative lead") during the game — the chance to recover from a bad position; **uncertainty (late)** = the outcome stays unclear deep into the game. Lead changes: "if a game does not alternate the leader, it becomes tedious; too many lead changes make the game unpredictable or chaotic" (Browne). Computable: run an evaluator/value-net over the game trace → a **win-probability curve**; extract (a) # lead changes (healthy: ~1–3 per game, not 0, not every turn), (b) time-of-last-lead-change (late is dramatic), (c) final margin distribution (close endings; blowouts <some % of games), (d) % of games where the winner trailed at the midpoint (target: substantial, e.g. 30–60%). Guard the converse: **permanence** (moves shouldn't be instantly undoable — takeback loops read as stalling) and **killer moves** ("significantly change a player's situation, turning them from a loser to a winner quickly") should exist but be scarce — a game decided only by one late killer move makes the first 80% of play meaningless.

**Game length distribution.** Browne's *duration* was among the 17 human-predictive criteria: games that end too fast feel accidental; games that drag feel dead. Measure the full distribution, not the mean: median in the design-target band (house games: 15–50 min; convert to turns), **coefficient of variation modest** (a game advertised at 30 min that sometimes runs 90 is broken), and near-zero mass below a "false start" floor (e.g., <25% of median). *Completion* (reaching a real end state) ~100% within the move cap; draws (decisiveness) <5–10% for 2-player abstracts.

**Board/component coverage.** GAVEL's *coverage*: if playouts never touch half the board (or a printed mechanism never actuates), the physical design is oversized or the mechanism is decorative — for Bob this doubles as a **print-the-wound audit**: % of playouts in which the marquee mechanism materially changed the outcome. Target: the mechanism is on the critical path of the winning line in the large majority of games (Rosewater #13 made computable).

**What the proxies cannot see.** Browne's criteria predicted preferences among 2-player abstracts. They say nothing about humor, table talk, bluff-reading, negotiation, dexterity feel, or theme resonance — i.e., most of what makes party/social/dexterity games fun, and *all* of Rosewater #5's emotional layer. LLM table-simulation playtests (reinSPQR pattern: personas around a virtual table, transcript mining for confusion/boredom/AP) partially cover this, and the human blind table covers the rest. **Bob's reward = tiered: (T0) simulables as hard gates → (T1) LLM-table signals as soft score → (T2) human "play again?" as ground truth that recalibrates T0/T1 weights over time.** That recalibration loop is exactly Browne's 57→17 experiment, run continuously.

---

## 3. Taxonomy skeleton for the scholar loop

Backbone sources: H.J.R. Murray, *A History of Board-Games Other Than Chess* (1952); David Parlett, *The Oxford History of Board Games* (1999) — traditional games classified as **race / space (alignment & configuration) / chase / displace (war) / mancala**; BoardGameGeek's mechanics list (~190 mechanics); Geoffrey Engelstein & Isaac Shalev, *Building Blocks of Tabletop Game Design* (2019, 2nd ed. 2022) — ~200 mechanisms in 13 categories, the single best structured syllabus for a scholar loop.

Each family below = one scholar-loop unit: study 2–3 exemplars, extract the *lesson* (the invariant that makes the family fun), add the lesson to Bob's design library, and register the family as a bandit arm.

**A. Ancient & traditional (the load-bearing invariants)**
1. **Race games** (Senet ~3100 BCE; Royal Game of Ur ~2600 BCE; Backgammon; Pachisi). Lesson: **luck + meaningful routing choice**; the doubling cube (backgammon, 1920s) is the oldest great "tension dial." Randomness is fine if the *decision about the randomness* is yours.
2. **War/capture games** (Chess, Xianggi, Shogi; Latrunculi; **Tafl** — asymmetric sides). Lesson: piece differentiation creates legible roles; asymmetry (Tafl's king-escape vs. capture) is ancient and beloved but doubles the balance burden — measure per-side win rates.
3. **Position/territory/connection** (Go ~2500 yrs; Nine Men's Morris; Hex 1942; Yavalath 2007). Lesson: **maximum depth per rule** lives here; also where all of §2's metrics apply most cleanly. Go's komi history = balance is patchable by points; Hex's pie rule = balance is patchable by procedure.
4. **Mancala family** (sowing games, hundreds of variants). Lesson: one physical verb (scoop & sow) carries the whole game — the strongest ancient precedent for "the mechanism is the game," and inherently tactile: closest ancient ancestor of the print-the-wound thesis.
5. **Hunt/chase (asymmetric)** (Fox & Geese, Bagh-Chal). Lesson: 1-vs-many asymmetry; good solo-vs-AI genes.

**B. Classical/folk & dexterity (the physical lineage — Bob's home turf)**
6. **Dexterity & physics** (Crokinole 1876; Carrom; Jenga; Loopin' Louie; Icecool; Klask; Rhino Hero; Cube Quest; mass-market mechanism toys: Mouse Trap 1963, Gravitrax). Lesson: **physics is a rules engine nobody argues with** (PLUMB's "the only fair referee is gravity") and skill progression is bodily, so Koster-learning is automatic. Historically undervalued by BGG-style raters but over-performs at real tables and in gift/holiday retail — exactly the house market. Every dexterity classic is *one* mechanism polished (flick, stack, tilt) — validation of one-mechanism games at $40 price points.
7. **Traditional card structures** (trick-taking: Whist→Skull King; climbing: Big Two→Tichu; shedding, melding). Lesson: hand management + hidden information + trick tension from 500 years of A/B testing; mechanisms that survived centuries are maximally load-bearing per rule.

**C. Modern families (post-1995) and their lessons**
8. **Eurogames** (Catan 1995; Carcassonne 2000; Ticket to Ride 2004; Agricola; Wingspan 2019). Lessons: indirect conflict, multiple scoring paths, **no player elimination**, catch-up mechanisms, 30–90 min; drama engineered via hidden endgame scoring. The BGG-top-list center of gravity (weight ~2.5–4.0).
9. **Ameritrash/thematic** (Risk→Nemesis, Dead of Winter). Lesson: theme first, variance welcomed, table stories are the product — Rosewater #5's emotional register; proxy metrics undervalue these on purpose.
10. **Worker placement / engine building / deck building** (Caylus 2005; Dominion 2008; Splendor; Race for the Galaxy). Lesson: **escalation curves feel like growth** (Koster-learning embodied in the economy); blocking = clean interaction. Dominant-path risk is highest here — policy-ladder these hard.
11. **Auction/valuation** (Knizia's Ra, Modern Art; Power Grid). Lesson: players generate the balance themselves — prices self-correct; the designer only supplies the market structure. Cheap for Bob: auctions self-balance AI-generated content whose values Bob can't perfectly tune (Axis B synergy: auction the AI-generated assets rather than price them).
12. **Social deduction / negotiation / party** (Werewolf; The Resistance; Codenames 2015; Wavelength; Diplomacy 1959). Lesson: the *other players* are the content; rules are minimal; fun is unsimulable — human/LLM-table testing only. Party sweet spot 15–30 min, teach-in-60-seconds.
13. **Roll-and-write / flip-and-write** (Yahtzee 1956 → Qwixx 2012 → Welcome To 2018 → Cartographers). Lesson: shared prompt + private combinatorial decisions = high decision density, zero downtime, near-zero components. **Natural Axis-B carrier: every sheet can be AI-generated and remixed** — cheapest possible per-copy uniqueness.
14. **Cooperative & campaign/legacy** (Pandemic 2008; Pandemic Legacy 2015; Gloomhaven 2017). Lessons: co-op vs. an automaton (quarterbacking is the failure mode — fix with hidden info); legacy = **permanent physical change as content**, the strongest retail proof that people pay for *a copy that becomes uniquely theirs* — the psychological precedent for per-copy AI generation.
15. **Abstract renaissance / combinatorial** (GIPF project 1997–; Hive 2001; Azul 2017; Santorini; Onitama). Lesson: the modern commercial ceiling for pure-mechanism games — and where computer-aided design has already succeeded (Yavalath sits in this family).
16. **Deduction/information games** (Mastermind; Clue; Cryptid; Sleuth; Turing Machine 2022 — which shipped with a physical punch-card verifier). Lesson: information budget design — each query must yield partial, composable evidence. THE ORACLE is this family with the deduction target made physical; Turing Machine proves a "mechanical verifier" deduction game sells today.

**Scholar-loop mechanics:** one family per cycle → extract 3–5 invariants ("what this family teaches," seeded from the table above) → add exemplar+invariant cards to the design library → bandit arms = family × house-mechanism-class (gear/linkage/gravity/tension/hidden-geometry) combos, rewarded by downstream game scores. History says the fertile ground is **crossovers** (deck-building × territory = Dominion→Tyrants of the Underdark; roll-and-write × drafting = Cartographers): mutation by *recombination across families* is literally how LUDI worked ("recombination games").

---

## 4. What makes 3D-printed games win

House thesis (`projects/vibe/boardgames/ten-new-games-2026.md` + `PLAYTEST.md`), confirmed against the market:

1. **The print must be load-bearing, or it's a novelty.** "Existing 3D-printed games use the printer for **decoration** — nicER chess pieces, fancier dice. That's why they're a novelty and not a category" (ten-new-games-2026.md). Survey of the 3D-print games market (Cults3D "349 best board-game STLs," Etsy/Gambody/MakerWorld catalogs, Kickstarter "3d printing × games" category) confirms: the volume is inserts, organizers, minis, and accessories — *component replacement*, not games whose play depends on the print. Nobody owns "the game that had to be printed."
2. **The winning axis is the mechanism**: "a geared orbit · a sagging chain · a swiveling counterweight · an interlocking edge · a hidden baffle · a descending escapement… When the mechanism IS the game, the print is load-bearing." Mechanical precedent that mechanism-play sells at scale: Mouse Trap (1963, Rube Goldberg machine as the toy), Gravitrax (system of printed-grade physics parts), Jenga/Klask/Loopin' Louie (single polished physical verb), Turing Machine's punch-card verifier (2022 — a physical computation device inside a hit deduction game). What 3D printing adds over injection molding: **toleranced assemblies in quantity one** (GYRE's four counter-rotating rings), **per-copy unique hidden geometry** (ORACLE's baffle — impossible to mass-produce *and* keep secret), **calibrated compliance** (CATENARY's chains that genuinely sag and snap), and **rules engraved in physical form** (INTERLOCK's edge profiles). Cardboard can't feel weight; molds can't do lot-size-one.
3. **Per-copy uniqueness is the second moat (Axis B).** "Retail games print 5,000 identical copies; we print 1 copy of 5,000 different games." Legacy games (Pandemic Legacy: Season 1 — BGG #1 for years) already proved players prize a copy that is uniquely theirs; AI generation delivers that at manufacture time instead of through play, and powers the remix marketplace (bounded-lineage creator cuts).
4. **Discipline that keeps prints honest** (PLAYTEST.md, all four rules): paper first ("if it's not fun in paper, printing won't fix it"); **print the wound** — print only the ONE mechanism the game stands on, prove the physics before the parts; blind every round; one change at a time. Print budget opens only on a demonstrated design question (e.g., ORACLE: "open the print budget only when two layouts can share an exit histogram").
5. **Rosewater cross-checks:** #2 aesthetics (layer lines are acceptable *because* mechanics are the point — "nobody minds a slightly rough piece" when the mechanism amazes; but the mechanism's *action* must feel great — that's the aesthetic surface); #12 (never print to prove the printer can); #13 (self-play audit: the winning line must run through the printed mechanism — see §2.2 coverage).
6. **Economic frame:** functional $40–80 corner, single ~200 mm bed, 10–20 h machine time per game (per-game specs in ten-new-games-2026.md: $39.99–$54.99, est. 10–20 h print). Evaluator must include printability/cost gates alongside fun gates: bed fit, print hours, assembly count, tolerance risk — a 9/10-fun unprintable game scores 0.

### Bob's evaluator stack (synthesis)

```
GATE 0  Legality/simulability      rules complete, engine-implementable, ends properly (Completion ≈ 1.0)
GATE 1  GAVEL floor (harmonic mean) balance 45–55% · decisiveness (draws <10%) · agency (~every turn a choice) ·
                                    coverage (board AND printed mechanism on the winning line) · completion
GATE 2  Depth ladder (RAPP/Lantz)   random < greedy < αβ < MCTS, monotone, 60–75% per rung;
                                    degenerate-specialist probes lose
SCORE 3 Browne aesthetics           drama (winner trailed), 1–3 lead changes, late uncertainty,
                                    killer moves scarce-but-present, permanence, duration distribution in band
SCORE 4 LLM table playtest          personas; mine transcript for confusion, downtime, AP, laughter,
                                    "one more game" sentiment; rules-questions count (reinSPQR pattern)
GATE 5  Print-the-wound             one mechanism, ≤200mm bed, ≤20h print, physics proven on paper+golden part
TRUTH   Human blind table           voluntary "can we play again?" ×3 groups = ship;
                                    every human result re-weights SCORE 3/4 (Browne's 57→17, run forever)
```

---

## Source list

- Rosewater, "Twenty Years, Twenty Lessons," GDC 2016 — [GDC Vault](https://gdcvault.com/play/1023186/Twenty-Years-Twenty); columns [Part 1](https://magic.wizards.com/en/news/making-magic/twenty-years-twenty-lessons-part-1-2016-05-30) / [Part 2](https://magic.wizards.com/en/news/making-magic/twenty-years-twenty-lessons-part-2-2016-06-06) / [Part 3](https://magic.wizards.com/en/news/making-magic/twenty-years-twenty-lessons-part-3-2016-06-13)
- Knizia — [ludobits.com quote](https://ludobits.com/quotes/reiner-knizia-on-winning/); [Think Like a Game Designer #52](https://www.thinklikeagamedesigner.com/podcast/2023/09/26think-like-a-game-designer-52-reiner-knizia); [Critical Hits, "Creation of a Successful Game"](https://critical-hits.com/blog/2008/07/03/reiner-knizia-creation-of-a-successful-game/)
- Koster, *A Theory of Fun for Game Design* (2004/2013) — [Goodreads quotes](https://www.goodreads.com/author/quotes/10980.Raph_Koster)
- Browne, "Automatic generation and evaluation of recombination games," QUT PhD 2008 — [QUT ePrints](https://eprints.qut.edu.au/17025/); *Evolutionary Game Design* (Springer 2011) — [review](https://link.springer.com/article/10.1007/s10710-012-9165-6); thesis walkthrough — [Opinionated Gamers 2018-04-23](https://opinionatedgamers.com/2018/04/23/james-nathan-cameron-brownes-automatic-generation-and-evaluation-of-recombination-games/); [Yavalath page](http://cambolbro.com/games/yavalath/)
- Ludii — [arXiv:1907.00240](https://arxiv.org/abs/1907.00240); [Maastricht Digital Ludeme Project](https://www.maastrichtuniversity.nl/news/ancient-games-and-artificial-intelligence)
- GAVEL — Todd et al., NeurIPS 2024, [arXiv:2407.09388](https://arxiv.org/abs/2407.09388)
- RAPP — Nielsen, Barros, Togelius, Nelson, EvoApplications 2015; Lantz et al., "Depth in Strategic Games," AAAI-17 workshop
- Elias, Garfield, Gutschera, *Characteristics of Games*, MIT Press 2012
- Parlett, *The Oxford History of Board Games*, 1999; Murray, *A History of Board-Games Other Than Chess*, 1952; Engelstein & Shalev, *Building Blocks of Tabletop Game Design*, 2019
- Playtesting — [BackerKit: 3 stages of playtesting](https://www.backerkit.com/blog/tabletop-games-crowdfunding-roadmap/playtest/the-3-stages-of-playtesting-internal-local-and-blind/); [Stegmaier interview, Nerds on Earth 2017](https://nerdsonearth.com/2017/06/jamey-stegmaier/)
- House thesis — `/Users/d/code/autonomous-org/projects/vibe/boardgames/ten-new-games-2026.md`, `/Users/d/code/autonomous-org/projects/vibe/boardgames/PLAYTEST.md`
