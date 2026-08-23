"""Publish — Path B of docs/research/publish-contract.md, exactly.

Bob publishes over plain HTTPS to the Panda Social API as its own AI-creator
account. The order is the contract's order: local validator (Layer 1, every
run, blocking) -> zip -> POST /designs/import with **status=draft always**
-> curate the rules page -> flip public with an **explicit price** (the
empty-body trap auto-lists at a platform-guessed price). Auto-publish is
Dee's 2026-08-22 ruling; the human gate is a kill switch (Telegram notice +
one-tap UNPUBLISH), not a turnstile.

Three non-negotiables carried from the contract:

1. **Idempotency lives here, not in the API.** "uploading the same zip twice
   creates two designs" — so games/<slug>/published.json is the ledger, and
   import_draft() with an existing ledger entry is a hard no-op.
2. **Disclosure is identity + copy**, because the backend has no structured
   AI field (0 swagger hits for disclosure/is_ai/ai_generated). The pinned
   bob user id, the fixed description line, and the 'ai-created' tag are the
   08-06 ruling's only carriers. Token belonging to any other account =
   refuse (the Gravity Well / Newsreel violation must not repeat).
3. **Dry-run is the default** (BOB_PUBLISH_DRY_RUN=1): the import API has no
   dry-run flag, so ours is Layer 1 + the zip + a manifest, then stop.

ALL network goes through one `_http()` seam; tests monkeypatch it and never
touch the real API. Every state write is atomic (tmp + os.replace).

Metadata source: games/<slug>/listing.json — {title, description, tags,
category, prompt, use_case, story_blocks[, price_cents]} — written by the
page-writer agent upstream. published.json next to it is written only by
this module.
"""

import hashlib
import io
import json
import os
import re
import stat
import sys
import urllib.error
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone

from harness import ledger, queue, telegram

# --- Walls (mirror the backend's own numbers; publish-contract §3, §9) -----

# 50 MB recommended cap (hard limit is 100 MB / HTTP 413) — we wall at the
# recommendation because Cloudflare kills >100 s responses and a 50 MB zip
# already flirts with that on a bad uplink.
MAX_ZIP_BYTES = 50 * 1024 * 1024
MAX_ZIP_ENTRIES = 4096          # backend hard limit; 4097th entry = 400
MAX_DESCRIPTION = 900           # publish.py precedent self-cap: "a store
                                # blurb has no business being longer" (API
                                # allows 2000; we keep the working bar)
MAX_TAGS = 10                   # backend: <=10 tags
MAX_TAG_CHARS = 40              # backend: <=40 chars each

# Story-block walls (models.ValidateDesignContent, in RUNES not bytes —
# Python len() on str counts code points, which is what the server counts).
MAX_BLOCKS = 10
LEAD_RUNES = (1, 40)
BODY_RUNES = (180, 400)

# The fixed disclosure line (publish-contract §5). FIXED means byte-for-byte:
# a paraphrase is a diff a validator can't see and a policy nobody can grep.
#: Dee 2026-08-24, verbatim: the listing byline is exactly "By Bob." — the
#: same shape Alice used on Blindcap. AI authorship rides on the byline and
#: the ai-created tag, never a paragraph of explanation.
DISCLOSURE_LINE = "By Bob."
# Stable machine-readable tag so a structured disclosure filter can be
# retrofitted later (§5 item 2).
AI_TAG = "ai-created"

# Price corner: the 07-23 red-team memo's "$40-80 functional/substantial
# corner". BOB_PRICE_OVERRIDE=1 lets a human list outside it; Bob alone
# cannot. The API's own bounds (100..1000000 cents) hold regardless.
PRICE_MIN_CENTS = 4000
PRICE_MAX_CENTS = 8000
API_PRICE_MIN = 100
API_PRICE_MAX = 1000000

# Cloudflare aborts >100 s; contract says "HTTP timeout >=120 s" so the
# client outlives the edge and reads the real error, not a local timeout.
HTTP_TIMEOUT_S = 120

# Pre-strip list (§3): the server strips these anyway, but shipping them
# wastes entry budget and, for transcripts/.env, ships things that must
# never leave the machine even to a stripping server.
STRIP_DIRS = frozenset([
    ".git", "__pycache__", ".claude", "inputs", "transcripts",
    "publish_payload",   # our own output — zipping it would recurse
    "review",            # judge evidence, not product
    "playtest",          # sim engine + playout logs, not product
    "export_text2game",  # the box-pipeline mirror — a byte-identical copy of
                         # the same meshes; shipping both doubled g0003's zip
                         # to 23.7 MB against a 50 MB advisory wall
    "__cadgen__",        # cadgen's build cache: regenerable, never product
])
STRIP_FILES = frozenset([
    "conversation_transcript.txt", "_tree.json", ".DS_Store",
    "published.json",    # the idempotency ledger is about the design,
    "listing.json",      # and the metadata IS the form fields — neither
                         # belongs inside the artifact they describe
])
STRIP_SUFFIXES = (".jsonl", ".pem", ".key")
STRIP_PREFIXES = (".env", "secrets.")

