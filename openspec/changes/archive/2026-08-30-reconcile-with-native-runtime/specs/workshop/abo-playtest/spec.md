## MODIFIED Requirements

### Requirement: ABO returns every result its lane requires

An ABO run's Playtest stage SHALL seal a check for every id the `invented-games` blueprint requires of that lane — `agent-playtest`, `game-simulation`, `mechanical-test` and `print-test` — each appearing exactly once, with no check the lane did not ask for.

ABO SHALL NOT own a Playtest stage of its own. The shared native Playtest stage produces these checks; ABO contributes the lane's judgment and its declared deterministic tools, and the host's gate decides whether the round passes.

Every check SHALL name a real evaluator and that evaluator's exact version, cite a configuration and an evidence file that both live inside the round's sealed evidence tree, record an explicit UTC observation time, and carry non-empty observations. Self-report is not an evaluator, and prose in a turn's reply is not evidence — a claim with no file behind it cannot be re-checked by anyone.

Every check SHALL be bound to the exact Make revision it tested: the sealed Playtest result carries that revision's identity and its product's content address, and evidence from a superseded revision SHALL NOT be carried forward.

A required check that is missing, malformed, stale, unevidenced, or bound to different bytes SHALL NOT pass. The run SHALL record a need naming that check, and Release SHALL NOT begin.

#### Scenario: All four results are present

- **WHEN** the Playtest stage seals a round for an ABO run
- **THEN** it carries checks identified as `agent-playtest`, `game-simulation`, `mechanical-test` and `print-test`, each exactly once
- **AND** a result missing one of them, or carrying an id the lane did not require, is refused

#### Scenario: A missing result blocks Instructions

- **WHEN** a required check is absent from the sealed evidence
- **THEN** the run records a need naming that check
- **AND** the stage that would write the product's instructions does not begin

#### Scenario: The wrong evidence class does not pass

- **WHEN** a passing check rests on evidence of a class that cannot support the claim it makes — a render offered as topology, a slice offered as a print, a model's opinion offered as measurement
- **THEN** the run records a need for that check

#### Scenario: Prose is not evidence

- **WHEN** a check names self-report as its evaluator, or cites no configuration and evidence file inside the round's sealed evidence tree
- **THEN** it does not pass, and the run records a need for that check

#### Scenario: Evidence is bound to the exact revision

- **WHEN** any check is checked against the revision it tested
- **THEN** the sealed result names that revision's identity and its product's content address
- **AND** a check offered against different product bytes is refused

### Requirement: The simulation gate is a thousand completed games, not a thousand attempts

`game-simulation` SHALL NOT pass on fewer than 1,000 **completed** games. A game abandoned at a turn cap, abandoned at a deadline, or ended by an engine error SHALL NOT be counted toward that total. The sealed evidence SHALL report the completed count, the seeds used, and the count of games that did not complete, separately.

Where the simulation reaches the round's allowance before 1,000 games complete, the run SHALL record a truthful need reporting how far it got. It SHALL NOT seal a passing check over a smaller sample, and it SHALL NOT lower the floor because the allowance ran short. The round allowance is the only budget the simulation has; a turn SHALL NOT grant itself a second one.

The sample SHALL be reproducible: replaying the recorded seeds against the same sealed engine bytes SHALL reproduce the same games.

#### Scenario: A thousand completed games pass the floor

- **WHEN** at least 1,000 seeded games run to a terminal state
- **THEN** the sealed evidence reports that completed count and the check may pass

#### Scenario: Abandoned games do not count

- **WHEN** games are abandoned at the turn cap
- **THEN** they are reported separately and excluded from the completed count

#### Scenario: A short run waits rather than passes

- **WHEN** the round's allowance is reached with fewer than 1,000 completed games
- **THEN** the run records a need naming `game-simulation` and reporting the completed count
- **AND** no passing simulation check is sealed, and the floor is not lowered

#### Scenario: The sample is reproducible

- **WHEN** the simulation is re-run from the recorded seeds against the same sealed engine bytes
- **THEN** it reproduces the same games

