## REMOVED Requirements

### Requirement: ABO invents the game as its wish research
**Reason**: This made an Inventor the implementation of a Python research capability — an executable seat that received the round's inputs and returned a breakdown. Inventors are declarative data with no entrypoint and no executable contract, and inventing a game from a Wish is cognitive work the runtime reserves for the native session.
**Migration**: The invention itself is the Concept turn's work under `workshop/concept-stage`, performed by the native session with ABO's Inventor subagent selected. ABO's game-specific judgment — that the Wish must be structural rather than decorative, that every distinction a player must make is carried by shape rather than colour or material, and what ABO refuses — lives in its `TASTE.md` and its required `abo-inventor` skill, where the agent that does the deciding actually reads it.

### Requirement: Rules declare the components each step touches
**Reason**: A structural rule over a Python return value's shape, checked by ABO's own module before it handed the value on. There is no return value and no ABO module to check it.
**Migration**: The obligation moves onto the Make turn and ABO's own deterministic tool: `workshop/abo-make` keeps the rules-to-engine translation and its declared-assumption discipline as obligations of the native Make turn, and where ABO ships an `abo-rules-engine` skill its hash-bound `scripts/` hold the engine that can only run if every step names pieces that exist.

### Requirement: Rules and bill are proved consistent before any brief is derived
**Reason**: The check was deterministic and mechanical — which is exactly why it survives — but its position did not. It was a precondition inside a Python research call, and there is no such call to gate.
**Migration**: The check itself becomes a deterministic specialist tool the native subagent invokes, shipped in the hash-bound `scripts/` of ABO's optional `abo-rules-engine` skill, with its result recorded as evidence rather than asserted. The host-enforced part of the guarantee — that the box and the build describe the same set of pieces — is settled where the host can settle it in bytes: `workshop/make-concept-adherence` requires the built part set to correspond one-to-one with the brief's components. Honestly stated: a self-declared complexity ceiling is no longer a host-blocking precondition; it is discipline the Taste and the tool carry.

### Requirement: The component bill is the concept's component breakdown
**Reason**: This bound one Python capability's output shape to another's input shape — ABO's bill becoming the brief's components. Neither shape is produced by ABO now, and the exploded-view check this requirement points the component set at is deleted.
**Migration**: The granularity rule becomes a universal gate rule rather than ABO's: `workshop/concept-stage` refuses a component specified only by name and purpose, requiring its form, bounding dimensions, placement, and interfaces, and refuses a single-component design that was defaulted rather than decided. The one-to-one correspondence the bill guaranteed is enforced at the Make boundary by `workshop/make-concept-adherence`, which is the check that replaced the inspector.

### Requirement: Every stated fact is attributable
**Reason**: Attribution was ABO's own obligation because ABO's module was the thing producing the facts. It is no longer an Inventor's to enforce, and an Inventor cannot enforce anything — its bundle is static bytes.
**Migration**: Attribution is now a rule of the host gate and applies to every Inventor, not just this one: `workshop/concept-stage` refuses a fact that names neither a recorded source nor a decision recorded with its reason, and refuses a fact that claims both. An unstated dimension recorded as ABO's own decision with the reason it was chosen satisfies that rule exactly as it did here.

### Requirement: The rules are sealed into the concept
**Reason**: ABO needed its own sealing rule because rules and a component bill were an ABO-shaped payload travelling beside a concept that did not know about them. The concept tree is now sealed whole.
**Migration**: `workshop/concept-stage` seals the entire concept tree — brief, research record, drawing instructions, descriptor, and every file in it — into one `concept_sha256`, and any byte added, removed, or modified after the gate accepted it fails at the next boundary that checks it. Rules written into that tree are covered by that seal like everything else, so they remain recoverable verbatim and an edit mid-round still fails the round.

### Requirement: A refining round revises the standing game rather than inventing a new one
**Reason**: Stated as a property of a research callable invoked once per run. Rounds are now driven by the host's feedback and round accounting, and a refining round may run no Concept turn at all.
**Migration**: `workshop/concept-stage` carries it for every lane: a Concept turn running with a standing concept receives that concept and the feedback, reuses the standing research rather than researching the Wish again, and preserves every feature the feedback did not challenge — so a revision cannot become an unrelated new design.