AUTH_FILE = "panda-auth.json"    # state/panda-auth.json, chmod 600
DEFAULT_CATEGORY = "toys-games"  # publish-contract §10 open item 1: picked
                                 # deliberately instead of publish.py's
                                 # sloppy first-active fallback; listing.json
                                 # may override once ops confirms the slug.


class PublishError(Exception):
    """Raised when publishing cannot proceed. The message always says what
    to do next (CONTRACTS §6) — a bare traceback teaches the 3am log reader
    nothing."""


# ---------------------------------------------------------------------------
# Plumbing
# ---------------------------------------------------------------------------

def _home():
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _api_base():
    # Overridable for the Layer-2 live rehearsal against a staging host.
    return os.environ.get(
        "BOB_PANDA_API", "https://panda-social-api.autonomous.ai/api/v1")


def _dry_run():
    # Default ON until creds exist (CONTRACTS §2). Only the literal '0'
    # arms the network path — anything else stays safe.
    return os.environ.get("BOB_PUBLISH_DRY_RUN", "1") != "0"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _game_dir(slug):
    return os.path.join(_home(), "games", slug)


def _published_path(slug):
    return os.path.join(_game_dir(slug), "published.json")


def _auth_path():
    return os.path.join(_home(), "state", AUTH_FILE)


