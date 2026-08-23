# Bob → Panda Social: the exact publish contract

Research date: 2026-08-22. Sources: reinSPQR/vibe-ideas @ main (cloned to
/tmp/bob-research-publish), autonomous-ai/panda-social-backend docs fetched via
`gh api` (design-import-api.md, design-content-api.md, desktop-text-to-cad.md,
APP_LOGIN_INTEGRATION.md, worker-contract.md, swagger.json), and org canon at
/Users/d/code/autonomous-org/projects/vibe/README.md.

TLDR: Bob publishes over plain HTTPS as its own AI-creator account — `POST
/api/v1/designs/import` (multipart, **always `status=draft`**; the default is
`public`), then the Design Content API for the rules page, then STOP. The
draft→public flip (`POST /designs/{slug}/publish`, which also sets the sale
price) is a human action, per both the working precedent (vibe-ideas
publish.py) and the org's 08-06 promotion ladder. The backend has **no
structured AI-authorship field anywhere** (0 hits in swagger.json for
`disclosure|is_ai|ai_generated`; `models.User` has no flag), so disclosure is
carried by the account identity + listing copy until the launch-blocking
disclosure feature ships. Bob must NOT publish under a human account — that is
exactly the violation the live Gravity Well / Newsreel listings commit today.

---

## 1. The two publish paths, and which one Bob uses

### Path A — backend-direct (the vibe-ideas precedent; NOT for Bob)

`board-game/tools/publish.py` (506 lines) + `publishdesign` (Go, 12.7 KB
main.go) publish by linking against the backend's own code:

- publish.py shells out to `bin/publishdesign`, compiled *inside* the
  panda-social-backend checkout (build.sh copies main.go into
  `<backend>/cmd/publishdesign` because `internal/config` can't be imported
  across modules).
- publishdesign calls `services.ImportDesign` — "the same function
  POST /designs/import runs" — with the backend checkout as cwd so Mongo/GCS
  coordinates come from the backend's own `.env` (godotenv). It needs
  `GOOGLE_APPLICATION_CREDENTIALS` (GCS service-account json, default
  `<backend>/secrets/gcs-sa.json`) and `PANDA_OWNER_ID` (24-hex Mongo user id).
- It verifies the owner row exists first: "A design owned by a user that does
  not exist is invisible: it shows no author byline and never appears on that
  account's design list."

Why Bob should not copy this: it requires a local backend checkout, a Go
toolchain, direct Mongo access, and GCS infra secrets on Bob's Mac. The import
API doc states the intended division explicitly: "the client must hold **no**
infrastructure secrets … Git repo (Gitea), CDN (GCS), MongoDB: ❌ no
credentials [client] / ✅ holds all secrets [backend]." Path A also bypasses
the API's auth, which is the wrong precedent for an AI creator that is supposed
to be *one account among human creators* (08-09 ruling).

Keep Path A only as the documented break-glass fallback (it works today and is
what shipped the existing board games).

### Path B — HTTP import API (Bob's path)

Everything Bob needs is public API surface on
`https://panda-social-api.autonomous.ai/api/v1`:

| Step | Endpoint | Notes |
|---|---|---|
| 1 | `POST /auth/oauth/google` or PKCE device flow | mint bob's JWTs (one-time human act; §2) |
| 2 | `POST /auth/refresh` | rotate access+refresh before expiry; on every tick |
| 3 | `POST /designs/import` | multipart zip, **`status=draft`**, 201 → design JSON |
| 4 | `PATCH /designs/{slug}/use-case`, `PUT /designs/{slug}/story-blocks` | curated rules page |
| 5 | *(human)* `POST /designs/{slug}/publish` with `{listing:{price_cents}}` | draft→public + sale |
| 6 | updates: `POST /designs/{slug}/import` (new version), content API (page), `PATCH /designs/{slug}` (metadata) | never re-import via step 3 |

Import is synchronous (no job to poll), free (no credits), and **not
idempotent** — "uploading the same zip twice creates two designs." Cloudflare
kills responses >100 s (error 524, aborted cleanly server-side, safe to
retry); keep zips ≤50 MB (hard limit 100 MB), HTTP timeout ≥120 s.

