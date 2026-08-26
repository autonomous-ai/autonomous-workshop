## Purpose

ABO's Playtest is the half of the lane nothing in this repository could previously satisfy: executable seeded games in the thousands, model-driven seats that report what a scripted policy cannot, and deterministic manufacturing measurement — all bound to the exact revision they tested, and all returned as findings a later round can act on rather than as a score.

## ADDED Requirements

### Requirement: ABO returns every result its lane requires

ABO's Playtest SHALL return a result for each capability the `invented-games` blueprint requires of the Playtest job, at minimum `agent-playtest`, `game-simulation`, `mechanical-test` and `print-test`. Every passing result SHALL be `evidence_class=ai-simulation`, SHALL name its evaluator and that evaluator's exact version, and SHALL reference sealed evidence by hash.

A required result that is missing, malformed, stale, timed out, or of the wrong evidence class SHALL NOT pass.

#### Scenario: All four results are present

- **WHEN** ABO's Playtest completes a round
- **THEN** it returns results identified as `agent-playtest`, `game-simulation`, `mechanical-test` and `print-test`

#### Scenario: A missing result blocks Instructions

- **WHEN** a required result is absent from the returned evidence
- **THEN** the run returns a `Need` naming that capability
- **AND** Instructions does not begin

#### Scenario: The wrong evidence class does not pass

- **WHEN** a passing result declares an evidence class other than AI simulation
- **THEN** the run returns a `Need` for that capability

#### Scenario: Evidence is bound to the exact revision

- **WHEN** any result is checked against the revision it tested
- **THEN** its artifact hash equals that revision's hash
- **AND** a result carrying a different hash is refused

### Requirement: The simulation gate is a thousand completed games, not a thousand attempts

`game-simulation` SHALL NOT pass on fewer than 1,000 **completed** games. A game abandoned at a turn cap, abandoned at a deadline, or ended by an engine error SHALL NOT be counted toward that total. The result SHALL report the completed count, the seeds used, and the count of games that did not complete, separately.

Where the simulation reaches its time budget before 1,000 games complete, the round SHALL return a truthful `Need` reporting how far it got. It SHALL NOT return a passing result over a smaller sample.

#### Scenario: A thousand completed games pass the floor

- **WHEN** at least 1,000 seeded games run to a terminal state
- **THEN** the result reports that completed count and may pass

#### Scenario: Abandoned games do not count

- **WHEN** games are abandoned at the turn cap
- **THEN** they are reported separately and excluded from the completed count

#### Scenario: A short run waits rather than passes

- **WHEN** the deadline is reached with fewer than 1,000 completed games
- **THEN** the run returns a `Need` naming `game-simulation` and reporting the completed count
- **AND** no passing simulation result is returned

#### Scenario: The sample is reproducible

- **WHEN** the simulation is re-run from the recorded seeds against the same engine bytes
- **THEN** it reproduces the same games

### Requirement: Four player styles, each with a policy that actually plays

`game-simulation` SHALL declare the four player styles `optimizing`, `social`, `exploratory` and `adversarial`, and each declared style SHALL be backed by a policy that executed games in the reported sample. A style SHALL NOT be declared because the lane names it.

The styles SHALL be genuinely distinct: each SHALL choose differently from the others on at least some positions in the sample, and the result SHALL record evidence of that distinctness rather than asserting it.

#### Scenario: Every declared style played

- **WHEN** the declared styles are checked against the sample
- **THEN** each style is attributable to games it played and moves it chose

#### Scenario: An unbacked style is refused

- **WHEN** a style is declared with no executing policy behind it
- **THEN** the result does not pass

#### Scenario: Styles are shown to differ

- **WHEN** the styles are compared over the sample
- **THEN** the result records positions where they chose differently
- **AND** two styles that never diverge are reported as one style, not two

### Requirement: Simulation measures the game, not the model's opinion

`game-simulation` SHALL report measured properties of play, at minimum: whether games terminate; whether any seat holds an unexplained advantage across a balanced sample with seats swapped; the fraction of turns that offered no real choice; how wide the decision space is; which declared move kinds were never legal or never chosen; and whether a stronger policy beats a weaker one by a margin, since a position where lookahead cannot beat greedy is not deep.

Where the engine declared an assumption about an ambiguous rule, the simulation SHALL exercise both readings and report whether the reading changed the outcome.

A turn that no seat ever chose anything at may be excluded from decision measurements only where it is shown, from played games, to have been the sole option everywhere it appeared. The engine's own declaration SHALL NOT be sufficient.

#### Scenario: Non-termination is reported

- **WHEN** games fail to reach a terminal state
- **THEN** the result reports it and the round does not pass on that measurement

#### Scenario: A seat advantage is reported

- **WHEN** one seat wins substantially more across a balanced, seat-swapped sample
- **THEN** the result reports the margin and the direction

#### Scenario: A fake choice is exposed

- **WHEN** a declared move kind is never legal, or is never chosen where it was legal
- **THEN** the result names it

#### Scenario: A declared assumption is played both ways

- **WHEN** the engine declared a reading of an ambiguous rule
- **THEN** the sample includes games played under both readings
- **AND** the result reports whether the reading changed the outcome

#### Scenario: An always-forced move kind must prove itself

- **WHEN** a move kind claimed to carry no decision is observed alongside another legal move
- **THEN** that claim is reported as a contract finding rather than accepted
- **AND** the move kind is counted as a real branch in the decision measurements

