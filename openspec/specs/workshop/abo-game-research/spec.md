## Purpose

For an abstract game the pieces are the rules, so the game has to be invented before the design's physical facts can be locked. This capability is ABO's researcher: it invents the game from the Wish, proves mechanically that its rules and its box of pieces describe the same game, and returns that as the researched breakdown Concept derives its brief and its images from — so the rules seal into the concept alongside the pixels.

## Requirements

### Requirement: ABO invents the game as its wish research

ABO's research step SHALL satisfy the `wish-research` capability by inventing the game. It receives the round's Wish, ABO's Taste, and the lane blueprint, and returns one researched breakdown describing a complete, original abstract game, from which the round's `ConceptBrief` and every concept image are derived. The breakdown SHALL carry, at minimum: the game's title and its central idea; the seat count it supports; the intended playtime; its complete rules; its component bill; and its art direction expressed in form language — silhouette, relief, chamfer, notch, and pierced feature — rather than in colour or material.

The invention SHALL be shaped by the Wish. If the meaningful content of the Wish can be removed without changing the game's structure, rules, or pieces, ABO has not made the requested product and SHALL NOT return the breakdown as satisfying it.

#### Scenario: A Wish becomes a game

- **WHEN** the researcher runs for an abstract-strategy Wish
- **THEN** it returns one breakdown carrying a title, a central idea, a seat count, a playtime, complete rules, a component bill, and form-language art direction

#### Scenario: The Wish is structural, not decorative

- **WHEN** the breakdown is checked against the Wish
- **THEN** a stated element of the Wish is traceable to the game's structure, rules, board, or pieces
- **AND** a breakdown whose only connection to the Wish is a name or a label is refused

#### Scenario: No colour is assigned

- **WHEN** the art direction is read
- **THEN** every distinction a player must make is carried by shape
- **AND** no rule, component, or art-direction entry depends on colour or material to be playable

### Requirement: Rules declare the components each step touches

Every rule step in the breakdown — setup, turn, end — SHALL declare, by component-bill name, the components that step uses, and the win condition SHALL do the same. A declaration SHALL name components that exist in the bill.

#### Scenario: Every step declares its components

- **WHEN** the rules are read
- **THEN** each setup, turn, and end step carries a list of the bill names it uses
- **AND** the win condition carries the same

#### Scenario: An undeclared component name is refused

- **WHEN** a rule step declares a component name that the bill does not contain
- **THEN** the breakdown is refused

### Requirement: Rules and bill are proved consistent before any brief is derived

The researcher SHALL run a deterministic consistency check over the rules and the component bill before returning, and SHALL NOT return a breakdown that fails it. The check SHALL be mechanical and SHALL involve no model judgement. It SHALL fail when a rule reaches for a component the bill does not contain, when the bill contains a component no rule uses, or when the design exceeds a complexity ceiling the breakdown itself declares.

A failure SHALL be reported as a truthful refusal naming each finding. It SHALL NOT be reported as a passing breakdown with a warning attached.

#### Scenario: A rule reaches for a piece that is not in the box

- **WHEN** a rule step uses a component absent from the bill
- **THEN** the check fails and names that step and that component
- **AND** no brief is derived

#### Scenario: The box contains a piece no rule uses

- **WHEN** the bill contains a component that no setup, turn, end, or win step declares
- **THEN** the check fails and names that component

#### Scenario: The declared complexity ceiling is exceeded

- **WHEN** the design exceeds the rule-length or action-type ceiling its own breakdown declares
- **THEN** the check fails
- **AND** the finding is distinguished from an ambiguity finding, because the design must subtract rather than be described more carefully

#### Scenario: A passing check is recorded, not asserted

- **WHEN** the check passes
- **THEN** its result is recorded with the breakdown as evidence that the check ran
- **AND** the recorded result names the exact rules and bill it was computed over

### Requirement: The component bill is the concept's component breakdown

The components in the breakdown SHALL be the game's actual physical pieces, at the granularity Make will build and the box will contain, and they SHALL become the `ConceptBrief`'s components. Where two component families differ only in a surface motif, each SHALL still be named separately, because a player must tell them apart by shape.

A component SHALL carry the quantity the game requires.

#### Scenario: The brief's components are the game's pieces

- **WHEN** the brief is derived from the breakdown
- **THEN** its components correspond one-to-one with the bill's components
- **AND** the exploded-view check runs against that same set

#### Scenario: Motif variants are named separately

- **WHEN** two piece families share a body and differ only in relief motif
- **THEN** both appear in the bill as distinct components with their own quantities

#### Scenario: A single-component game is legitimate only when researched

- **WHEN** the breakdown returns exactly one component
- **THEN** it is accepted only where the research concluded the game is one physical part
- **AND** it is not accepted as a default that was never decided

### Requirement: Every stated fact is attributable

Each physical fact and each design fact the breakdown states SHALL be attributable, either to a source the researcher recorded or to a decision recorded with its reason. A fact carrying neither SHALL be refused.

Where the Wish or a prior-art search left a dimension, ratio, or quantity unstated, the breakdown SHALL record it as ABO's own decision and say why that value was chosen, rather than presenting it as though it came from somewhere.

#### Scenario: A sourced fact names its source

- **WHEN** the breakdown states a fact taken from a source
- **THEN** that fact names the recorded source it came from

#### Scenario: A decided fact names its reason

- **WHEN** the breakdown states a value the Wish and its sources did not supply
- **THEN** that fact is recorded as a decision with the reason it was chosen

#### Scenario: An unattributed number is refused

- **WHEN** the breakdown states a dimension with neither a source nor a recorded decision
- **THEN** the breakdown is refused

### Requirement: The rules are sealed into the concept

The rules, the bill, and the consistency-check result SHALL be sealed inside the concept root alongside the images and the research, so that the concept hash covers the game as well as the pixels. Editing any of them after the concept is sealed SHALL invalidate the round.

The rules SHALL be sealed as the game record itself, not paraphrased into the brief's prose fields. The brief's own fields remain what they are — the design's physical facts — and a reader SHALL be able to recover the exact rules the images and the bill were drawn from.

#### Scenario: The concept hash covers the rules

- **WHEN** a sealed concept is produced from an ABO breakdown
- **THEN** the rules, the bill, and the check result are inside the sealed concept root
- **AND** the concept hash changes if any of their bytes change

#### Scenario: The exact rules are recoverable

- **WHEN** a sealed concept is read
- **THEN** the complete rules and component bill are recoverable from it verbatim

#### Scenario: Rules edited mid-round fail the round

- **WHEN** the sealed rules change between Concept returning and Make returning
- **THEN** the round fails on the concept seal re-check

### Requirement: A refining round revises the standing game rather than inventing a new one

Where a round is refining an existing design in response to Playtest feedback, the researcher SHALL revise the standing game and SHALL NOT invent an unrelated one. Research SHALL run once per run; a refining round reuses the standing research and folds the feedback into it.

#### Scenario: Feedback revises the standing game

- **WHEN** a round runs with Playtest feedback against a standing game
- **THEN** the returned breakdown is a revision of that game
- **AND** the feedback that caused the revision is recorded against the change it produced

#### Scenario: Research does not repeat

- **WHEN** a second round runs within one run
- **THEN** the standing research is reused rather than researched again
