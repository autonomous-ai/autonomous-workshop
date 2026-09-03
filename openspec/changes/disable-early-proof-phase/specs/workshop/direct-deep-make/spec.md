## ADDED Requirements

### Requirement: New deep runs freeze a direct Make profile
New Codex Forge and Quest runs SHALL freeze an immutable capability that preserves current deep Invent behavior, 256,000-token automatic compaction, later-stage economics, one Wish-wide session, one Goal per active stage, bounded recovery, and the eight-turn invocation cap while starting Make at high reasoning with the ordinary 60-minute boundary.

#### Scenario: A new Forge run is created
- **WHEN** the host creates a new Codex Forge run
- **THEN** its immutable inputs contain the current direct-deep capability
- **AND** the first Make turn uses high reasoning, 256,000-token compaction, the ordinary 60-minute boundary, and `agent-outcome.json`
- **AND** the turn receives final-product Make instructions rather than early-proof instructions

#### Scenario: A direct run resumes
- **WHEN** a run frozen on the direct capability resumes during Make
- **THEN** the host retains direct behavior without inserting an early-proof or source-handoff phase

### Requirement: Current deep Make has no early-proof protocol
The current deep profile SHALL NOT require `review/early-proof/`, `proof.py`, proof state entries, early held or signature renders, `finding.json`, `.make-proof-ready.json`, or a private proof-acceptance receipt. The only native file marker that can complete the direct Make Goal SHALL be the normal checkpoint-bound `agent-outcome.json` written through the Make finalizer.

Absence of early-proof files or host proof receipts SHALL NOT block current-profile Make progress, recovery, finalization, or explicit operator resume.

#### Scenario: Current Make begins without proof artifacts
- **WHEN** direct-profile Make begins with no historical proof residue
- **THEN** the host neither requests nor waits for an early-proof marker
- **AND** no proof receipt is created

#### Scenario: Final product passes without proof directory
- **WHEN** a current-profile product satisfies every final Make requirement without a `review/early-proof/` directory
- **THEN** Make can finalize through `agent-outcome.json`

#### Scenario: A fabricated marker appears
- **WHEN** `.make-proof-ready.json` is written during current direct Make
- **THEN** the host does not interpret it as Make completion or create proof-acceptance state

### Requirement: Direct Make follows sealed Invent authority
Direct Make SHALL batch the exact Wish, current stage packet, sealed `NativeInvented` contract, selected Inventor guidance, Make reference, and CAD skill, persist a coherent complete self-contained CAD baseline early, and iterate against generated final artifacts. Narrow engineering coupons MAY test uncertain geometry, but disposable generic blockouts SHALL NOT become mandatory final form. The instructions SHALL NOT assume a separate Concept-stage image tree.

#### Scenario: Make needs an engineering check
- **WHEN** an uncertain fit or form fact needs falsification
- **THEN** the agent may build a narrow coupon
- **BUT** the final geometry remains governed by the Wish and sealed Invent result

### Requirement: Final product gates remain authoritative
Removing the early-proof phase SHALL NOT waive or weaken the Made result's binding to accepted Invent, complete printable inventory, strict fit, mesh validity, 0.4 mm wall-thickness checks, exact product-state evidence, final hash-bound independent semantic review, integrated CAD verification, Quest Playtest, Release manual validation, authenticated publication, or snapshot integrity.

#### Scenario: A proof-free product fails a final gate
- **WHEN** any authoritative final or downstream gate fails
- **THEN** the run does not advance merely because it uses the direct profile

### Requirement: Historical deep runs retain frozen proof behavior
Existing runs whose immutable inputs bind deep-v13 or an older proof-phased profile SHALL retain their original reasoning levels, context ceiling, turn boundaries, early-proof instructions, marker and receipt handling, recovery routing, and final gates. A repository upgrade SHALL NOT silently convert an existing checkpoint to direct Make.

#### Scenario: A v13 checkpoint resumes
- **WHEN** a v13 run resumes before proof acceptance, after proof acceptance, during source handoff, or during normal recovery
- **THEN** the host applies its frozen v13 protocol exactly

#### Scenario: New inputs contain historical reference files
- **WHEN** a new v14 run materializes the complete reference tree including v13 files
- **THEN** profile selection still binds the v14 direct marker
