# ADR 0085: An invisible Contract Amendment may be made inside a run, confirmed by a fresh reader

- Status: Accepted; implemented and deterministically tested; not yet
  validated by a live run
- Date: 2026-10-03
- Owners: the `make-round` skill (`--propose-amendment`,
  `--record-amendment-review`, `--contract-amendments`, `--clear-blocked`),
  the Contract Reviewer definition
  (`src/workshop/make/agents/contract-reviewer.toml`), the make_round guard
  and its host side (`make/make_round_guard.py`, `make/role_guard.py`), the
  host's replay (`make/contract_amendments.py`), product-run Make
  instructions (`references/make.md`, product-run `AGENTS.md`), the Make
  finalizer (`stage_proposal.py`), the host's Make gate and receipt
  (`workflow/native_run.py`, `cli/main.py`), and `build-a-toy`
- Amends: ADR 0080 (a Contract Contradiction is always a `need`), ADR 0083
  (only the Reference Camera may be amended inside a run), issue #88 (how a
  Blocked Report is cleared)
- Issue: #90; amended by #96 (one Smaller Retry, 2026-10-04) and #100 (an
  Owner Contract Amendment on resume, 2026-10-04)

## Context

A Contract Contradiction stops the run with a `need` (ADR 0080, issue #88).
Apart from the Reference Camera (ADR 0083), no path amends a sealed Design
Contract inside a run, so even an invisible fix (a clearance, a print stance,
geometry no reference image shows) costs a full stop, an outer-loop pass and
a fresh attempt. Broken God attempts 9, 10, 11, 14 and 15 all hit Contract
Contradictions. In attempt 11 the Manager resolved them silently in shared
code, which the contract does not allow; nothing recorded which statement
had changed.

The unattended `build-a-toy` loop (issue #89) already applies an invisible
amendment without the owner, outside the run. The cost is the stop, not the
decision.

## Decision

1. **In-run Contract Amendment, invisible changes only.** When the Workshop
   Manager meets a Contract Contradiction (directly, or through a Blocked
   Report) whose smallest fix changes nothing a sealed reference image
   shows, it may propose a Contract Amendment instead of a `need`:
   `make_round <cad-project> --propose-amendment PROPOSAL.json`, with
   `{"rows": [...], "changes": [{"from", "to"}], "reason", "report"?}`.
   `rows` quotes the two or more statements that cannot both hold, verbatim.
   Each change replaces one whole requirement text, or one Interface's text
   under schema 4. A reference, a geometry's name, count or dimensions and
   an Interface's kind, envelope or poses are beyond an in-run amendment:
   the tool refuses them. One amendment awaits review at a time; while it
   does, an assembly round, `--full` and the Make proposal are refused.
2. **A fresh Contract Reviewer confirms it.** The proposal writes a packet
   with the rows, each change before and after, the reason and every sealed
   reference image by path and sha256. The Manager spawns a new
   `contract-reviewer` (a fixed Make role agent beside the Component Worker
   and Component Reviewer, at the run's frozen effort) and sends it only the
   packet path and hash. It views every image and answers three things:
   `contradiction` (the rows cannot both hold), `smallest` (no smaller
   change removes it) and `visible_in` (every reference that would show
   it), with `references_checked` naming every reference.
   `--record-amendment-review` records the verdict. The amendment applies
   only when the first two are true and `visible_in` is empty; otherwise it
   is refused and the Manager stops with the `need` the tool prints. A
   reviewer is fresh: never the Manager, never a Component's reviewer, and
   never one who reviewed an earlier amendment. On Claude Code it is named
   by native agent id, and the guard logs its start and every image it
   reads (issue #77's evidence).
3. **The host records it by hash.** Each event goes to the CAD project's
   `measure/contract-amendments.jsonl`, bound to the run by the sha256 of
   `WISH.json` and to the canonical-JSON hash of the contract it was
   proposed against. `WISH.json`, the requirements outside the amended
   rows, and every image keep their bytes. Before Make acceptance the host
   replays the ledger against the contract `WISH.json` sealed and refuses a
   proposal whose contract hash differs from the one the applied amendments
   before it leave, a change that quotes a row wrongly, an amendment
   without a recorded review, a packet that changed or omits a sealed
   reference, a review that does not account for every reference, a
   reviewer who is not fresh, and on Claude Code a reviewer the runtime did
   not start as a `contract-reviewer` or who did not read every sealed
   image. A status is derived from the verdict, never read. The Make gate
   receipt seals every amendment: the old and new row text, the reviewer's
   record and the contract hash before and after. The run receipt lists
   every amendment of every attempt from the ledgers, so a run that stopped
   still lists them, and `workshop status` prints one line for each.
4. **Rounds read the amended rows.** `make_round` reads the sealed contract
   with every applied amendment: the rows a component round delivers, the
   rows a worker's Blocked Report quotes, and the contract-rows hash a
   review is bound to. A Component whose rows changed (an amended row
   scoped to it, an Interface that names it, or any amended assembly row)
   unlocks as it does for a Shared Helper change, and a review never carries
   across the change. The finalizer matches the signature review's
   requirement rows against the amended contract.
5. **A Blocked Report may be cleared by an amendment.** `--clear-blocked
   {"report": N, "amendment": M}` clears a report when amendment M is
   applied and names report N. The host refuses a report cleared by an
   amendment that is not.
6. **Visible changes still stop the run** with a `need`. The outer loop
   and the owner handle them.
7. **The outer loop folds amendments back.** `build-a-toy` merges every
   applied in-run amendment into the toy's `CONTRACT.md` for the next
   attempt (`scripts/ledger.py fold`) and records it in the ledger's
   `in_run_amendments`.

## Consequences

- An invisible Contract Contradiction costs one fresh reader's turn, not a
  stop and a new attempt.
- Who may change a sealed contract mid-run widens from the host (a camera)
  to the Manager with a fresh reader's agreement; the host still verifies
  every byte and hash it accepts.
- The visible/invisible line is the reviewer's judgement against the
  images, not a measurement. A wrong "invisible" verdict is caught later by
  the Component Review against that image, and the owner sees every
  amendment in the run report and the ledger.

## Compatibility

A frozen run keeps its materialized `make_round`, guard and role agents; it
has no ledger and nothing changes. A run whose ledger is absent records no
amendment. A Component locked by a review recorded before this change has
no contract-rows binding and is unlocked only as before.

## Amendment: one Smaller Retry after a "smaller change exists" refusal (2026-10-04, issue #96)

Status: Accepted; implemented and deterministically tested; not yet
validated by a live run.

**Context.** Broken God attempt 16 (`wish-20261003-115126-141dbe76`) had all
ten Components locked and assembly r0004 passing. Amendment 1 changed R01
"as a V" to "spread behind it". Its reviewer answered `contradiction: true`,
`visible_in: []`, `smallest: false`: deleting only "as a V" removes the
contradiction without adding a requirement. Under decision 2 the Manager
stopped on a need, and the outer loop discarded about 183M tokens of
conforming work for a three-word change the reviewer had already named.

**Decision.** Decision 2 changes for new runs:

1. **One Smaller Retry.** When the only earlier amendment quoting the same
   rows (compared as a whitespace-collapsed set) was refused with
   `contradiction` true, `visible_in` empty and `smallest` false, the
   Manager may propose once more for that contradiction. The retry quotes
   the same rows; each change names a row the refused amendment changed,
   from the same text; and each change's `to` is that `from` with only
   deletions applied: strictly fewer characters, a character subsequence of
   the original text, and every word of it a word of the original, in
   order, so no word is added or respelled. It may change fewer rows, and
   it may not repeat the refused change.
2. **Another fresh reader.** The retry goes to a fresh `contract-reviewer`:
   not the one who refused, not the Manager, not a Component's reviewer.
   The existing freshness rule already covers it, in the tool and at
   replay. The reviewer is asked to name the smaller change in `reason` as
   the exact row text, so the Manager can propose it.
3. **Only then the need.** A refusal of the retry, a refusal for any other
   reason (`contradiction` false or `visible_in` not empty), or any later
   proposal quoting rows an earlier amendment quoted (applied or refused)
   stops the run with the need, as before.
4. **The host enforces it by text.** `make_round --propose-amendment`
   refuses a retry that breaks these rules, and records `retry_of` (the
   refused amendment's number, or null) in the proposal event and packet.
   The host's replay before Make acceptance re-derives `retry_of` from the
   ledger and refuses a proposal whose `retry_of` differs, a retry that adds
   or respells text, a third proposal for the same rows, a retry after a
   contradiction or visibility refusal, and a reused reviewer.
   `--record-amendment-review` prints the retry and the reviewer's reason
   after a smaller-change refusal that still allows it, and the need it
   stops on otherwise.

**Compatibility.** A frozen run keeps its materialized `make_round`,
guidance and role agent text and never proposes a retry. The host's replay
now refuses any second proposal quoting the same rows unless it is a valid
Smaller Retry; under the original decision 2 a refused amendment already
stopped the run on its need, so a conforming earlier ledger has no such
proposal.

## Amendment: an Owner Contract Amendment answers a contradiction need on resume (2026-10-04, issue #100)

Status: Accepted; implemented and deterministically tested; not yet
validated by a live run.

**Context.** Broken God attempt 17 (`wish-20261004-050844-831e5160`) had all
ten Components locked and five Coupled Interface rounds run when it stopped
on a Contract Contradiction need. Amendment 1 was refused as not the
smallest, and its Smaller Retry (amendment 2) was refused too, so the run
could only wait. The owner's root fix (amend-l: a hard stop ends the closed
extreme, the detent holds the open one) changed only R03, the
`interface:wing-housing` text and two prose lines. `workshop resume` had an
owner answer for a camera need (ADR 0083) and none for a contract need, so
the loop had to relaunch and rebuild every locked Component, about 30 cost
units.

**Decision.**

1. **The owner answers on resume.** `workshop resume <wish-id>
   --amend-contract CONTRACT.md` takes the owner's whole amended contract
   file, the same file `build-a-toy` keeps at the toy's root. The run must
   be unfinished and in Make. No Contract Reviewer is asked: the source is
   the owner.
2. **The host diffs, it does not judge.** The file must parse as a Design
   Contract. Its block is compared with the contract the run reads now: the
   sealed contract, then every applied in-run amendment of the current Make
   attempt's ledger, then every earlier owner amendment. Only requirement
   text and Interface text may differ. The host refuses, naming every
   difference at once, a change to the schema, title, Inventor, envelope, a
   reference or its camera, a geometry, a requirement's id, scope or order,
   and an Interface's id, kind, Components, envelope, poses or yielding
   side. It also refuses a file that changes nothing, a ledger that does not
   replay, and an in-run amendment awaiting its review. Prose outside the
   block may change freely.
3. **The run keeps its sealed name line.** A run sealed with `workshop wish
   --contract` holds the whole file as its objective, opening with the
   round's name (`Name this toy exactly: ...`). The amended objective is the
   owner's file with the run's sealed name line in its place (prepended
   when the file has none); a name line in a file for a run that sealed
   none is refused. A correction run's objective is its brief, which holds
   no contract prose, so only the block's rows are amended there.
4. **Recorded by hash, beside `WISH.json`.** `WISH.json`, the requirement
   ids, the Interface ids, kinds and Components, and every image keep their
   bytes. The host appends the amendment to the run root's
   `CONTRACT-AMENDMENTS.json` (ADR 0083's host-written file, rebound in the
   tamper-checked input manifest) under `owner_amendments`: `source:
   owner`, each change's row, scope, text before and after, the Components
   it affects, the contract hash before and after, the prose diff, the
   objective hash before and after, the file's sha256, the attempt and the
   number of in-run amendments its ledger held. The amended objective goes
   beside it as `objective`. The same record goes to the host's own
   host-correction ledger, which no agent writes.
5. **Rounds read it; only touched Components unlock.** `make_round` and the
   Make finalizer read the sealed contract, then the applied in-run
   amendments, then the owner amendments. A Component whose own rows
   changed (a requirement scoped to it, or an Interface that names it)
   unlocks through the contract-rows hash, as decision 4 above. Unlike an
   in-run amendment, an owner's assembly row binds no Component: no
   Component Review judged it, and the assembly rounds, the blind review
   and the final verification read the current contract.
6. **In-run amendments close.** After the owner's first amendment,
   `make_round --propose-amendment` is refused, and the host's replay before
   Make acceptance refuses an in-run amendment numbered above the count the
   ledger held then. A further contradiction stops on a need for the owner,
   who can answer it the same way.
7. **The host replay and the report account for it.** At Make acceptance
   the host refuses a run-root file whose `owner_amendments` differ from
   its own records, applies the closure above, and seals the owner
   amendments in the Make gate receipt after the in-run ones. The run
   receipt lists camera, in-run and owner amendments, and `workshop status`
   prints one line for each owner amendment. `build-a-toy`'s `fold` skips
   them: the owner's file already holds them.

**Frozen runs.** An owner amendment cannot reach a run materialized before
this change, and the host refuses it before writing anything. A run's
`make_round` and Make finalizer are frozen at launch, and only these tools
read `owner_amendments`. Tested on a copy of the motivating run
(materialized at `70a2a652`, ledger amendments 1 and 2 both refused):

- the frozen `make_round` reading a `CONTRACT-AMENDMENTS.json` that holds
  the owner's R03 and `interface:wing-housing` changes still returns the
  sealed contract, and no Component's contract-rows hash moves. Its rounds,
  its packets and its finalizer would keep the sealed R03 while the host
  recorded another, so the run could never finalize against the owner's
  rows;
- the frozen replay refuses a third in-run proposal quoting the rows that
  amendments 1 and 2 quote ("a contradiction gets one Smaller Retry at
  most"), so no ledger event can carry the fix either, and faking a
  Contract Reviewer's verdict would forge the review that ADR 0085 binds to
  a proven reviewer;
- `--amend-contract` on that copy is refused with "this run's make_round
  was materialized before owner contract amendments (issue #100) and would
  keep reading the sealed rows", and no file of the run or its host state
  changes.

The host detects support by the marker `workshop-owner-contract-amendments-v1`
in both the frozen `make_round` and the frozen finalizer, each verified
against its input binding. `workshop resume --refresh-tools` does not make a
frozen run eligible: it rewrites `make_round` but not the finalizer, the
role agents or the Make guidance, and mixing tool generations inside one
run is not a capability frozen runs gain. On the same copy the current
`make_round` would compute the same contract-rows hashes on the sealed
contract and would move only `spine-housing` and `wing` for the owner's
rows, which is what the new path does for a run launched after this change.

**Rejected.**

- Rewriting `WISH.json`: it is sealed, and every ledger event and review
  binds its hash.
- Appending an owner event to the in-run ledger: the ledger is written
  inside the agent's workspace, and frozen replays refuse an unknown event
  kind.
- Reopening in-run amendments after an owner amendment: the replay would
  need to interleave host and ledger events by position, and the owner is
  already the one answering.

## Rejected

- Letting the Manager amend alone: attempt 11 showed a silent choice.
- A deterministic visibility rule (refuse every geometry row): too broad,
  since a print stance or a clearance is a requirement row no image shows.
- Writing the amendment into `CONTRACT-AMENDMENTS.json` mid-turn: only the
  host writes run inputs, and it is not present inside the native turn. The
  ledger plus the host's replay at Make acceptance gives the same binding.
