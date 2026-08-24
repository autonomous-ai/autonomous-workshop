# Bob

Bob is the canonical **moving-machines** inventor. He shows the middle customization
level: Bob owns **Make**, while Workshop supplies Wish intake, Taste binding,
the default AI-agent **Playtest**, product Instructions, Deliver, and durable runtime.
[`TASTE.md`](TASTE.md) defines his kinetic point of view.

```text
creation:       Wish -> Bob Make <-> Workshop Playtest -> Workshop Instructions -> Workshop Deliver
after delivery: customer Reviews -> future Makes
```

Workshop Playtest uses AI agents and deterministic tools. Exact printing and
hands-on QA belong to Deliver; customer feedback arrives later as Reviews and
may guide future Makes.

The custom moving-machine Make is an explicit integration seam and is not implemented
yet. `python3 profile.py` is the canonical Workshop-facing entrypoint;
it must fail closed rather than route a kinetic Wish into unrelated code.

```bash
python3 -m pip install -e ../..
python3 profile.py profile
python3 profile.py preview first-machine "I wish my rally car became a hand-cranked climbing machine"
python3 profile.py run first-machine "I wish my rally car became a hand-cranked climbing machine" --playtest-rounds 4
```

`run` currently returns a typed `waiting` result at Bob's owned Make seam. The
remaining migration is exactly one `MakeContext -> Made` moving-machine callback.
Once installed, the callback feeds the shared AI-agent Playtest; `bob.py` is
never used as a fallback.
`--playtest-rounds` is a checked 1–100 allowance recorded with the Wish; it is
not inferred from free-form prompt text.

## Preserved board-game laboratory (noncanonical)

Bob's original board-game harness is preserved in `bob.py`, `harness/`,
`loops/`, and `toys/` because its budgeting, research, simulation, effect, and
learning work remains useful migration material. It is **not** Bob's moving-machine
Make implementation and the Workshop profile never calls it implicitly. Its
original creative constitution is preserved in
[`TASTE.board-games.md`](TASTE.board-games.md).

That laboratory studies game history, develops physical mechanisms, plays each
design thousands of times, and keeps only games that survive deterministic
checks and adversarial review. Its historical customer diagram was:

```text
WISH  --------------------------  WAIT  ----------------------  RECEIVE
  |                                                                  ^
  +--> Bob's TASTE guides MAKE <-> INSPECT ---------------------------+
                           |
                 artifact + runtime + adapter + receipt
```

The legacy storefront adapter can create a draft. Manufacturing and delivery
are the next part of the customer path, not something this code pretends is
complete.

## How the legacy board-game laboratory uses Workshop

```text
Wish + historical board-game Taste
      |
      v
MAKE  Bob explores rules, mechanics, play engines, and printable geometry
      |
      v
INSPECT
      rules checks -> 1,000+ simulations -> seated LLM games -> CAD checks
      -> isolated judges -> frozen reward threshold
      |
      v
      artifact: `pack_artifact(...)` -> `PackedArtifact`
      inspection: `inspect_pack(...)` verifies exact bytes and SHA-256
      runtime: records intent before any remote effect
      adapter: `ShopDoor` creates a private draft or optional public listing
      receipt: binds the remote result to the exact artifact and owner
```

Bob's inspectors are specific to board games; the Workshop supplies the shared
Taste binding, canonical artifact handling, durable runtime, storefront adapter,
and typed receipts. Existing APIs named `PackedArtifact`, `Clockwork`, `Sender`,
`ShopDoor`, and `Stamp` remain compatibility names while callers migrate. A
mutable JSON file, a remote design id, command output, or a human assertion is
never proof that an external effect succeeded.

The durable Bob state machine predates the Workshop language and keeps its exact
on-disk names for safe upgrades:

```text
sparked -> researched -> ruled -> rules_gated -> simulated -> tabled
        -> briefed -> built -> build_gated -> reviewed -> published -> live
```

Those are Bob's persisted queue values, not extra shared Workshop stages. In
the developer story they group naturally as:

- `MAKE`: idea search through CAD build
- `INSPECT`: rules, simulation, table, build, and reward checks

After Inspection, ordinary artifact handling and the runtime can invoke the
storefront adapter and retain its receipt. They are implementation details, not
additional Workshop verbs.

`bob.py tick` advances one step of one game. It runs an integrity audit first,
then checks budget and leases. When no game can move, Bob studies one source or
runs the weekly architecture loop. Files under `corpus/`, `state/`, and
`toys/` are the message bus; agents never edit the queue or reward function.

