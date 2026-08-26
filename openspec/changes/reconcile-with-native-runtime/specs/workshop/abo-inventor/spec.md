## ADDED Requirements

### Requirement: ABO is a declarative invented-games Inventor bundle

The Workshop SHALL carry an inventor identified as `abo`, named Abstract Boardgame Oracle, whose folder is named for that id. Its manifest SHALL be schema v7 and SHALL declare exactly one capability — the lane `invented-games` — alongside its identity, its status, its source, and a hash-bound inventory of its extensions.

ABO owns no product contract and no evidence contract, because an inventor is declarative data: it contributes taste and specialist instruction, and the host runs every stage the same way for every inventor. ABO's extensions are static bytes the host fingerprints and makes available to the native session; the host never imports or executes them, and there is no entry point to run.

The manifest SHALL declare only operational facts. ABO's creative identity and routing description SHALL live only in its `TASTE.md`, so the two files cannot disagree. Its folder SHALL contain only its manifest, its Taste, its skills directory, and an optional README; any other entry SHALL fail the contribution check.

The Workshop SHALL own Concept, Make, Playtest, Release, Deliver, artifact identity, evidence binding, the runtime, and the round allowance for ABO exactly as for every other inventor.

#### Scenario: The materialized bundle is discovered and hash-verified

- **WHEN** the Workshop discovers inventors under the inventors root
- **THEN** `abo` is found with both an `inventor.json` and a `TASTE.md`
- **AND** every declared extension tree is re-fingerprinted and matches its recorded `artifact_sha256`
- **AND** discovery and verification need no model credential, no network, no printer, and no carrier

#### Scenario: The manifest carries no creative prose

- **WHEN** `inventors/abo/inventor.json` is read
- **THEN** it contains schema version, identity, status, capabilities, source, and extensions only
- **AND** it contains no routing description, taste statement, or creative policy
- **AND** it declares no entry point, profile, or executable contract

#### Scenario: Exactly one lane capability

- **WHEN** ABO's declared capabilities are checked
- **THEN** they are exactly one lane, `invented-games`
- **AND** a manifest declaring a second capability is refused

#### Scenario: Exactly one abo-inventor extension

- **WHEN** ABO's extension inventory is read
- **THEN** exactly one record is named `abo-inventor`
- **AND** every record's name begins with `abo-` and resolves to `skills/<name>`
- **AND** the skills directory contains those declared skills and nothing else

#### Scenario: The folder contains only the four permitted entries

- **WHEN** `inventors/abo` is listed
- **THEN** it contains only `inventor.json`, `TASTE.md`, `skills`, and an optional `README.md`
- **AND** any other entry fails the contribution check, naming it

## MODIFIED Requirements

### Requirement: ABO's taste is abstract structure, and it says what it refuses

ABO's `TASTE.md` SHALL open with bounded YAML frontmatter carrying only a `name` and a `description`, in that order, and that description SHALL read as a selection boundary — naming both what should choose ABO and the nearest work it must refuse.

The Taste body SHALL commit to, at minimum: abstract structure over theme; a low ceiling on distinct piece types, with a stated reason that component count is a learnability cost a mechanically clean design does not excuse; depth bought by combinatorial structure rather than by an additional action type; distinction carried by shape — footprint, height, relief, notch count, pierced holes, silhouette — because no colour or material is assigned anywhere in the pipeline; a preference for perfect information over hidden information and heavy luck, stated as a preference rather than a ban; and the skill ladder as the operative test of "hard to master".

Taste is direction and SHALL NOT be admissible as evidence. A statement of quality in `TASTE.md` SHALL NOT pass a Playtest result, substitute for a Deliver receipt, or stand in for a customer Review.

#### Scenario: The catalog indexes only the header

- **WHEN** the host builds the persona catalog over a roster containing ABO
- **THEN** only ABO's `name` and `description` are read from its Taste
- **AND** the Taste body is loaded only for the inventor Match selects

