# Blindcap: Duel — design review loop 01

This review applies the public analytical frames around four board-game design books. It does not pretend that a publisher description is a substitute for reading the books, and it does not quote or reproduce their text.

## What the game is asking players to learn

Blindcap has one central learning object: convert a physical two-bit reading into a theory about the rival field, then decide whether that theory is worth a scarce crown. The same information affects three systems at once:

- **Deduction:** which of four species is under a cap?
- **Network building:** where can my known mushrooms extend that hidden grove?
- **Commitment:** is this grove valuable enough to crown before I know everything?

That is a coherent pattern-recognition loop rather than three unrelated mechanisms. The physical read is not a toy pasted onto the game; it changes the player's model of the board and therefore the next plant or claim.

## Player-centric characteristics

| Trait | Current evidence | Gate |
| --- | --- | --- |
| Players | Exactly two; no kingmaking or downtime between other players | Pass |
| Chance | Random opening starter only; uncertainty comes from an opponent's choices | Pass, subject to human opening study |
| Skill | Greedy policy beat random in 90% of 60 rotated games | Promising, not human evidence |
| Agency | Median legal branching factor 8.0; no forced turns in the 400-game run | Pass digitally |
| Effort | Four-species code, grove scoring, contest rule and a five-step tie chain | Human comprehension test required |
| Reward | Every main turn plants one object and makes one tactile probe-or-crown decision | Strong if the probe is satisfying |
| Duration | Fixed arc: simultaneous seed, five main rounds, closing crown, harvest | Pass digitally; verify 25 minutes at table |
| Interaction | Players probe and crown only rival mushrooms while using their own known mushrooms to shape shared groves | Strong and legible in the rules |

## Mechanism audit

The game combines hidden information, constrained action selection, network/connection scoring, ownership markers, and commitment before reveal. Each mechanism has one job:

- Hidden species create the deduction problem.
- Visible ownership prevents the hidden layer from swallowing spatial strategy.
- Three probes price information.
- Three crowns price commitment.
- Orthogonal groves make planting matter after a mushroom leaves the tray.
- Contested scoring gives the other player counterplay after a claim becomes visible.

Nothing currently deserves removal on redundancy grounds. The five-step tie chain is the least elegant part: largest uncontested grove, followed by four recorded probe counts. Those comparisons use evidence players deliberately created, are seat-neutral, and reduced competent shared wins from roughly 44% to 8.5%. Put the chain on the scoring aid; do not expect first-time players to memorize it.

## Current risks

### P0 — physical truth

The game does not exist until the printed reader has two unmistakable, repeatable outcomes without exposing the species. A digital solid check is necessary but not sufficient. Any ambiguous probe, cross-talk between the two channels, visible hidden feature, or fit that changes with print variation kills the current mechanism.

### P1 — score legibility

`n²`, contested `n`, and a double-value species are learnable but create arithmetic at the most fragile moment: harvest. The product needs a one-card scoring aid with worked grove examples. Do not add a new scoring rule; make the existing rule visible.

### P1 — deduction may feel thinner than it simulates

Three probes create scarcity, but a player can spend only three bits in a field of six rival mushrooms. The remaining value comes from reading the rival's planting pattern and using one's own known species to extend or interrupt groves. Blind human play must confirm that players actually form those theories rather than crown randomly and wait for harvest.

### P1 — the tactile reward carries the whole product

The game has little chance, spectacle or narrative outside the object itself. That is a strength only if inserting a probe is smooth, the two outcomes are obvious across the table, and the harvest reveal feels earned. A mediocre fit turns a focused design into a dry optimization exercise.

### P2 — first-game memory load

The four-species code and main scoring rule should live on the two tray backs. The complete tie chain belongs on the scoring aid and in the rules, not on the board. This lowers effort without changing a decision.

## Three improvements that preserve the validated core

1. **Make the trays teach.** Emboss the four two-bit species patterns and the grove scoring examples on the player-facing tray walls. This reduces lookup effort while keeping hidden information private.
2. **Stage the first probe in setup.** The rules should include one out-of-game demonstration on a fit coupon before the first match, so both players learn the two physical outcomes without revealing a live mushroom.
3. **Make harvest procedural.** The scoring aid now records four public probe counts before pin removal, then numbers the physical sequence: withdraw probes, invert each stool in its original cell, preserve crown ownership, trace groves, and score. This protects both the reveal and the earned tiebreak evidence without pretending an admitted probe can remain through the shank during removal.

## Decision

The digital design earns a physical prototype. It does not yet earn a public listing. Keep the fixed five-round arc, the three-probe/two-early-crown constraint, the network scoring, and the earned neutral tie chain. Spend the next iteration on a printed fit coupon and blind human evidence—not another mechanism.

## Public sources used for this loop

- MIT Press describes *Characteristics of Games* as a player-centric framework comparing player count, rules, luck, skill, and reward-to-effort: <https://mitpress.mit.edu/9780262542692/characteristics-of-games/>
- CRC Press describes *Building Blocks of Tabletop Game Design* as a categorized reference of mechanisms and their design uses: <https://www.routledge.com/Building-Blocks-of-Tabletop-Game-Design-An-Encyclopedia-of-Mechanisms/Engelstein-Shalev/p/book/9781032015811>
- Raph Koster describes *A Theory of Fun for Game Design* as an exploration of engagement through pattern recognition and learning: <https://www.raphkoster.com/about-raph/>
- *GameTek* is used here only as a standing mandate to test probability, incentives and psychology with measurements; no book text is reproduced.