## 2. Auth: the `bob` account and its token

Facts from APP_LOGIN_INTEGRATION.md + swagger:

- Users are only created by verifying a **Google id_token**
  (`POST /auth/device/login` from the web page, or `POST /auth/oauth/{provider}`
  directly). Both end in the same `{access_token, refresh_token, user}` pair.
- The PKCE device-login flow's hosted page is **stale**: desktop-text-to-cad.md
  (note dated 2026-07-25) says `https://panda.autonomous.ai/desktop-login` is
  gone and "no `desktop-login` route exists in the new FE repo yet — desktop
  sign-in needs a new hosted-login URL before it works again." So don't plan on
  the browser flow.
- One-time codes expire in 5 minutes, single-use, S256 PKCE only.
- `Authorization: Bearer <access_token>` on everything; `POST /auth/refresh`
  rotates the pair. Token lifetimes are not documented — refresh proactively
  each tick and on any 401, and persist the rotated refresh token immediately.

**The plan for Bob:**

1. Ops creates a Google identity for Bob (e.g. `bob@autonomous.ai` in the
   Workspace). This is a human act, once.
2. A human performs one sign-in to mint the first token pair. Given the stale
   login page, the practical route is obtaining a Google `id_token` for the bob
   identity (OAuth playground / gcloud) and calling
   `POST /api/v1/auth/oauth/google` — same response shape as exchange. This
   also **upserts the user row**, which is what makes the author byline exist.
3. Set the profile to disclose: username `bob` (or `bob-the-inventor`),
   display_name "Bob — AI game inventor", bio stating plainly that every game
   is invented, playtested, and published by an autonomous AI system.
   (`models.User.verified` is "Set admin-side / in DB; defaults false" — ask
   ops to set it if we want the check mark.)
4. Bob stores `{access_token, refresh_token, user.id}` in a chmod-600 file
   (e.g. `~/.bob/panda-auth.json`, same pattern as the desktop app's
   `panda-social-auth.json`) and self-serves refresh from then on. No Anthropic
   credentials ever go to this API; it is not a Claude proxy.

If the refresh chain ever dies (revoked/expired), publishing halts and Bob
raises a human task — it cannot re-mint alone. That's acceptable: publishing is
the end of the pipeline, not the tick loop.

## 3. `POST /designs/import` — exact request Bob sends

```
POST /api/v1/designs/import
Authorization: Bearer <bob access token>
Content-Type: multipart/form-data
```

| Field | Bob sends | Rule |
|---|---|---|
| `file` | the game zip | required; ≤50 MB rec. / 100 MB hard (413); expanded ≤512 MB; ≤4096 entries |
| `title` | game title | else derived from project.json name / spec.md H1 / folder |
| `description` | pitch + player count + playtime + **AI-authorship line** (§5) | ≤2000 chars; publish.py self-caps at 900 ("a store blurb has no business being longer") |
| `status` | **`draft` — always, hardcoded** | default is `public` = live on the feed immediately. Bob must never rely on the default |
| `tags` | `board-game,3d-print,cadquery` + an AI-authorship tag (§5) | ≤10 tags, ≤40 chars each |
| `category` | active slug from `GET /design-categories` (e.g. `toys-games` if active) | unknown/inactive → 400 |
| `license` | omit (defaults `CC-BY-NC-SA`) | ≤60 chars |
| `prompt` | the game concept sentence | shown in design history |
| `thumbnails` | hero render first, QA sheet second | jpg/png/webp ≤5 MB, max 5; first file = cover |

**Zip contract** (one zip = one design; two design folders → 400):

- Wrapper layout: `<slug>/{...}` — publish.py zips exactly this shape.
- Must contain `project.json` **or** a `*.py` defining `def gen_step` — else
  400 "no design found". Bob's CadQuery builds satisfy this with main.py.