#### Scenario: Taste cannot rescue a failed result

- **WHEN** a Playtest result fails and ABO's Taste asserts the design is good
- **THEN** the run does not pass, and the assertion is not recorded as evidence

### Requirement: ABO and the personalized-games inventor are separable within one lane

ABO SHALL share the `invented-games` lane with Leo, the bundled personalized-games inventor, without either absorbing the other's work. ABO's Taste SHALL refuse a Wish whose meaningful content is a person, a relationship, a place, a memory, or a private reference that must survive into the object — that Wish belongs to Leo, whose Taste requires exactly that. Leo's Taste already refuses a stock or classic game with cosmetic personalization.

A lane does not decide who may be considered. Match SHALL rank the whole roster for every Wish, and a lane's only mechanical effect SHALL be selecting the Playtest checks its blueprint requires — for `invented-games`, the game simulation check. The boundary between ABO and Leo is therefore carried by Taste and by the recorded rationale for the ranking, not by routing, and neither inventor SHALL be handed a Wish on the grounds that its lane matched.

Adding ABO SHALL NOT modify Leo's Taste, manifest, extensions, or status.

#### Scenario: An abstract Wish reaches ABO

- **WHEN** a Wish asks for a two-player abstract strategy game that is quick to teach and hard to master, naming no person or personal reference
- **THEN** ABO accepts it under its Taste
- **AND** the ranking records why it was placed above Leo

#### Scenario: A personal Wish is refused by ABO

- **WHEN** a Wish asks for a game built around the recipient's household, their in-jokes, or their shared history
- **THEN** ABO's Taste rejects it and says so
- **AND** no selection forces it onto ABO because the lane matched

#### Scenario: The lane does not narrow the ranking

- **WHEN** Match ranks inventors for any Wish
- **THEN** the ranking covers every inventor in the roster exactly once, whatever their lane
- **AND** ABO's position is justified by its Taste, not by lane membership

#### Scenario: The existing inventor is unchanged

- **WHEN** Leo's Taste hash, manifest, and declared extensions are compared before and after ABO is added
- **THEN** all are identical

### Requirement: The imported tree is reviewed, byte-locked provenance

ABO is built from an external snapshot, and its provenance SHALL be recorded where an offline check can settle it in bytes. Its manifest SHALL declare `source.kind=upstream-snapshot` naming the source repository, the exact pinned commit, and the date of import. Each declared extension SHALL carry the canonical fingerprint of its own tree, so the imported bytes are pinned by the same mechanism that pins every other inventor's — the manifest is the lock, and no separate snapshot lock file SHALL be reintroduced beside it.

An `UPSTREAM.md` SHALL record the licence, what was imported, and what was deliberately not imported. It SHALL travel inside the extension tree, under the primary skill's references, because the inventor folder itself admits only the manifest, the Taste, the skills directory, and an optional README — which also means the provenance record is covered by the same fingerprint as the bytes it describes.

A vendored file SHALL NOT be edited in place without updating the declared fingerprint and the provenance record in the same change.

#### Scenario: The lock proves the imported tree

- **WHEN** ABO's bundle is loaded
- **THEN** each declared extension tree is re-fingerprinted and matched against the `artifact_sha256` its manifest records
- **AND** the check needs no network access

#### Scenario: A silent edit is caught

- **WHEN** any byte of a vendored file under ABO changes without a corresponding manifest update
- **THEN** the materialized tree's fingerprint differs from the declared one and the bundle is refused

#### Scenario: The manifest names the snapshot

- **WHEN** ABO's manifest source is read
- **THEN** its kind is `upstream-snapshot`
- **AND** it names the repository, the full commit, and the import date

#### Scenario: Provenance names what was left behind

- **WHEN** ABO's `UPSTREAM.md` is read
- **THEN** it names the upstream repository, the pinned commit, and the licence
- **AND** it lists the upstream components deliberately not imported, with the reason each one has no place in a Wish-driven Workshop run

