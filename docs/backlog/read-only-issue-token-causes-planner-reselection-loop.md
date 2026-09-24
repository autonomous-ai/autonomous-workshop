# A read-only `GH_TOKEN` makes the Sandcastle planner re-select finished work forever

- Status: Open — root cause confirmed, no fix applied
- Priority: High (silently burns whole iterations; the run never terminates)
- Component: `.sandcastle/` orchestration (`main.ts`, `plan-prompt.md`), not `src/workshop/`
- Observed: iterations 7–9 of the `sandcastle-tooling` run on 2026-09-23

## Symptom

The planner re-selected the same issues on consecutive iterations and the run
made no forward progress:

- Iteration 7: planned #40 → implementer committed a "still blocked" note
- Iteration 8: planned #37 and #38 → **0 branches with commits, nothing to merge**
- Iteration 9: planned #40 again → same blocked note as iteration 7

Left alone this repeats until `MAX_ITERATIONS`, spending a full agent budget
per iteration to rediscover that the work is already done or still blocked.

## Root cause

Issue state on GitHub is the planner's only memory between iterations, and the
sandbox cannot write it.

`.sandcastle/main.ts` injects `GH_TOKEN` from `.sandcastle/.env` into each
container. That file documents the required grants as "Issues (Read and write)
and Metadata (Read)", but the token GitHub actually honours has neither:

| Probe with that token | Result |
| --- | --- |
| `gh api user` | authenticates as `reinSPQR` |
| `X-OAuth-Scopes` response header | absent → it is a **fine-grained** PAT |
| `gh api repos/autonomous-ai/autonomous-workshop/issues/37` | 200 `#37 open` |
| `gh api repos/autonomous-ai/autonomous-workshop/collaborators` | 403 `Resource not accessible by personal access token` |
| `gh api -X PATCH .../issues/37 -f state=open` (no-op write) | 403 `Resource not accessible by personal access token` |

`autonomous-workshop` is a **public** repository, so the successful issue read
proves nothing — anonymous access returns the same bytes. The `collaborators`
probe is the diagnostic one: it needs authenticated repository access and also
403s. The token therefore holds *no* granted access to this repository and is
falling back to public-read-only.

That is the signature of a fine-grained PAT that the `autonomous-ai`
organization has not approved, or whose "Repository access" list omits this
repository. Fine-grained PATs against org-owned repositories are inert until an
org owner approves them, whatever permissions were ticked at creation time.

The host's own `gh` (classic PAT, `repo` scope, `MAINTAIN` on the repository)
can write issues fine — which is why the read-only sandbox token was not
noticed earlier. Only host-side steps, such as the plan prompt's
`!gh issue list ...` expansion, use it.

## Consequence chain

1. Implementers finish #37, #38 and #39; the commits merge into
   `sandcastle-tooling` (`a948453c`, `7dbcffbc`, `7a7e33b2` — all verified
   ancestors of the branch).
2. Each implementer tries to close or comment on its issue and is 403'd. Two
   separate sessions recorded this; commit `254efa28` is one of them.
3. The issues stay open, so the next planner reads them as outstanding work.
4. The planner is smart enough to *notice* the commits and skip #37–#39 in its
   prose, but the plan block it emits is still driven by open-issue state, so
   it falls through to #40 — the only remaining issue with no open blocker.
5. #40 is separately un-runnable in the sandbox, so it produces another note
   and closes nothing. Return to step 3.

The dependency graph guarantees the loop rather than softening it: #41–#44 are
each blocked by #40 and #45 by #44, so #40 is the sole selectable issue once
#37–#39 are ignored. There is no other work for the planner to fall back to.

## Why this is worth fixing beyond the token

Repairing the token unblocks *this* run, but the failure mode is structural and
will recur the next time a token is rotated, expires, or loses org approval:

- The 403 is discovered by the *implementer*, deep inside an iteration, after
  the expensive work is already done. Nothing checks write access up front.
- A 403 on close is treated as a soft note-to-self, not as a run-level fault.
  The orchestrator sees a successful iteration.
- The planner has no signal distinguishing "open and ready" from "open only
  because nobody could close it", and no memory of having planned the identical
  issue set on the previous iteration.

## Suggested fixes

1. **Preflight the token.** On run start, assert issue-write with a harmless
   idempotent call (`PATCH issues/<n> -f state=open` on an already-open issue,
   or `gh api repos/:owner/:repo/collaborators`). Fail the run loudly rather
   than discovering it mid-iteration. Cheapest fix, catches every recurrence.
2. **Treat a failed close as a run fault.** If an implementer reports
   `<promise>COMPLETE</promise>` but could not close its issue, surface that to
   the orchestrator instead of leaving it in a commit message.
3. **Detect the repeat.** If the planner emits an issue set identical to the
   previous iteration's and that iteration produced no commits, stop with a
   diagnostic. This is the general guard: it also catches a genuinely
   un-runnable issue such as #40, which no token grant fixes.
4. **Correct `.sandcastle/.env`'s comment** once the real grant is known, so
   the documented requirement matches what is provisioned.

## Repro

With the sandbox `GH_TOKEN` loaded, against any open issue in the repository:

```
gh api -X PATCH repos/autonomous-ai/autonomous-workshop/issues/37 -f state=open
# => gh: Resource not accessible by personal access token (HTTP 403)
```

Then run two planner iterations back to back and observe the identical plan
block, with no commits produced by the second.

## Related

- Issue #40's own blocker, a `claude` CLI without credentials, is cleared: the
  baseline Run completed and is recorded in `docs/BASELINE_CORRECTION_RUN.md`.