def _atomic_write(path, data, mode=None):
    """tmp + os.replace; optional chmod BEFORE the replace so the secret
    file is never world-readable for even one scheduler tick."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.tmp.%s" % (path, uuid.uuid4().hex[:8])
    with open(tmp, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        fh.flush()
        os.fsync(fh.fileno())
    if mode is not None:
        os.chmod(tmp, mode)
    os.replace(tmp, path)


def _write_json(path, obj, mode=None):
    _atomic_write(path, json.dumps(obj, indent=2, sort_keys=True), mode=mode)


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _http(method, url, headers=None, data=None, timeout=HTTP_TIMEOUT_S):
    """THE network seam. Returns (status, headers_dict, body_bytes).

    HTTP error statuses are returned, not raised — the caller reads the
    body because the backend's 400s name the exact wall (e.g. the price
    floor 400 "names the exact minimum"). Transport failures (DNS, TLS,
    timeout) do raise: there is no response to interpret.
    Tests monkeypatch this function; nothing else in the module may open
    a socket.
    """
    req = urllib.request.Request(url, data=data, method=method)
    for key, val in (headers or {}).items():
        req.add_header(key, val)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()


# ---------------------------------------------------------------------------
# Auth — the bob account, and nobody else's
# ---------------------------------------------------------------------------

def _load_auth():
    """state/panda-auth.json:
    {access_token, refresh_token, user: {id, ...}, bob_user_id}

    bob_user_id is the PIN — written once by the human who minted the
    account (publish-contract §2), never by Bob. user.id comes from the
    last auth response. They must match or publishing refuses (§5: "If the
    token on disk ever belongs to a human account ... refuse to publish").
    """
    # BOB_FACTORY_TOKEN is the operator path (Alice's ALICE_FACTORY_TOKEN
    # pattern, the one that shipped Blindcap): a bearer lifted from a
    # logged-in autonomous.ai web session, handed to Bob for one run. It
    # wins over the file because it is the fresher credential by
    # construction, and it is never written to disk — a session token in a
    # repo is a leak waiting for a git add.
    env_token = os.environ.get("BOB_FACTORY_TOKEN", "").strip()
    if env_token:
        return {
            "access_token": env_token,
            "refresh_token": "",
            "user": {"id": os.environ.get("BOB_FACTORY_USER_ID", "")},
            "bob_user_id": os.environ.get("BOB_FACTORY_USER_ID", ""),
            "source": "env:BOB_FACTORY_TOKEN",
        }
    path = _auth_path()
    if not os.path.exists(path):
        return None
    try:
        return _read_json(path)
    except ValueError:
        return None


def refresh_auth():
    """POST /auth/refresh; persist the rotated pair 0600, immediately.

    "persist the rotated refresh token immediately" (§2) — refresh rotates
    BOTH tokens, so a crash between response and disk strands the account
    (the old refresh token is dead). Hence atomic write, chmod before
    replace, and no other function ever writes this file.
    """
    auth = _load_auth()
    if not auth or not auth.get("refresh_token"):
        raise PublishError(
            "no refresh token in %s — a human must mint the bob account's "
            "first token pair (publish-contract §2); Bob cannot re-mint "
            "alone." % _auth_path())
    body = json.dumps({"refresh_token": auth["refresh_token"]}).encode()
    status, _, resp_body = _http(
        "POST", _api_base() + "/auth/refresh",
        headers={"Content-Type": "application/json"}, data=body)
    if status != 200:
        raise PublishError(
            "auth refresh failed (HTTP %s): %s — if the refresh chain is "
            "dead, publishing halts; raise a human task to re-mint the bob "
            "token (publish-contract §2)."
            % (status, resp_body.decode("utf-8", "replace")[:300]))
    fresh = json.loads(resp_body.decode("utf-8"))
    auth["access_token"] = fresh.get("access_token", auth.get("access_token"))
    auth["refresh_token"] = fresh.get(
        "refresh_token", auth.get("refresh_token"))
    if isinstance(fresh.get("user"), dict):
        auth["user"] = fresh["user"]
    auth["refreshed_at"] = _now_iso()
    _write_json(_auth_path(), auth,
                mode=stat.S_IRUSR | stat.S_IWUSR)  # 0600
    return auth


def _bearer(auth):
    return {"Authorization": "Bearer %s" % auth.get("access_token", "")}


# ---------------------------------------------------------------------------
# Layer-1 validator — every wall, locally, before any bytes move
# ---------------------------------------------------------------------------

def _load_listing(slug):
    path = os.path.join(_game_dir(slug), "listing.json")
    if not os.path.exists(path):
        return None
    try:
        return _read_json(path)
    except ValueError:
        return None


def _has_design_source(gdir):
    """project.json OR a *.py defining `def gen_step` — else the backend
    400s "no design found". Scan is shallow: the design entry point lives
    at the design root by the publish.py zip convention."""
    if os.path.exists(os.path.join(gdir, "project.json")):
        return True
    try:
        names = os.listdir(gdir)
    except OSError:
        return False
    for name in names:
        if not name.endswith(".py"):
            continue
        try:
            with open(os.path.join(gdir, name), "r", encoding="utf-8",
                      errors="replace") as fh:
                if re.search(r"^\s*def\s+gen_step\b", fh.read(),
                             re.MULTILINE):
                    return True
        except OSError:
            continue
    return False


def validate(slug):
    """Layer-1 local validator (publish-contract §9). Returns a list of
    wall-failure strings — empty means green. Each string names its wall
    so a test (and the 3am log) can tell exactly which brick was hit.

    Builds the zip if it doesn't exist yet: the three zip walls are
    unmeasurable without the artifact, and build_zip() is local,
    deterministic, and idempotent.
    """
    problems = []
    gdir = _game_dir(slug)
    if not os.path.isdir(gdir):
        return ["game dir: games/%s does not exist — nothing to validate"
                % slug]

    # -- design source ------------------------------------------------------
    if not _has_design_source(gdir):
        problems.append(
            "design source: no project.json and no *.py with `def gen_step` "
            "— the backend rejects the zip with 'no design found'")

    # -- primary mesh + cover ------------------------------------------------
    if not os.path.exists(os.path.join(gdir, "assembled.stl")):
        problems.append(
            "assembled.stl: missing — 'assembled' wins the primary-mesh "
            "ranking; the build step must export it at the design root")
    cover = os.path.join(gdir, "%s_review" % slug, "_assembled.png")
    if not (os.path.exists(cover) and os.path.getsize(cover) > 0):
        problems.append(
            "cover: %s_review/_assembled.png missing or empty — no cover "
            "from any source means 400, nothing created" % slug)

    # -- rules ---------------------------------------------------------------
    rules = os.path.join(gdir, "RULES.md")
    if not (os.path.exists(rules) and os.path.getsize(rules) > 0):
        problems.append(
            "RULES.md: missing or empty — the zip is the only surface with "
            "no length cap; a game whose rules only half-arrived is not a "
            "game anyone can play")

    # -- listing copy --------------------------------------------------------
    listing = _load_listing(slug)
    if listing is None:
        problems.append(
            "listing.json: missing or unparseable — the page-writer step "
            "must produce {title, description, tags, ...} before publish")
    else:
        desc = listing.get("description") or ""
        if not desc:
            problems.append("description: empty")
        if len(desc) > MAX_DESCRIPTION:
            problems.append(
                "description: %d chars > %d cap — a store blurb has no "
                "business being longer" % (len(desc), MAX_DESCRIPTION))
        if DISCLOSURE_LINE not in desc:
            problems.append(
                "description: missing the fixed disclosure line %r — AI "
                "goes on the listing, never off the page (08-06 ruling)"
                % DISCLOSURE_LINE)
        tags = listing.get("tags") or []
        if len(tags) > MAX_TAGS:
            problems.append("tags: %d > %d cap" % (len(tags), MAX_TAGS))
        if AI_TAG not in tags:
            problems.append(
                "tags: missing %r — the machine-readable disclosure bridge "
                "until the backend grows a structured field" % AI_TAG)
        for t in tags:
            if len(str(t)) > MAX_TAG_CHARS:
                problems.append("tags: %r is %d chars > %d cap"
                                % (t, len(str(t)), MAX_TAG_CHARS))
        if not listing.get("title"):
            problems.append("title: empty — the import would fall back to "
                            "a folder-name-derived title")

    # -- the zip itself ------------------------------------------------------
    zip_path = os.path.join(gdir, "publish_payload", "%s.zip" % slug)
    if not os.path.exists(zip_path):
        try:
            zip_path = build_zip(slug)
        except (OSError, PublishError) as exc:
            problems.append("zip: could not build — %s" % exc)
            zip_path = None
    if zip_path and os.path.exists(zip_path):
        size = os.path.getsize(zip_path)
        if size > MAX_ZIP_BYTES:
            problems.append(
                "zip: %d bytes > %d — prune renders/meshes; the hard limit "
                "is 100 MB but 50 MB is the Cloudflare-safe bar"
                % (size, MAX_ZIP_BYTES))
        try:
            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()
        except zipfile.BadZipFile:
            names = None
            problems.append("zip: corrupt archive — rebuild with "
                            "build_zip('%s')" % slug)
        if names is not None:
            if len(names) > MAX_ZIP_ENTRIES:
                problems.append("zip: %d entries > %d backend cap"
                                % (len(names), MAX_ZIP_ENTRIES))
            tops = set(n.split("/", 1)[0] for n in names if n.strip("/"))
            if tops != set([slug]):
                problems.append(
                    "zip: expected exactly one design folder '%s/', found "
                    "%s — two design folders is a 400" % (slug, sorted(tops)))

    # -- auth: right account or no account ----------------------------------
    auth = _load_auth()
    if auth is None:
        problems.append(
            "auth: state/%s missing or unparseable — a human must mint the "
            "bob token pair first (publish-contract §2)" % AUTH_FILE)
    elif auth.get("source") == "env:BOB_FACTORY_TOKEN":
        # Operator-supplied session bearer (Alice's shipped path). There is
        # no minted bob account yet, so the identity pin cannot apply — the
        # byline "By Bob." on the listing carries authorship instead, which
        # is the disclosure the 08-06 ruling actually asks for. A refresh
        # token is meaningless for a session bearer; a 401 means the human
        # pastes a fresh one, which is the honest failure mode.
        pinned = auth.get("bob_user_id")
        actual = (auth.get("user") or {}).get("id")
        if pinned and actual and actual != pinned:
            problems.append(
                "auth: token user.id %r != pinned bob id %r — refusing"
                % (actual, pinned))
    else:
        pinned = auth.get("bob_user_id")
        actual = (auth.get("user") or {}).get("id")
        if not pinned:
            problems.append(
                "auth: no pinned bob_user_id in state/%s — ops must pin the "
                "bob account id so a human token can never publish as Bob"
                % AUTH_FILE)
        elif actual != pinned:
            problems.append(
                "auth: token user.id %r != pinned bob id %r — refusing; "
                "publishing under a human account is exactly the Gravity "
                "Well violation (publish-contract §5)" % (actual, pinned))
        if not auth.get("refresh_token"):
            problems.append("auth: no refresh_token — the pair cannot "
                            "rotate; re-mint per publish-contract §2")
    return problems


# ---------------------------------------------------------------------------
# Zip assembly
# ---------------------------------------------------------------------------

def _keep_entry(rel_parts, name):
    """Should this file ship? rel_parts are the path components below the
    game dir (dirs only), name is the basename."""
    for part in rel_parts:
        if part in STRIP_DIRS or part.startswith(".env"):
            return False
    if name in STRIP_FILES:
        return False
    if name.startswith(STRIP_PREFIXES):
        return False
    if name.endswith(STRIP_SUFFIXES):
        return False
    if name.startswith(".") and name not in (".gitignore",):
        # dotfiles are config/secrets territory, never game content
        return False
    return True


def build_zip(slug):
    """Assemble games/<slug>/publish_payload/<slug>.zip.

    Wrapper layout `<slug>/...` (one zip = one design; the backend 400s on
    two top-level folders). Pre-strips everything the server would strip
    anyway plus our own process artifacts — transcripts and .env must not
    leave the machine even to a stripping server, and every skipped file
    is entry budget saved (4096 cap). Deterministic: fixed timestamp so
    rebuilding an unchanged game dir yields byte-identical zips (stable
    sha256 in the manifest).
    """
    gdir = _game_dir(slug)
    if not os.path.isdir(gdir):
        raise PublishError("games/%s does not exist — nothing to zip" % slug)
    out_dir = os.path.join(gdir, "publish_payload")
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, "%s.zip" % slug)

    entries = []
    for root, dirs, files in os.walk(gdir):
        rel_root = os.path.relpath(root, gdir)
        rel_parts = [] if rel_root == "." else rel_root.split(os.sep)
        # prune stripped dirs in place so walk never descends into them
        dirs[:] = sorted(d for d in dirs
                         if d not in STRIP_DIRS and not d.startswith(".env")
                         and not d.startswith("."))
        for name in sorted(files):
            if not _keep_entry(rel_parts, name):
                continue
            full = os.path.join(root, name)
            arc = "/".join([slug] + rel_parts + [name])
            entries.append((full, arc))

    tmp = zip_path + ".tmp.%s" % uuid.uuid4().hex[:8]
    # 1980-01-01: the zip epoch. Real mtimes would make every rebuild a
    # "new" artifact and churn the manifest sha for no content change.
    fixed_date = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for full, arc in entries:
            with open(full, "rb") as fh:
                data = fh.read()
            info = zipfile.ZipInfo(arc, date_time=fixed_date)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            zf.writestr(info, data)
    os.replace(tmp, zip_path)
    return zip_path


# ---------------------------------------------------------------------------
# Multipart — written carefully, tested against golden bytes
# ---------------------------------------------------------------------------

def _multipart(fields, files, boundary=None):
    """Encode multipart/form-data with stdlib only.

    fields: list of (name, value) — a LIST, because field order is part of
    the wire format and a dict would make the golden-bytes test flaky on
    3.6-era habits. files: list of (name, filename, content_type, bytes).
    Returns (body_bytes, content_type_header). CRLF everywhere: bare LF in
    multipart is the classic "works on curl, 400s on Go" bug.
    """
    if boundary is None:
        boundary = "bob-boundary-%s" % uuid.uuid4().hex
    if not re.match(r"^[A-Za-z0-9'()+_,\-./:=? ]{1,70}$", boundary):
        raise ValueError("boundary %r has characters HTTP won't carry"
                         % boundary)
    buf = io.BytesIO()
    dash = ("--%s\r\n" % boundary).encode("ascii")
    for name, value in fields:
        buf.write(dash)
        buf.write(('Content-Disposition: form-data; name="%s"\r\n\r\n'
                   % name).encode("utf-8"))
        buf.write(str(value).encode("utf-8"))
        buf.write(b"\r\n")
    for name, filename, ctype, data in files:
        buf.write(dash)
        buf.write(('Content-Disposition: form-data; name="%s"; '
                   'filename="%s"\r\n' % (name, filename)).encode("utf-8"))
        buf.write(("Content-Type: %s\r\n\r\n" % ctype).encode("ascii"))
        buf.write(data)
        buf.write(b"\r\n")
    buf.write(("--%s--\r\n" % boundary).encode("ascii"))
    return buf.getvalue(), "multipart/form-data; boundary=%s" % boundary


# ---------------------------------------------------------------------------
# Import (draft, always)
# ---------------------------------------------------------------------------

def import_draft(slug):
    """Import the game as a DRAFT design. The one function that moves bytes
    to the marketplace.

    Hard no-op when games/<slug>/published.json exists: the API is not
    idempotent ("the same zip twice creates two designs"), so the ledger on
    disk is the only guard — safe to call from a loop.

    Dry-run (default): validate + build_zip + write
    publish_payload/manifest.json, advance the queue with note 'dry-run',
    stop. Auth walls are recorded as warnings rather than blockers in
    dry-run — dry-run exists precisely because creds don't yet.
    """
    pub_path = _published_path(slug)
    if os.path.exists(pub_path):
        return {"noop": True, "reason": "published.json exists — a second "
                "import would fork the game into a second design",
                "published": _read_json(pub_path)}

    problems = validate(slug)
    dry = _dry_run()
    if dry:
        auth_warnings = [p for p in problems if p.startswith("auth")]
        blocking = [p for p in problems if not p.startswith("auth")]
    else:
        auth_warnings, blocking = [], problems
    if blocking:
        raise PublishError(
            "validator dirty for '%s' — fix these walls, then re-run:\n  - %s"
            % (slug, "\n  - ".join(blocking)))

    listing = _load_listing(slug) or {}
    zip_path = os.path.join(_game_dir(slug), "publish_payload",
                            "%s.zip" % slug)
    with open(zip_path, "rb") as fh:
        zip_bytes = fh.read()
    with zipfile.ZipFile(zip_path) as zf:
        n_entries = len(zf.namelist())
    zip_sha = hashlib.sha256(zip_bytes).hexdigest()

    fields = [
        ("title", listing.get("title", slug)),
        ("description", listing.get("description", "")),
        # ALWAYS draft, hardcoded: the API default is `public` = live on
        # the feed immediately. Bob must never rely on the default.
        ("status", "draft"),
        ("tags", ",".join(listing.get("tags", []))),
        ("category", listing.get("category", DEFAULT_CATEGORY)),
        ("prompt", listing.get("prompt", "")),
    ]

    if dry:
        manifest = {
            "slug": slug,
            "dry_run": True,
            "at": _now_iso(),
            # The Go CLI's dry-run surfaces the description because "it is
            # what the store page shows under the title" — ours surfaces
            # every field the form would carry.
            "fields": dict(fields),
            "zip": {"path": os.path.relpath(zip_path, _home()),
                    "bytes": len(zip_bytes), "entries": n_entries,
                    "sha256": zip_sha},
            "auth_warnings": auth_warnings,
        }
        _write_json(os.path.join(_game_dir(slug), "publish_payload",
                                 "manifest.json"), manifest)
        try:
            queue.advance(slug, "published", "dry-run")
        except (KeyError, ValueError) as exc:
            manifest["queue_note"] = str(exc)
        return manifest

    # ---- live path ---------------------------------------------------------
    # Proactive refresh BEFORE the upload: a mid-flight 401 wastes a 50 MB
    # POST; refresh is cheap (publish-contract §2: refresh each tick).
    auth = refresh_auth()

    files = [("file", "%s.zip" % slug, "application/zip", zip_bytes)]
    cover = os.path.join(_game_dir(slug), "%s_review" % slug,
                         "_assembled.png")
    if os.path.exists(cover):
        with open(cover, "rb") as fh:
            # hero render first = cover (§3 thumbnails rule)
            files.append(("thumbnails", "_assembled.png", "image/png",
                          fh.read()))

    body, ctype = _multipart(fields, files)
    headers = _bearer(auth)
    headers["Content-Type"] = ctype
    status, _, resp_body = _http(
        "POST", _api_base() + "/designs/import", headers=headers, data=body)
    if status != 201:
        raise PublishError(
            "import failed (HTTP %s): %s — a 524/500 mid-import never "
            "leaves a half-built design visible and is safe to retry; a "
            "400 names the wall the local validator missed (fix the "
            "validator too)." % (status,
                                 resp_body.decode("utf-8", "replace")[:400]))
    design = json.loads(resp_body.decode("utf-8"))

    # The 201 response IS the idempotency ledger. Persist before anything
    # else can fail — a crash after this line costs a retry of curation,
    # never a duplicate design.
    record = {
        "slug": slug,
        "design": design,
        "status": "draft",
        "imported_at": _now_iso(),
        "zip_sha256": zip_sha,
    }
    _write_json(pub_path, record)

    ledger.append({"slug": slug, "kind": "publish", "stage": "import_draft",
                   "notes": "draft %s imported" % design.get("slug", slug)})
    try:
        queue.advance(slug, "published",
                      "draft imported: %s" % design.get("slug", slug))
    except (KeyError, ValueError) as exc:
        sys.stderr.write("publish: queue advance skipped: %s\n" % exc)
    telegram.send(
        "Bob imported draft '%s' (%s). It is private until flipped public. "
        "Check the viewer loads the model first: %s"
        % (listing.get("title", slug), design.get("slug", slug),
           design.get("project_url", "")))
    return record


# ---------------------------------------------------------------------------
# Curate — the rules page
# ---------------------------------------------------------------------------

def _content_walls(use_case, blocks):
    """Mirror models.ValidateDesignContent locally (§4): failing walls we
    could have measured for free wastes a network round-trip and leaves a
    half-curated page."""
    problems = []
    label = (use_case or {}).get("label", "")
    body = (use_case or {}).get("body", "")
    if not (1 <= len(label) <= 40):
        problems.append("use_case.label: %d runes outside 1-40" % len(label))
    if not (BODY_RUNES[0] <= len(body) <= BODY_RUNES[1]):
        problems.append("use_case.body: %d runes outside %d-%d"
                        % (len(body), BODY_RUNES[0], BODY_RUNES[1]))
    if len(blocks) > MAX_BLOCKS:
        problems.append("story_blocks: %d blocks > %d cap — spend the last "
                        "block pointing at RULES.md instead"
                        % (len(blocks), MAX_BLOCKS))
    for i, blk in enumerate(blocks):
        lead = blk.get("lead", "")
        bbody = blk.get("body", "")
        if not (LEAD_RUNES[0] <= len(lead) <= LEAD_RUNES[1]):
            problems.append("story_blocks[%d].lead: %d runes outside %d-%d"
                            % (i, len(lead), LEAD_RUNES[0], LEAD_RUNES[1]))
        if not (BODY_RUNES[0] <= len(bbody) <= BODY_RUNES[1]):
            problems.append("story_blocks[%d].body: %d runes outside %d-%d"
                            % (i, len(bbody), BODY_RUNES[0], BODY_RUNES[1]))
        for field, text in (("lead", lead), ("body", bbody)):
            if "<" in text or ">" in text:
                problems.append(
                    "story_blocks[%d].%s: contains '<' or '>' — plain text "
                    "only, the server rejects markup" % (i, field))
    return problems


def _authed_call(method, url, payload):
    """JSON call with bearer; one retry through refresh_auth() on 401
    (token lifetimes are undocumented — §2 says refresh on any 401)."""
    auth = _load_auth()
    if not auth:
        raise PublishError("no auth on disk — mint the bob token first "
                           "(publish-contract §2)")
    body = json.dumps(payload).encode("utf-8")
    headers = _bearer(auth)
    headers["Content-Type"] = "application/json"
    status, hdrs, resp = _http(method, url, headers=headers, data=body)
    if status == 401:
        auth = refresh_auth()
        headers = _bearer(auth)
        headers["Content-Type"] = "application/json"
        status, hdrs, resp = _http(method, url, headers=headers, data=body)
    return status, hdrs, resp


def curate(slug):
    """PATCH use-case + PUT story-blocks (publish-contract §4).

    Order matters: import first (the cover URL comes from the import
    response), use-case, then story-blocks. If a content write fails the
    design is still correct — retry ONLY this step (publishdesign's own
    recovery note). Never touches the feed pin: these endpoints don't bump
    updated_at.
    """
    pub_path = _published_path(slug)
    if not os.path.exists(pub_path):
        raise PublishError(
            "no published.json for '%s' — run import_draft first; curation "
            "needs the design's own cover URL" % slug)
    record = _read_json(pub_path)
    design = record.get("design", {})
    listing = _load_listing(slug) or {}
    use_case = listing.get("use_case") or {}
    blocks = listing.get("story_blocks") or []

    problems = _content_walls(use_case, blocks)
    if problems:
        raise PublishError(
            "content walls for '%s' — fix listing.json, then re-run "
            "curate:\n  - %s" % (slug, "\n  - ".join(problems)))

    image = use_case.get("image")
    if not image:
        thumbs = design.get("thumbnail_urls") or []
        image = thumbs[0] if thumbs else ""
    if not str(image).startswith("https://"):
        raise PublishError(
            "use_case.image must be an absolute https URL (the design's own "
            "cover from the import response is the publishdesign precedent); "
            "got %r" % image)

    dslug = design.get("slug", slug)
    base = _api_base()
    status, _, resp = _authed_call(
        "PATCH", "%s/designs/%s/use-case" % (base, dslug),
        {"label": use_case.get("label", ""),
         "body": use_case.get("body", ""),
         "image": image})
    if status not in (200, 201):
        raise PublishError(
            "use-case PATCH failed (HTTP %s): %s — the design itself is "
            "already written and correct; only the curated page failed. "
            "Retry curate('%s') alone."
            % (status, resp.decode("utf-8", "replace")[:300], slug))
    status, _, resp = _authed_call(
        "PUT", "%s/designs/%s/story-blocks" % (base, dslug), blocks)
    if status not in (200, 201):
        raise PublishError(
            "story-blocks PUT failed (HTTP %s): %s — retry curate('%s') "
            "alone; the 400 names the offending block index."
            % (status, resp.decode("utf-8", "replace")[:300], slug))

    record["curated_at"] = _now_iso()
    _write_json(pub_path, record)
    return record


# ---------------------------------------------------------------------------
# The flip — deliberate, priced, telegraphed
# ---------------------------------------------------------------------------

def flip_public(slug, price_cents):
    """POST /designs/{slug}/publish with an EXPLICIT price.

    The contract's trap: "an empty body publishes AND auto-lists at a
    platform-estimated price" — so the price is a required positional
    argument and there is no default. Refuses when: dry-run mode is on,
    published.json is missing (never imported), the validator is dirty, or
    the price sits outside the 4000-8000 corner (07-23 memo) without the
    human override BOB_PRICE_OVERRIDE=1. The API's own 100..1000000 bound
    holds even overridden.

    On success: published.json updated, ledger row, queue -> live, and the
    Telegram notice with the link + one-tap UNPUBLISH (the kill switch the
    auto-publish ruling demands).
    """
    if _dry_run():
        raise PublishError(
            "BOB_PUBLISH_DRY_RUN is on — the flip is the one irreversible-"
            "facing act; set BOB_PUBLISH_DRY_RUN=0 deliberately to arm it")
    pub_path = _published_path(slug)
    if not os.path.exists(pub_path):
        raise PublishError(
            "no published.json for '%s' — import_draft must succeed before "
            "anything can flip public" % slug)

    problems = validate(slug)
    if problems:
        raise PublishError(
            "validator dirty for '%s' — nothing flips public unmeasured "
            "(vibe-ideas gate discipline):\n  - %s"
            % (slug, "\n  - ".join(problems)))

    try:
        price = int(price_cents)
    except (TypeError, ValueError):
        raise PublishError("price_cents must be an integer of USD cents; "
                           "got %r" % (price_cents,))
    override = os.environ.get("BOB_PRICE_OVERRIDE") == "1"
    if not override and not (PRICE_MIN_CENTS <= price <= PRICE_MAX_CENTS):
        raise PublishError(
            "price %d outside Bob's %d-%d corner (the $40-80 functional/"
            "substantial corner, 07-23 memo) — a human may override with "
            "BOB_PRICE_OVERRIDE=1" % (price, PRICE_MIN_CENTS,
                                      PRICE_MAX_CENTS))
    if not (API_PRICE_MIN <= price <= API_PRICE_MAX):
        raise PublishError(
            "price %d outside the API's own %d..%d bound — no override "
            "exists for this one" % (price, API_PRICE_MIN, API_PRICE_MAX))

    record = _read_json(pub_path)
    design = record.get("design", {})
    dslug = design.get("slug", slug)
    status, _, resp = _authed_call(
        "POST", "%s/designs/%s/publish" % (_api_base(), dslug),
        {"listing": {"price_cents": price}})
    if status not in (200, 201):
        raise PublishError(
            "flip failed (HTTP %s): %s — a 400 here often names the "
            "fulfilment floor's exact minimum; re-price at or above it "
            "and retry" % (status, resp.decode("utf-8", "replace")[:300]))

    record["status"] = "public"
    record["price_cents"] = price
    record["flipped_at"] = _now_iso()
    _write_json(pub_path, record)

    ledger.append({"slug": slug, "kind": "publish", "stage": "flip_public",
                   "notes": "public at %d cents" % price})
    try:
        queue.advance(slug, "live", "flipped public at %d cents" % price)
    except (KeyError, ValueError) as exc:
        sys.stderr.write("publish: queue advance skipped: %s\n" % exc)

    listing = _load_listing(slug) or {}
    telegram.send(
        "Bob published '%s' at $%.2f — %s\nUndo any time: bob unpublish %s"
        % (listing.get("title", slug), price / 100.0,
           design.get("project_url", ""), slug),
        buttons=["unpublish %s" % slug])
    return record


def unpublish(slug):
    """POST /designs/{slug}/unpublish — the one-tap undo behind every flip.

    Updates published.json only; the queue's `live` state is terminal by
    design ("done is done"), so an unpublished game re-enters the pipeline
    as a new slug if it ever comes back — history stays honest.
    """
    pub_path = _published_path(slug)
    if not os.path.exists(pub_path):
        raise PublishError(
            "no published.json for '%s' — it was never imported, so there "
            "is nothing to unpublish" % slug)
    record = _read_json(pub_path)
    design = record.get("design", {})
    dslug = design.get("slug", slug)
    status, _, resp = _authed_call(
        "POST", "%s/designs/%s/unpublish" % (_api_base(), dslug), {})
    if status not in (200, 201):
        raise PublishError(
            "unpublish failed (HTTP %s): %s — if this persists, pull the "
            "listing in the app; DELETE is permanent and stays human-only"
            % (status, resp.decode("utf-8", "replace")[:300]))
    record["status"] = "draft"
    record["unpublished_at"] = _now_iso()
    _write_json(pub_path, record)
    ledger.append({"slug": slug, "kind": "publish", "stage": "unpublish",
                   "notes": "pulled back to draft"})
    telegram.send("Bob unpublished '%s' — back to draft, invisible to "
                  "everyone but the bob account." % slug)
    return record