## Layout

| Path | What it contains |
|---|---|
| `TASTE.md` | Bob's canonical moving-machine creative constitution |
| `TASTE.board-games.md` | preserved Taste for the noncanonical board-game laboratory |
| `ARCHITECTURE.md` | the design, gates, loops, and Workshop mapping |
| `docs/REWARD.md` | the frozen board-game reward specification |
| `docs/CONTRACTS.md` | Bob's module and state contracts |
| `harness/` | queue, budgets, reward, ledger, Workshop adapter, effect boundary |
| `loops/` | Make and Inspection work, playtests, study, architecture, improvement |
| `toys/<slug>/` | one game's wishes, rules, engines, parts, reviews, and page kit |
| `state/` | durable queue, effect ledger, credentials, and heartbeat |
| `ops/` | launchd install, uninstall, and watchdog |

## Run the preserved board-game laboratory

These commands exercise legacy migration material. They do not run Bob's
canonical moving-machines profile and must not receive a new kinetic Wish.

```bash
cd inventors/bob
python3 -m unittest discover -s tests -t .
python3 bob.py seed
python3 bob.py tick
python3 bob.py status
ops/install.sh
```

The historical board-game route defaults to an offline rehearsal:

```bash
BOB_SEND_DRY_RUN=1 python3 bob.py tick
BOB_SEND_DRY_RUN=0 python3 bob.py send <slug>
BOB_SEND_DRY_RUN=0 python3 bob.py send <slug> --price-cents 5900
```

The last command performs the optional public storefront action. The default
`bob send <slug>` stops at a private draft. `BOB_SHOP_PUBLIC=1` lets the
scheduled loop request the priced public action after Inspection is green.
After an ambiguous public send, `python3 bob.py reconcile-public <slug>` reads
back the recorded intent and never repeats the effect.

Canonical operator settings are:

```text
BOB_SEND_DRY_RUN=1
BOB_SEND_VIA=workshop
BOB_SHOP_PUBLIC=0
BOB_SHOP_API=https://panda-social-api.autonomous.ai/api/v1
BOB_SHOP_ALLOWED_ORIGINS=https://panda-social-api.autonomous.ai
BOB_SHOP_OWNER_ID=<Bob's pinned marketplace owner id>
BOB_WORKSHOP_SRC=/absolute/path/to/autonomous-workshop/src   # nonstandard layouts only
```

The provider hostname retains its historical name; the storefront adapter class
in Bob's code is still `ShopDoor`. Credentials live at `state/shop-auth.json`
(mode 0600). The compatibility runtime database remains
`state/inventor-workshop.sqlite3`. New games emit `toys/<slug>/send.json` and
`toys/<slug>/pack/`; these filenames are persisted interfaces, not Workshop
concepts.

Old names are accepted only at a conflict-checked compatibility edge:

- `BOB_PUBLISH_*`, `BOB_AUTO_FLIP`, `BOB_PORTAL_*`, `BOB_PANDA_*`,
  `PORTAL_OWNER_ID`, and `PANDA_OWNER_ID`
- `BOB_FOUNDATION_SRC` and `BOB_CORE_SRC`
- `portal-auth.json`, `panda-auth.json`, `inventor-foundation.sqlite3`, and
  `inventor-core.sqlite3`
- `launch.json`, `published.json`, `launch_payload/`, and `publish_payload/`
- `harness.publish` and `bob publish`

Bob continues one legacy authority in place. If canonical and legacy sources,
settings, credentials, projections, or state files disagree, he refuses to
send until an operator resolves the split.

The historical text2game server was named `box`; `bob export <slug>` preserves
its payload format for local manual investigation only. `push_box` and
`BOB_SEND_VIA=box` fail closed before rsync, SSH, or remote publication. The
autonomous loop never exports or treats external stdout/design ids as receipts. The obsolete
`mark-published` command fails closed.

The checked-in `g0003` / Clearance draft remains intentionally stranded. It
predates Bob's Workshop intent and artifact identity and belongs to a different
principal. Its current owner must resolve that remote draft separately; Bob
will not adopt it or retry the slug.

## The rules Bob lives by

1. The evaluator is the product; the generator is replaceable.
2. Budgets live in code, outside agent prompts.
3. Nothing expensive happens before the game has been played.
4. Every verdict binds to the exact artifact SHA-256 it inspected.
5. An absent verdict is a failure, never a pass.
6. Kill early, kill cheap, and record why—the reason becomes training data.
