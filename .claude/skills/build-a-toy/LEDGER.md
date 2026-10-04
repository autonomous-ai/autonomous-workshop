# The build-a-toy ledger

`<contract-dir>/build-a-toy/ledger.json` is the source of truth for a toy's
builds. `scripts/ledger.py check` validates it; `scripts/ledger.py next`
reads it and prints the unattended loop's next action, so a new session
resumes the loop from this file alone.

## Fields every ledger has

| Field | What it holds |
|---|---|
| `contract` | the contract's path |
| `title`, `inventor` | the toy's clean title and Inventor |
| `rounds[]` | every attempt and round: number, kind (`wish` or `fix`), name, wish id, run workspace, toy directory, final status, brief, finding ids; free-form notes may follow |
| `contract_versions` | every contract version by key (`v1`, `amend-a`, ...), each with its status, notes and backups |

## Fields the unattended loop adds

A ledger without `loop` predates the unattended mode. `check` accepts it;
`next` prints `migrate` until the fields below are added from the existing
record.

### `loop`

| Field | What it holds |
|---|---|
| `schema` | `1` |
| `state` | `launch`, `watching`, `diagnosing`, `fixing`, `awaiting-owner`, `stopped` or `done` |
| `attempt` | the latest attempt number |
| `wish_id` | the attempt being watched, or the one that last stopped |
| `source_commit` | the `origin/main` commit the current or next attempt runs from |
| `awaiting` | while `awaiting-owner`: `reasons` (each stop condition that holds), `review_page` (or null) and `since`; otherwise null |
| `updated` | when the loop last wrote the ledger |
| `no_progress_cleared_through` | set by the owner's decision: the no-progress count starts again from this attempt |

### `stops[]`

One entry per stop of an attempt, in order.

| Field | What it holds |
|---|---|
| `attempt`, `wish_id` | the attempt that stopped |
| `stop_category`, `status` | from the receipt |
| `class` | `complete`, `camera-need`, `contract-contradiction`, `reference-mismatch`, `harness-defect`, `budget-progressing` or `other`, from `ledger.py classify` |
| `evidence` | what the diagnosis found, one line each, with paths or times |
| `progress` | `locked` and `repeated_print_defects` at the stop, from `tally.py --json` |
| `budget_raised` | `true` on the one stop per attempt that was resumed with a raised cap |
| `resolution` | what the loop did about it |

### `contract_contradictions[]`

| Field | What it holds |
|---|---|
| `id` | a short unique id |
| `attempt` | the attempt that exposed it |
| `signature` | `<check>:<component>`: the `design-a-toy` check that covers the class, and the Component. A later entry with the signature of an applied one is a contradiction that came back |
| `rows` | at least two contract statements, verbatim |
| `amendment` | the `contract_versions` key that fixes it |
| `visible` | whether a reference image must be redrawn |
| `approved` | null until approved: `owner <date>` for a visible change (or for one the owner approved before the loop), `not-needed` for an invisible one |
| `applied` | true once the amendment is in `CONTRACT.md` and re-audited; it needs `approved` |
| `reaudit` | the whole-contract Stage 3b/3c/3d notes; required once applied |
| `recurrence_acknowledged` | `owner <date>` when the owner let a contradiction that came back be fixed again |
| `resume` | null until tried: `resumed` when the stopped run took the applied, invisible fix as an owner amendment (`workshop resume --amend-contract`, issue #100), `refused` when the run predates it and the loop relaunched instead. `ledger.py next` prints `resume-amendment` while an applied invisible entry of the last attempt has none |
| `design_check` | `name`, `issue` (or null when the check landed with no issue) and `status` (`proposed`, `open`, `merged`) of the `design-a-toy` check that catches the class |

### `in_run_amendments[]`

Every Contract Amendment a run applied inside itself (ADR 0085), folded into
`CONTRACT.md` for the next attempt. `scripts/ledger.py fold` writes the
entries; set `contract_version` to the version that holds the fold.

| Field | What it holds |
|---|---|
| `attempt`, `wish_id` | the attempt and run that applied it |
| `amendment` | the run's amendment number |
| `rows` | the contradicting statements it removed, verbatim |
| `changes` | each `row` with its `from` and `to` text |
| `reviewer` | the Contract Reviewer who confirmed it |
| `contract_sha256`, `amended_sha256` | the run's contract hash before and after |
| `folded` | true once `CONTRACT.md` holds the `to` text |
| `contract_version` | the `contract_versions` key of the folded contract; required once folded |

### `harness_issues[]`

| Field | What it holds |
|---|---|
| `number`, `title` | the GitHub issue |
| `opened_by_loop` | the loop implements and merges only issues it opened |
| `attempt` | the attempt that exposed it, or null |
| `status` | `open`, `implementing`, `merged`, `failed`, `conflict`, or `abandoned` when the owner drops it |
| `merge_commit` | required when merged |

### `cost_units`

| Field | What it holds |
|---|---|
| `cap` | 100 unless the owner sets another |
| `by_attempt` | attempt number to cost units, from `tokens.py --json` |
| `unmeasured_attempts` | attempts whose transcripts cannot be measured |
| `total` | the sum of `by_attempt` |

Cost units weight a million tokens by price relative to fresh input: input 1,
cache write 1.25, cache read 0.1, output 5.