### Requirement: Four player styles, each with a policy that actually plays

`game-simulation` SHALL declare the four player styles `optimizing`, `social`, `exploratory` and `adversarial`, and each declared style SHALL be backed by a policy in ABO's deterministic simulation harness that executed games in the reported sample. A style SHALL NOT be declared because the lane names it.

The styles SHALL be genuinely distinct: each SHALL choose differently from the others on at least some positions in the sample, and the sealed evidence SHALL record where they diverged rather than asserting that they did.

These are scripted policies inside a deterministic harness, and they are what `game-simulation` measures. They SHALL NOT be offered in support of `agent-playtest`, which is a claim about a different kind of seat entirely.

#### Scenario: Every declared style played

- **WHEN** the declared styles are checked against the sample
- **THEN** each style is attributable to games it played and moves it chose

#### Scenario: An unbacked style is refused

- **WHEN** a style is declared with no executing policy behind it
- **THEN** the check does not pass

#### Scenario: Styles are shown to differ

- **WHEN** the styles are compared over the sample
- **THEN** the sealed evidence records positions where they chose differently
- **AND** two styles that never diverge are reported as one style, not two

#### Scenario: Scripted policies do not stand in for model seats

- **WHEN** `agent-playtest` cites games played only by the simulation's scripted policies
- **THEN** that check does not pass

### Requirement: Simulation measures the game, not the model's opinion

`game-simulation` SHALL report measured properties of play, at minimum: whether games terminate; whether any seat holds an unexplained advantage across a balanced sample with seats swapped; the fraction of turns that offered no real choice; how wide the decision space is; which declared move kinds were never legal or never chosen; and whether a stronger policy beats a weaker one by a margin, since a position where lookahead cannot beat greedy is not deep.

Each of those measurements SHALL be readable from the evidence file the check cites. A number stated only in a turn's narration is not a measurement, because nothing later in the run can re-read it.

Where the sealed product tree records a declared assumption about an ambiguous rule, the simulation SHALL exercise both readings and report whether the reading changed the outcome.

A turn that no seat ever chose anything at may be excluded from decision measurements only where it is shown, from played games, to have been the sole option everywhere it appeared. The engine's own declaration SHALL NOT be sufficient.

#### Scenario: Non-termination is reported

- **WHEN** games fail to reach a terminal state
- **THEN** the sealed evidence reports it and the round does not pass on that measurement

#### Scenario: A seat advantage is reported

- **WHEN** one seat wins substantially more across a balanced, seat-swapped sample
- **THEN** the sealed evidence reports the margin and the direction

#### Scenario: A fake choice is exposed

- **WHEN** a declared move kind is never legal, or is never chosen where it was legal
- **THEN** the sealed evidence names it

#### Scenario: A measurement with no file behind it does not count

- **WHEN** a required measurement appears in the turn's account but not in the evidence file the check cites
- **THEN** the check does not pass

#### Scenario: A declared assumption is played both ways

- **WHEN** the sealed product tree records a reading of an ambiguous rule
- **THEN** the sample includes games played under both readings
- **AND** the sealed evidence reports whether the reading changed the outcome

#### Scenario: An always-forced move kind must prove itself

- **WHEN** a move kind claimed to carry no decision is observed alongside another legal move
- **THEN** that claim is reported as a finding against the engine's declaration rather than accepted
- **AND** the move kind is counted as a real branch in the decision measurements

### Requirement: Model seats play the game and no part of the harness is an agent

`agent-playtest` SHALL come from games in which each seat's decision is the judgment of the native session or one of its bounded subagents, and SHALL report at least two distinct, non-empty roles — the player perspectives the session actually took. There is no model-seat endpoint to configure and no seat process to schedule: the seats are the session's own bounded judgment, exercised position by position.

The harness around them stays deterministic. ABO's engine and its simulation tool render the position, enumerate the legal moves, restrict the view to what that seat is permitted to see, apply the returned choice, and seal the trace. Nothing in that harness starts a session, schedules a prompt, decides a transition, or passes a gate.

