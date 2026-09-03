## 1. Freeze the direct deep profile

- [x] 1.1 Add a new immutable current deep-economics capability file that preserves Forge/Quest Invent behavior, the 256,000-token compaction ceiling, later-stage settings, the eight-turn command cap, and normal recovery while specifying high-reasoning 60-minute Make from its first turn; verify capability packaging and byte/hash tests pass.
- [x] 1.2 Rename current-profile code identifiers to explicit deep-v13 compatibility identifiers and add separate direct-deep versus phased-deep classification helpers; verify tests select the new marker only for newly created Forge/Quest runs and still recognize representative v13, v12, v10, and older frozen markers.
- [x] 1.3 Update run materialization and frozen-input validation so new deep runs bind the direct profile permanently without changing existing run roots or checkpoints; verify a new run retains direct behavior after resume and a fixture frozen on v13 retains proof-phased behavior.

## 2. Route current Make directly to final product work

- [x] 2.1 Change current-profile Make launch selection to use high reasoning, the 60-minute boundary, and `agent-outcome.json` from the first turn; verify launcher tests show no 16-minute proof turn or 15-minute proof-to-source handoff for the direct profile.
- [x] 2.2 Bypass proof discovery, proof validation, `.make-proof-ready.json`, proof-acceptance receipt creation/readback, and proof-specific turn selection for direct-profile Make while retaining those functions for frozen phased profiles; verify focused workflow tests observe no proof marker or receipt on direct Make and unchanged marker/receipt handling on v13 fixtures.
- [x] 2.3 Route recoverable and explicit-resume continuations of direct Make through the ordinary same-session, same-stage, same-Goal recovery path over durable product bytes; verify recovery tests never insert a proof or source-handoff phase and remain bounded by the existing recovery policy.
- [x] 2.4 Replace the current Make prompt and materialized product-run guidance with Invent-to-Make instructions that batch the exact Wish, sealed `NativeInvented` contract, and other mandatory reads, persist a coherent complete CAD baseline early, permit narrow engineering coupons, and forbid disposable blockouts from becoming mandatory final form; verify prompt/asset tests preserve Wish and Invent-result authority, assume no Concept-stage images, and omit current-profile early-proof requirements.
- [x] 2.5 Make the CAD skill's early-proof exclusion explicitly historical/profile-scoped so current direct Make can load it immediately without weakening old-run instructions; verify skill-registry and materialized-asset tests cover both current and frozen-profile behavior.

## 3. Preserve gates and compatibility failure paths

- [x] 3.1 Add direct-profile tests proving Make can finalize without `review/early-proof/` and that missing proof residue does not block progress, recovery, finalization, or operator resume; verify the targeted native-host test module passes.
- [x] 3.2 Add failure-path tests proving proof-free runs still fail on final semantic review, Made-to-Invent binding, inventory, fit, mesh, wall-thickness, exact-evidence, integrated verification, and downstream Quest/Release requirements; verify no direct-profile fixture advances after a failed authoritative gate.
- [x] 3.3 Add historical-resume tests for checkpoints before proof acceptance, after proof acceptance, during final-source handoff, and during normal recovery; verify v13 and older runs preserve their frozen timeouts, prompts, markers, receipts, and final gates after upgrade.
- [x] 3.4 Ensure runtime cleanup and marker handling remove or interpret `.make-proof-ready.json` only for frozen phased profiles and cannot mistake it for direct-profile completion; verify a fabricated marker in a current run does not complete Make or create host-owned proof state.

## 4. Update acceptance coverage

- [x] 4.1 Update the authenticated mock-session Forge route so current Make is one direct final-product phase using the normal finalizer; verify its trace contains one Wish-wide session and one Make Goal but no proof turn, marker, receipt, or source handoff.
- [x] 4.2 Update the authenticated mock-session Quest route with the same direct Make behavior before Playtest; verify its trace reaches the unchanged Playtest and Release boundaries without fabricated proof state.
- [x] 4.3 Add an acceptance-audit failure case for helpers that fabricate `.make-proof-ready.json`, proof receipts, or host proof state for a current-profile run; verify the route fails rather than masking the production contract.
- [x] 4.4 Run the focused effort, native-host, native-session, asset, CAD-skill-registry, and mock-session suites, then the full deterministic test suite; verify every command exits successfully and no historical compatibility assertion is weakened or deleted merely to pass.

## 5. Document the superseding architecture

- [x] 5.1 Add the next ADR recording why the proof checkpoint is superseded for new deep runs after the 256k context fix, why final gates remain, and why v13 proof handling must remain resumable; verify the ADR explicitly supersedes the relevant current-profile portions of ADRs 0030, 0033, 0038, and 0041 without rewriting their historical record.
- [x] 5.2 Update `AGENTS.md`, the product-run `AGENTS.md`, `docs/NATIVE_AGENT_RUNTIME.md`, `docs/ARCHITECTURE.md`, and `docs/QUALITY_ECONOMICS.md` to distinguish direct current Make from historical phased Make; verify repository searches find no statement that new Forge/Quest runs freeze v13 or require early proof.
- [x] 5.3 Update Forge, Quest, and workshop-floorplan diagrams and accessible descriptions to show direct high-reasoning Make with ordinary recovery and unchanged gates; verify the rendered/source diagrams contain no early-proof checkpoint on the current route.

## 6. Rerun and evaluate the exact Wish

- [x] 6.1 From the implementation worktree, launch a fresh Forge run through the normal Workshop CLI using exactly `A geometry-readable orthodox chess set that turns six Ho Chi Minh City landmarks into a complete 32-piece skyline, with round River and square Grid plinths distinguishing the two sides without relying on color.`; verify the frozen checkpoint identifies the direct profile and preserve any genuine completed, waiting, or failed terminal state without bypassing host-owned effects.
- [x] 6.2 Preserve the new run identifier plus hashes/paths for its sealed `NativeInvented` artifact, `snap/iso.png`, `snap/signature.png`, final semantic review, checkpoint, elapsed-time evidence, and native token telemetry in the private run workspace; verify the evidence resolves to the exact run bytes and do not commit private product artifacts or transcripts.
- [x] 6.3 Conduct a blind render comparison in which the reviewer first identifies orthodox roles and specific HCMC landmarks without labels, then evaluates each final against its exact Wish and that run's accepted structured Invent requirements; verify the record covers the new run and both baselines `wish-20260902-133652-1fe0198a` and `wish-20260902-154647-fabfb6fc`, including disagreements and the fresh-Invent confound.
- [x] 6.4 Add an evidence-backed comparison to `docs/QUALITY_ECONOMICS.md` reporting Wish adherence, Invent-result adherence, landmark recognizability, role recognizability, visual finish, completion, elapsed time, and measured token use for all three runs; verify it cites run IDs and artifact hashes, truthfully states whether quality improved, and introduces no host-side aesthetic score or production gate.

## 7. Final verification

- [x] 7.1 Run strict OpenSpec validation for `disable-early-proof-phase` and the repository's complete deterministic verification from the implementation worktree; verify both succeed with a clean diff check and document any external Release waiting state separately from code correctness.
- [x] 7.2 Review the final diff for frozen-run compatibility, unchanged effect ownership, unchanged deterministic and semantic gates, and absence of committed credentials, private artifacts, transcripts, or build output; verify each requirement scenario is covered by a test or the preserved same-Wish evaluation evidence.