- Primary STL named **`assembled.stl`** (or `<slug>.stl`; "assembled" wins the
  primary-mesh ranking). Include a client-exported `.glb` if available (server
  fallback conversion is "unindexed — a client-side trimesh export is
  smaller/nicer"; >2 M triangle meshes are skipped).
- Renders in `<slug>_review/` — filename scoring: contains `assembled` +100,
  `iso` +50, starts with `_` +20, `section/exploded/print` −40. Convention:
  **`<stem>_review/_assembled.png`** is the highest-scoring name possible.
- **`RULES.md` written into the zip** — publish.py precedent: the zip is the
  only surface with no length cap, so the *complete* rulebook ships there
  ("a game whose rules only half-arrived is not a game anyone can play").
  Also ship `bill.json` (part list + quantities) and `spec.md`.
- Server strips automatically: `.git/`, `__pycache__/`, `.claude/`, `inputs/`,
  `*.jsonl`, `conversation_transcript.txt`, `_tree.json`, `.env*`, `*.pem`,
  `*.key`, `secrets.*`, `.DS_Store` etc. Bob should still pre-strip (keeps zip
  small, entry count low). publish.py also drops `build/` when the root already
  carries the same assembled STL (avoids two identically-named STLs).
- No cover from any source (files, urls, zip renders, renderable STL) → 400,
  nothing created.

**Response 201** = full design JSON: keep `id`, `slug`, `status`,
`project_url`, `thumbnail_urls`, `current_history_id`. Persist it as
`published.json` next to the game (publish.py precedent) — this ledger is the
idempotency guard, because the API has none.

## 4. The rules page — Design Content API

The description caps long before a rulebook, so the rules go up in **three
places** (publish.py's exact split):

1. `RULES.md` inside the zip — complete, no limit.
2. `story_blocks` — the on-page walkthrough. Hard walls enforced server-side
   (`models.ValidateDesignContent`): lead 1–40 runes, body **180–400 runes**
   (runes, not bytes), max **10 blocks**, plain text (`<`/`>` rejected). When
   10×400 can't hold the walkthrough, spend the last block *saying so* and
   pointing at RULES.md (publish.py's `RULES_CLOSING`).
3. `description` — the pitch + facts ("2-4 players · 30 min") + the pointer
   "The complete rules ship with the files as RULES.md."

Endpoints (all owner-only, bearer required, same-shape response, no
`updated_at` bump so curating never re-pins the feed):

- `PATCH /designs/{slug}/use-case` — first write must carry `label` + `body` +
  `image` together (label ≤40, body 180–400, image absolute https 16:9 — use
  the design's own cover URL from the import response, exactly what
  publishdesign does).
- `PUT /designs/{slug}/story-blocks` — full array in render order; every block
  complete; 400 names the offending index.
- `print_specs` has **no API write path** — it's ops-authored (publishdesign
  writes it straight to Mongo). Over HTTP Bob simply skips print_specs; the
  slicer populates material data itself after publish, and per publish.py "a
  curated spec row OUTRANKS the slicer's measured one for good … a guess here
  would permanently mask the real number."

Order matters: import first (to have a cover URL), then use-case, then
story-blocks. If content writes fail, the design is still correct — retry the
content step only (publishdesign has the same recovery: "The design itself is
already written and correct; only the curated page failed.")

## 5. AI-authorship disclosure — where it goes

Org canon, /Users/d/code/autonomous-org/projects/vibe/README.md:

- 2026-08-06 (Dee): "Ruling on the word 'AI,' for canon: **it comes out of the
  hero and goes onto the listing — it never comes off the page.** You may omit
  the method; you may never assert an authorship the disclosure label will
  contradict."
- 2026-08-09 (Dee, strategy reset): AI inventory is "**one creator profile
  among human creators** — Autonomous operating as an AI creator on its own
  marketplace — and more AI creators land over time, one per niche." Launch-
  blocking for the open sell path: "creator payout ledger, hard-refuse
  classifier (CPSIA class), the 15 card-copy validations, and **AI-authorship
  disclosure on AI-creator listings** (the 08-06 'AI goes on the listing,
  never off the page' ruling — **now per-creator identity too**)."

**Backend reality check (measured):** swagger.json (372,738 bytes) has zero
occurrences of `disclosure`, `ai_creator`, `is_ai`, or `ai_generated`; neither
`apis.publishReq` nor `models.User` carries any AI flag. There is no structured
field to set. So until the disclosure feature ships, Bob carries the ruling in
the only places the schema offers:

1. **Per-creator identity (primary):** the `bob` account itself — username,
   display name, bio, avatar all state it's an AI inventor. Every listing shows
   this byline (`author` block in the design response). This is the 08-09
   "per-creator identity" mechanism.
2. **On every listing:** description opens or closes with a fixed line, e.g.
   "Invented, playtested, and published by Bob, an autonomous AI game
   designer." Plus a stable tag (e.g. `ai-created`) so a structured filter can
   be retrofitted later. Optionally one story block ("Who made this").
3. **Never in the hero/title** — per 08-06, AI is not hero copy; it's listing
   copy. And never omitted: omitting the method is allowed, contradicting it is
   not.

**The violation Bob must not repeat:** the live board-game listings today —
Gravity Well ($39.99, live on /vibe per
knowledge/site-truth-2026-08-09.md:33) and Newsreel — are listed under human
accounts with no AI-authorship disclosure, against the 08-06 ruling (the
Gravity Well launch thread, content/ideas/gravity-well-launch-thread.md, hangs
it off Dee's account). Bob publishes under the `bob` account only, disclosure
in place from the first draft. If the token on disk ever belongs to a human
account (check `user.id` against the pinned bob id at startup), refuse to
publish.

**CPSIA hard-refuse:** the 08-06 audit found "an uncertified toddler-grip toy
buyable under CPSIA (`VB-TZ2PYGGA`)", and the hard-refuse classifier is
launch-blocking. Bob's rule: board games are 14+ general-audience products.
Hard-refuse at the *idea* stage anything designed for or marketed to children
(child-targeted theme + small parts = CPSIA territory); never write age
grading below 14+ into copy; the human publish gate re-checks. This is a
refusal, not a warning.

## 6. Draft → public flip, and pricing

`POST /designs/{slug}/publish` (owner only, JSON body optional):

- `title` — rename as it goes public; slug re-derived, old slug kept as alias;
  >120 chars rejects, design stays draft.
- `listing: {price_cents}` — integer USD cents, **100..1000000**, and must
  cover the fulfilment floor once the design has been sliced:
  `(weight_g × 1.3 × 3820 / 1000) + 800` cents — "the printed mass uplifted
  30% for waste and priced at $38.20/kg, plus $8 flat shipping at cost." Equal
  to the minimum is accepted; the 400 names the exact minimum. First listing
  mints an immutable SKU.
- `attachments` (≤12 CDN links), `assembly_parts` (draft-editor colors) —
  optional.
- **Trap: an empty body publishes AND auto-lists at a platform-estimated
  price.** So the flip must always be deliberate and carry an explicit price.

Post-publish management: `PUT /designs/{slug}/listing` (re-price/re-list, same
SKU), `DELETE /designs/{slug}/listing` (pause), `POST /designs/{slug}/unpublish`.

**Price corner:** the 07-23 red-team memo reframe — "buyable catalog = the
**$40–80 functional/substantial corner** (no sub-$25 decorative, no ASINs),
shipping charged separately" — and the convergence note: Dee's printed samples
("family board game, traffic puzzle — colorful, multi-part") *are* that
corner. Bob's recommended price is therefore **4000–8000 cents**, floored by
the fulfilment formula, and it is a *recommendation attached to the human
gate*, not something Bob sets.

## 7. What only a human may do

Straight from precedent and canon:

1. **The draft→public flip + the price.** publish.py: "It stops at DRAFT —
   private to its owner — and the draft→public flip stays a human action in
   the app … Nothing here ever makes a design public." Org 08-06 promotion
   ladder: "agents generate/price/prune unsupervised; **a human signs the
   batch to publish**." Bob's harness must not even hold code that calls
   `/designs/{slug}/publish` in its autonomous loop — put the flip in a
   separate human-invoked script (`bob publish-approve <slug>`) so an agent
   bug can't reach it.
2. **Minting the account and its first token** (Google sign-in, §2), and
   setting `verified` (admin/DB-side).
3. **Deleting a public design** (`DELETE /designs/{slug}` is permanent).
4. **CPSIA edge calls** — the classifier hard-refuses the clear cases; a human
   judges anything borderline before the flip.
5. Physical proof: per the 07-23 memo, "Proof-of-print + moderation/IP/safety
   gates before any stranger's design is buyable" — for Bob's own games the
   equivalent bar is the human seeing the printed game (or explicitly waiving
   it) before the flip.

Mirror of the vibe-ideas gate discipline Bob should keep: publish is only
reachable from a queue state meaning "owner said ship" (their `shipped` state,
set by `pipeline_queue.py ship <slug>` — "owner: gate 2 yes"), with a
machine-checked quality gate (`gate.json` pass) that even `--force` has to
name-check: "nothing reaches the world unmeasured."

## 8. Updates after first publish (never re-import)

"a second import would fork the game into a second design" — publish.py.

- Files changed → `POST /designs/{slug}/import` (new version of the existing
  design; publishdesign's `-design <id> -zip` mode / `--new-version`).
- Rules/page text changed → content API only (`--page` mode). Does not touch
  the snapshot or bump `updated_at`.
- Title/description/tags/cover order → `PATCH /designs/{slug}` (never changes
  the slug; `PATCH /designs/{slug}/rename` for that).
- The `published.json` ledger decides which mode applies; import mode with an
  existing ledger entry is a hard no-op ("safe to call from a loop").

## 9. Dry-run design

The HTTP import has **no dry-run flag** and is not idempotent, so Bob's
dry-run is two layers:

**Layer 1 — local validator (every run, blocking):** mirror the backend's own
walls before any bytes move:
zip ≤50 MB and ≤4096 entries; exactly one design folder; `gen_step` py or
project.json present; `assembled.stl` present; a `_review/_assembled.png`
cover; RULES.md non-empty; description ≤2000 (target ≤900); ≤10 tags ≤40
chars; story blocks ≤10, leads 1–40 runes, bodies 180–400 runes, no `<`/`>`;
use_case complete; thumbnails ≤5 × ≤5 MB png/jpg/webp; auth: token refreshes
and `user.id` == pinned bob id. Print the would-be title/description/tags —
the Go CLI's dry-run explicitly surfaces the description because "it is what
the store page shows under the title."

**Layer 2 — live rehearsal (once per Bob release, and first game):** import a
sacrificial game with `status=draft` for real, verify the viewer loads
`project_url` + `_tree.json`, the cover, and the story blocks, then
`DELETE /designs/{slug}`. Drafts are invisible to everyone but the owner
(`404` for others), so a rehearsal draft leaks nothing. A 524/500 mid-import
"never leaves a half-built design visible … safe to retry."

The Telegram notification pattern from publish.py is worth keeping verbatim in
spirit: after every real import, message the owner with id/slug/link + "It is
private until you flip it to public in the app. Check the viewer loads the
model first."

## 10. Open items for Bob's build

1. Confirm the active category slug for games (`GET /design-categories`) —
   publish.py sends none (falls back to first active), which is sloppy for a
   storefront; pick one deliberately.
2. Access/refresh token lifetimes are undocumented — measure once, then set
   the refresh cadence.
3. The structured AI-disclosure field is a backend launch-blocker owned by the
   Software agent (vibe README §next). When it lands, Bob adopts it in the
   same release; the tag+bio scheme is the bridge.
4. `autonomous.ai/factory` vs `/vibe`: canon nav (product-architecture v4) has
   Factory; the live listings surface today is `/vibe`. Either way the backend
   contract above is the same Panda Social API; only the public URL Bob prints
   in reports differs — resolve at integration time.