### Requirement: ABO is request-driven and never schedules itself

ABO SHALL receive one assignment, do that work, and return. This now follows from what an inventor is: its extensions are static bytes the host fingerprints and never imports, and inventor-supplied code SHALL NOT launch an agent, schedule a prompt, choose a lifecycle transition, pass or waive a gate, read a credential, or perform an external effect. ABO's deterministic tools may compute for the native session that invokes them; only the native session may think, and only the host may decide what happens next.

ABO SHALL NOT poll for work, maintain a queue of ideas across runs, hold a lease on an idea between runs, hold a run open for a human approval, or send an approval request to an external messaging channel. The bounded round allowance the host records on the run SHALL be the only budget governing how many times ABO's design may be improved.

#### Scenario: Inventor bytes cannot start anything

- **WHEN** ABO's extensions are loaded for a run
- **THEN** the host fingerprints them and makes them available to the native session
- **AND** it imports and executes none of them itself
- **AND** nothing shipped under ABO launches an agent, chooses a transition, or waives a gate

#### Scenario: No persistent queue

- **WHEN** an ABO run completes or stops
- **THEN** no cross-run queue state, claim, or lease survives it
- **AND** a subsequent run begins from its own assignment alone

#### Scenario: The allowance is the only budget

- **WHEN** an ABO run exhausts the round allowance recorded on it without passing
- **THEN** the run stops truthfully at that boundary
- **AND** no separate repair, rework, or clarification budget grants it a further round

#### Scenario: Wish text cannot buy rounds

- **WHEN** a Wish's objective text asks for more playtest rounds or more simulated games
- **THEN** the allowance is unchanged

### Requirement: A missing capability parks the run truthfully

Where a capability an ABO run needs is not configured, the run SHALL be recorded as waiting with a typed need naming that capability and what would satisfy it, and SHALL NOT substitute a default, a fixture, or an assertion for it.

Concept is the first place this bites: with the image capability unconfigured, the run SHALL park at `concept`, before any geometry exists. ABO's own Make SHALL never be invoked, because ABO has no Make of its own — Make is a shared stage the host runs identically for every inventor, and what ABO brings to it is Taste and instruction, not a contract.

#### Scenario: Concept parks before Make is reached

- **WHEN** an ABO run reaches Concept with no image capability configured
- **THEN** the run is recorded as waiting at `concept` with a need naming that capability
- **AND** no Make turn runs for that round
- **AND** no placeholder concept is sealed in place of one that was never drawn

#### Scenario: The model seats are absent

- **WHEN** Playtest is reached and the capability that supplies distinct model seats is unavailable
- **THEN** the run is recorded as waiting with a need naming that capability
- **AND** it does not report a passing `agent-playtest` result built from scripted policies alone
- **AND** no endpoint of ABO's own is consulted, because ABO configures no model seat

#### Scenario: There is no ABO Make to invoke

- **WHEN** an ABO run reaches Make
- **THEN** the shared Make stage runs under the same packet and the same gate as for every other inventor
- **AND** no ABO-owned product contract is called

## REMOVED Requirements

### Requirement: ABO is an invented-games inventor at the maximum customization level

**Reason**: There is no customization level. The `custom-make` / `custom-playtest` ladder and the owned `MakeContext -> Made` and `PlaytestContext -> Playtested` contracts it named do not exist: an inventor is now declarative data with exactly one lane capability and a hash-bound extension inventory, and the host runs every stage identically for every inventor. The v5 manifest, its twelve capability strings, and its executable entry point are all gone with it.

**Migration**: Replaced by "ABO is a declarative invented-games Inventor bundle", which restates ABO's identity against the schema-v7 shape — one lane capability, one primary `abo-inventor` extension, the four permitted folder entries, no creative prose in the manifest, and discovery with hash verification in place of a declared entry point that runs.