A seat SHALL choose only from the moves the engine enumerated, SHALL be shown only what that seat is permitted to see, and SHALL have no access to the engine, the evidence, the run's files, or another seat's messages. A seat SHALL NOT answer a rules question on its own behalf, replay a game because the first was dull, or take a turn for another seat.

Where the session cannot supply distinct seats — because a capability the check needs is absent — the run SHALL be recorded as waiting at `playtest` with a need naming what is missing. It SHALL NOT seal a passing `agent-playtest` assembled from the simulation's scripted policies, because a scripted policy is precisely what this check exists to be more than.

#### Scenario: Two distinct roles are reported

- **WHEN** `agent-playtest` is sealed
- **THEN** it names at least two distinct, non-empty roles
- **AND** a check naming one role, or repeating one, does not pass

#### Scenario: A seat cannot make an illegal move

- **WHEN** a seat returns a choice
- **THEN** it is an index into the moves the engine enumerated for that seat
- **AND** anything else is refused rather than interpreted

#### Scenario: A seat cannot see what it should not

- **WHEN** a seat is asked to decide in a hidden-information game
- **THEN** it is shown only that seat's permitted view

#### Scenario: The harness holds no tools

- **WHEN** a seat's decision is requested
- **THEN** the request carries the position and the move list and nothing else
- **AND** the seat has no file, engine, or evidence access through which to reach anything further

#### Scenario: A missing seat capability parks the run

- **WHEN** the capability that supplies distinct model seats is unavailable
- **THEN** the run is recorded as waiting at `playtest` with a need naming that capability
- **AND** no passing `agent-playtest` is sealed for that round

#### Scenario: A model seat's report is not a fun claim

- **WHEN** a seat reports that a turn had no real decision in it, or that the game became smaller once it was worked out
- **THEN** that is recorded as a simulation finding
- **AND** it is not recorded as evidence that people enjoyed the game

### Requirement: Findings return as feedback the next round can act on

Every finding that prevents a pass SHALL be sealed as structured feedback naming the area, what was observed, the evidence it came from, a severity, the concrete change the next round should make, and the stages it invalidates. A finding addressed to the game SHALL name the rule it is about.

Severity SHALL distinguish a design that must change from a description that must be clearer: a defect in how the game functions, or a failed manufacturing measurement, is blocking; an ambiguity or an incompleteness in the rules is an improvement. Both send the game back through the loop; only the wording of the fix differs.

A failing verdict SHALL propose a return to Make. The host preserves that exact sealed result as the next round's feedback, advances the bounded round, and invalidates the evidence downstream of the revision that failed. The turn SHALL NOT edit the revision it just tested, and SHALL NOT amend its own sealed evidence to make a round appear to pass.

Where a finding invalidates the design rather than the geometry, the next round SHALL revise the sealed concept rather than work around it in the build.

#### Scenario: A finding names its fix

- **WHEN** a check fails
- **THEN** the sealed feedback names the area, the finding, the evidence, the severity, the change to make, and the stages it invalidates

#### Scenario: A broken mechanic blocks

- **WHEN** the simulation shows a dominant line, an unreachable ending, or a fake decision
- **THEN** the feedback is blocking and names the rule responsible

#### Scenario: An ambiguity is an improvement, not a block

- **WHEN** the engine could not proceed because a rule was silent
- **THEN** the feedback is an improvement against the rules
- **AND** it still returns the game to the loop

#### Scenario: A failing verdict returns to Make and invalidates downstream work

- **WHEN** the round's verdict is not a pass
- **THEN** the run returns to Make in a new round, carrying that sealed result as feedback
- **AND** the evidence downstream of the failed revision is invalidated
- **AND** the failed revision and its sealed evidence are left unedited

#### Scenario: A design fault is answered in the design

- **WHEN** feedback invalidates the game's structure rather than its geometry
- **THEN** the next round revises the sealed concept before Make runs again
- **AND** it does not compensate for the fault in CAD alone
