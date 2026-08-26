## Purpose

Abstract Boardgame Oracle is an `invented-games` inventor whose taste is abstract structure rather than personal reference: a small number of piece types on a rich board, depth from combinatorial complexity rather than from added rules, and every distinction carried by shape because the pipeline assigns no colour. This capability defines its identity, the boundary that separates it from the other inventor in its lane, the provenance of the tree it was built from, and what it waits for when a capability is absent.

## Requirements

### Requirement: ABO is an invented-games inventor at the maximum customization level

The Workshop SHALL carry an inventor identified as `abo`, named Abstract Boardgame Oracle, in the `invented-games` lane, at the `custom-playtest` level — meaning it owns both the product contract (`MakeContext -> Made`) and the evidence contract (`PlaytestContext -> Playtested`). Its manifest SHALL be schema v5 and SHALL declare only operational facts; its creative identity and routing description SHALL live only in its `TASTE.md`, so the two files cannot disagree.

Workshop SHALL continue to own Concept's job seam, Instructions, Deliver, artifact identity, evidence binding, runtime, and the improvement loop for ABO exactly as for every other inventor.

#### Scenario: The inventor is discoverable and runnable

- **WHEN** the Workshop discovers inventors under the inventors root
- **THEN** `abo` is found with both an `inventor.json` and a `TASTE.md`
- **AND** its declared entry point runs and its declared checks pass without a model credential, a network, a printer, or a carrier

#### Scenario: The manifest carries no creative prose

- **WHEN** `inventors/abo/inventor.json` is read
- **THEN** it contains identity, status, entry point, capabilities, checks, and source only
- **AND** it contains no routing description, taste statement, or creative policy

#### Scenario: Custom Playtest implies custom Make

- **WHEN** ABO's declared capabilities are checked
- **THEN** they include both `custom-make` and `custom-playtest`

### Requirement: ABO's taste is abstract structure, and it says what it refuses

ABO's `TASTE.md` SHALL open with bounded YAML frontmatter carrying only a `name` and a `description`, and that description SHALL read as a selection boundary — naming both what should choose ABO and the nearest work it must refuse.

The Taste body SHALL commit to, at minimum: abstract structure over theme; a low ceiling on distinct piece types, with a stated reason that component count is a learnability cost a mechanically clean design does not excuse; depth bought by combinatorial structure rather than by an additional action type; distinction carried by shape — footprint, height, relief, notch count, pierced holes, silhouette — because no colour or material is assigned anywhere in the pipeline; a preference for perfect information over hidden information and heavy luck, stated as a preference rather than a ban; and the skill ladder as the operative test of "hard to master".

Taste is direction and SHALL NOT be admissible as evidence. A statement of quality in `TASTE.md` SHALL NOT pass a Playtest result, substitute for a Deliver receipt, or stand in for a customer Review.

#### Scenario: The catalog indexes only the header

- **WHEN** the Manager builds its catalog over a roster containing ABO
- **THEN** only ABO's `name` and `description` are indexed
- **AND** the Taste body is loaded only if ABO reaches the finalist shortlist

#### Scenario: Taste cannot rescue a failed result

- **WHEN** a Playtest result fails and ABO's Taste asserts the design is good
- **THEN** the run does not pass, and the assertion is not recorded as evidence

### Requirement: ABO and the personalized-games inventor are separable within one lane

ABO SHALL share the `invented-games` lane with the bundled personalized-games inventor without either absorbing the other's work. ABO's Taste SHALL refuse a Wish whose meaningful content is a person, a relationship, a place, a memory, or a private reference that must survive into the object — that Wish belongs to the inventor whose Taste requires it. The other inventor's Taste already refuses a stock or classic game with cosmetic personalization.

Adding ABO SHALL NOT modify the other inventor's Taste, profile, seams, or status.

#### Scenario: An abstract Wish reaches ABO

- **WHEN** a Wish asks for a two-player abstract strategy game that is quick to teach and hard to master, naming no person or personal reference
- **THEN** ABO accepts it under its Taste
- **AND** the ranking records why it beat the other lane finalist

#### Scenario: A personal Wish is refused by ABO

- **WHEN** a Wish asks for a game built around the recipient's household, their in-jokes, or their shared history
- **THEN** ABO's Taste rejects it and says so
- **AND** the Manager does not force it into ABO because the lane matched

#### Scenario: The existing inventor is unchanged

- **WHEN** the bundled personalized-games inventor's Taste hash and profile are compared before and after ABO is added
- **THEN** both are identical

### Requirement: The imported tree is reviewed, byte-locked provenance

ABO is built from an external snapshot. Its folder SHALL carry an `UPSTREAM.md` recording the source repository, the exact pinned commit, the date of import, the licence, and what was deliberately not imported. Its manifest SHALL declare `source.kind=upstream-snapshot`, and the repository's snapshot lock SHALL record the imported tree's canonical fingerprint so an offline check proves it byte-for-byte.

A vendored file SHALL NOT be edited in place without updating that lock and the provenance record in the same change.

#### Scenario: The lock proves the imported tree

- **WHEN** the repository's snapshot lock verification runs
- **THEN** it computes ABO's imported tree fingerprint and matches it against the recorded value
- **AND** the check requires no network access

#### Scenario: A silent edit is caught

- **WHEN** any byte of a vendored file under ABO changes without a corresponding lock update
- **THEN** snapshot lock verification fails

#### Scenario: Provenance names what was left behind

- **WHEN** `inventors/abo/UPSTREAM.md` is read
- **THEN** it names the upstream repository and commit
- **AND** it lists the upstream components deliberately not imported, with the reason each one has no place in a Wish-driven six-job Workshop

### Requirement: ABO is request-driven and never schedules itself

ABO SHALL receive one assignment, do that work, and return. It SHALL NOT poll for work, maintain a queue of ideas across runs, hold a lease on an idea between runs, hold a run open for a human approval, or send an approval request to an external messaging channel. The bounded `playtest_rounds` allowance recorded with the Wish SHALL be the only budget governing how many times ABO may improve a game.

#### Scenario: No persistent queue

- **WHEN** an ABO run completes or stops
- **THEN** no cross-run queue state, claim, or lease survives it
- **AND** a subsequent run begins from its own assignment alone

#### Scenario: The allowance is the only budget

- **WHEN** an ABO run exhausts its `playtest_rounds` allowance without passing
- **THEN** the run stops truthfully at that boundary
- **AND** no separate repair, rework, or clarification budget grants it a further round

#### Scenario: Wish text cannot buy rounds

- **WHEN** a Wish's objective text asks for more playtest rounds or more simulated games
- **THEN** the allowance is unchanged

### Requirement: A missing capability parks the run truthfully

Where a capability ABO needs is not configured, the run SHALL stop with a typed `Need` naming that capability and what would satisfy it, and SHALL NOT substitute a default, a fixture, or an assertion for it. This applies to the shared Concept capabilities the run reaches first and to ABO's own model-seat endpoint.

#### Scenario: Concept parks before Make is reached

- **WHEN** an ABO run starts with no researcher, image provider, or exploded-view check configured
- **THEN** the run parks at Concept with a `Need` for each missing capability
- **AND** ABO's Make is never invoked

#### Scenario: The model seats are absent

- **WHEN** Playtest is reached with no model-seat endpoint configured
- **THEN** the run returns a `Need` for that capability
- **AND** it does not report a passing `agent-playtest` result built from scripted policies alone