### Requirement: Model seats play the game and no part of the harness is an agent

`agent-playtest` SHALL come from games in which each seat's decision is made by an independent model, and SHALL report at least two distinct, non-empty roles. The loop that renders a position, asks the seat whose turn it is, reads back one choice and applies it SHALL be deterministic code.

A seat SHALL choose only from the moves the engine enumerated, SHALL be shown only what that seat is permitted to see, and SHALL have no access to the engine, the evidence, the run's files, or another seat's messages. A seat SHALL NOT be able to answer a rules question on its own behalf, replay a game because the first was dull, or take a turn for another seat.

#### Scenario: Two distinct roles are reported

- **WHEN** `agent-playtest` is returned
- **THEN** it names at least two distinct non-empty roles
- **AND** a result naming one role, or repeating one role, does not pass

#### Scenario: A seat cannot make an illegal move

- **WHEN** a seat returns a choice
- **THEN** it is an index into the moves the engine enumerated for that seat
- **AND** anything else is refused rather than interpreted

#### Scenario: A seat cannot see what it should not

- **WHEN** a seat is prompted in a hidden-information game
- **THEN** it is shown only that seat's permitted view

#### Scenario: The harness holds no tools

- **WHEN** a seat's decision is requested
- **THEN** the request carries the position and the move list and nothing else
- **AND** the seat has no file, engine, or evidence access through which to reach anything further

#### Scenario: A model seat's report is not a fun claim

- **WHEN** a seat reports that a turn had no real decision in it, or that the game became smaller once it was worked out
- **THEN** that is recorded as a simulation finding
- **AND** it is not recorded as evidence that people enjoyed the game

### Requirement: Manufacturing results are deterministic measurement bound to the source closure

`mechanical-test` and `print-test` SHALL come from deterministic measurement over the exact geometry in the revision. The evidence SHALL bind the measured outputs to a hash of the sources they were computed from, so a measurement computed from stale geometry is detectable.

`mechanical-test` SHALL cover, at minimum, solid validity, mesh topology, dimensions against the brief, interference between parts in their declared poses, and clearance at declared fits. `print-test` SHALL cover, at minimum, bed fit for every part, minimum wall thickness, overhang and bridging, and slicing under a pinned printer, material, and profile.

A check that could not be run SHALL be reported as unmeasured, distinctly from a check that ran and passed. An unmeasured check SHALL NOT count as a pass.

#### Scenario: Measurement is bound to its sources

- **WHEN** the manufacturing evidence is checked
- **THEN** it names the source-closure hash it was computed from
- **AND** evidence computed from geometry that has since changed is refused

#### Scenario: A part that does not fit the bed fails

- **WHEN** a part exceeds the pinned printer's usable envelope and is not declared as tiled
- **THEN** `print-test` fails and names that part

#### Scenario: Parts that intersect fail

- **WHEN** two parts intersect in a declared pose where they must not
- **THEN** `mechanical-test` fails and names both parts

#### Scenario: An unrun check is not a pass

- **WHEN** slicing cannot run because no pinned profile is configured
- **THEN** print time and material are reported as unmeasured
- **AND** `print-test` does not pass on the strength of the checks that did run

#### Scenario: Images are not geometry evidence

- **WHEN** a render or preview is present
- **THEN** it is not offered in support of topology, fit, interference, or printability

### Requirement: Findings return as feedback the next round can act on

Every finding that prevents a pass SHALL be returned as structured feedback naming the area, what was observed, the evidence it came from, a severity, and the concrete change the next round should make. A finding addressed to the game SHALL name the rule it is about.

Severity SHALL distinguish a design that must change from a description that must be clearer: a defect in how the game functions, or a failed manufacturing measurement, is blocking; an ambiguity or an incompleteness in the rules is an improvement. Both send the game back through the loop; only the wording of the fix differs.

Where a finding invalidates the design rather than the geometry, the next round SHALL revise the sealed game rather than work around it in the build.

#### Scenario: A finding names its fix

- **WHEN** a result fails
- **THEN** the returned feedback names the area, the finding, the evidence, the severity, and the change to make

#### Scenario: A broken mechanic blocks

- **WHEN** the simulation shows a dominant line, an unreachable ending, or a fake decision
- **THEN** the feedback is blocking and names the rule responsible

#### Scenario: An ambiguity is an improvement, not a block

- **WHEN** the engine could not proceed because a rule was silent
- **THEN** the feedback is an improvement against the rules
- **AND** it still returns the game to the loop

#### Scenario: A design fault is answered in the design

- **WHEN** feedback invalidates the game's structure rather than its geometry
- **THEN** the next round revises the sealed rules and bill
- **AND** it does not compensate for the fault in CAD alone

### Requirement: Playtest never becomes a claim about people

No ABO Playtest result SHALL claim that people understood the game, enjoyed it, or would play it again. Simulated play, model-seat reports, computed geometry, and slicer output SHALL each stay within what they measured. Whether customers want another play is learned after delivery through Reviews.

#### Scenario: Simulation stays simulation

- **WHEN** a passing simulation result is recorded
- **THEN** it claims that seeded games terminated and what was measured in them
- **AND** it makes no claim about human enjoyment

#### Scenario: Slicing is not printing

- **WHEN** slicing succeeds under the pinned profile
- **THEN** the claim is that the meshes sliced under that profile
- **AND** it is not a claim that the game printed or assembled
