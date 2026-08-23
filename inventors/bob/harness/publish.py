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
   creates two designs" — Foundation's SQLite outbox records the packet-bound intent
   before HTTP and blocks retries after any ambiguous result. The historical
   games/<slug>/published.json remains Bob's human-readable projection.
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
import urllib.parse
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from harness import core_runtime, ledger, queue, telegram

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
MAX_HTTP_RESPONSE_BYTES = 2 * 1024 * 1024

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
    "published.json",    # Bob's publication projection is about the design,
    "listing.json",      # and the metadata IS the form fields — neither
                         # belongs inside the artifact they describe
])
STRIP_SUFFIXES = (".jsonl", ".pem", ".key")
STRIP_PREFIXES = (".env", "secrets.")

AUTH_FILE = "panda-auth.json"    # state/panda-auth.json, chmod 600
CORE_STATE_FILE = "inventor-core.sqlite3"
DEFAULT_CATEGORY = "toys-games"  # publish-contract §10 open item 1: picked
                                 # deliberately instead of publish.py's
                                 # sloppy first-active fallback; listing.json
                                 # may override once ops confirms the slug.


class PublishError(Exception):
    """Raised when publishing cannot proceed. The message always says what
    to do next (CONTRACTS §6) — a bare traceback teaches the 3am log reader
    nothing."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward Bob's bearer through an HTTP redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


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


def _core_store_path():
    return os.path.join(_home(), "state", CORE_STATE_FILE)


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


def _require_core():
    try:
        return core_runtime.require_core()
    except core_runtime.CoreUnavailable as exc:
        raise PublishError(
            "Inventor Foundation is unavailable — publication cannot safely "
            "continue: %s" % exc
        ) from exc


def _core_packet_identity(zip_path):
    runtime = _require_core()
    try:
        identity = runtime.inspect_publish_packet(Path(zip_path))
    except Exception as exc:
        raise PublishError(
            "core rejected publish packet %s: %s" % (zip_path, exc)
        ) from exc
    return dict(identity)


def _core_allowed_origins():
    configured = os.environ.get(
        "BOB_PANDA_ALLOWED_ORIGINS",
        "https://panda-social-api.autonomous.ai",
    )
    origins = tuple(item.strip() for item in configured.split(",") if item.strip())
    if not origins:
        raise PublishError("BOB_PANDA_ALLOWED_ORIGINS must pin at least one HTTPS origin")
    return origins


def _core_owner(auth):
    pinned = auth.get("bob_user_id")
    actual = (auth.get("user") or {}).get("id")
    if not pinned or not actual or pinned != actual:
        raise PublishError(
            "core publication requires Bob's non-empty pinned owner id to "
            "match the authenticated user; set BOB_FACTORY_USER_ID for an "
            "operator bearer or repair state/%s" % AUTH_FILE
        )
    return pinned


def _core_transport(runtime):
    def transport(method, url, headers, body, timeout):
        status, response_headers, response_body = _http(
            method, url, headers=dict(headers), data=body, timeout=timeout
        )
        return runtime.HttpResponse(status, response_headers, response_body)

    return transport


def _validated_core_api_base():
    """Return the API base only after core has pinned its HTTPS origin.

    Authentication refresh is itself a credential-bearing network effect.  It
    therefore has to pass the same origin contract as design import/publish,
    before the refresh token is placed in a request body.
    """
    runtime = _require_core()
    try:
        client = runtime.PandaClient(
            "origin-validation-only",
            api_base=_api_base(),
            transport=_core_transport(runtime),
            allowed_origins=_core_allowed_origins(),
        )
    except Exception as exc:
        raise PublishError(
            "Panda API origin is not an allowed HTTPS endpoint: %s" % exc
        ) from exc
    return client.api_base


def _validated_panda_url(url):
    """Require one credential-bearing URL to stay below the pinned API base."""
    api_base = _validated_core_api_base()
    try:
        expected = urllib.parse.urlsplit(api_base)
        candidate = urllib.parse.urlsplit(url)
    except (TypeError, ValueError) as exc:
        raise PublishError("Panda request URL is malformed") from exc
    base_path = expected.path.rstrip("/")
    if (
        candidate.scheme != expected.scheme
        or candidate.netloc != expected.netloc
        or candidate.username is not None
        or candidate.password is not None
        or candidate.query
        or candidate.fragment
        or not candidate.path.startswith(base_path + "/")
    ):
        raise PublishError(
            "credential-bearing Panda request escaped the pinned API base"
        )
    return urllib.parse.urlunsplit(candidate)


def _core_publication_context(auth):
    runtime = _require_core()
    owner = _core_owner(auth)
    token = auth.get("access_token")
    if not isinstance(token, str) or not token:
        raise PublishError("Bob's authenticated access token is empty")
    try:
        store = runtime.InventorStore(Path(_core_store_path()))
        client = runtime.PandaClient(
            token,
            api_base=_api_base(),
            transport=_core_transport(runtime),
            allowed_origins=_core_allowed_origins(),
        )
        coordinator = runtime.PandaPublicationCoordinator(store, client, owner)
    except Exception as exc:
        raise PublishError("could not initialize core publication runtime: %s" % exc) from exc
    return runtime, store, coordinator, owner


def _core_product_id(slug):
    if not isinstance(slug, str) or not slug:
        raise PublishError("Bob publication slug must be a non-empty string")
    return "bob:%s" % hashlib.sha256(slug.encode("utf-8")).hexdigest()


def _core_product(store, runtime, slug, artifact_sha):
    # Stable logical identity is essential: including artifact_sha here would
    # let changed source allocate a fresh product and bypass an UNKNOWN import
    # intent for the same marketplace game.
    product_id = _core_product_id(slug)
    try:
        product = store.get_product(product_id)
    except KeyError:
        try:
            product = store.register_product(
                product_id,
                "reviewed",
                metadata={"inventor_id": "bob", "slug": slug},
                artifact_sha256=artifact_sha,
            )
        except runtime.StateConflict:
            product = store.get_product(product_id)
    if product.get("artifact_sha256") != artifact_sha:
        raise PublishError(
            "core product for '%s' is already bound to different artifact "
            "bytes; corrected bytes require a new slug because an earlier "
            "non-idempotent import may have reached Panda" % slug
        )
    return product_id


def _bound_core_intent(store, slug, identity, owner=None, api_origin=None):
    """Resolve publication truth from core, never from ``published.json``.

    The JSON file beside a game is an operator-facing projection.  It can be
    stale, partially written after a crash, or edited.  The durable product and
    intent are keyed from Bob's logical slug and must identify the exact packet
    currently present before a public result can be recorded locally.
    """
    product_id = _core_product_id(slug)
    try:
        product = store.get_product(product_id)
    except KeyError as exc:
        raise PublishError(
            "core has no publication product for '%s'; import its draft first"
            % slug
        ) from exc
    if product.get("artifact_sha256") != identity.get("artifact_sha256"):
        raise PublishError(
            "current game files do not match the exact artifact bound to core product "
            "%s" % product_id
        )
    try:
        intent = store.latest_publish_intent(product_id)
    except AttributeError as exc:
        raise PublishError(
            "Foundation lacks the public latest_publish_intent contract"
        ) from exc
    if intent is None:
        raise PublishError(
            "core has no publication intent for '%s'; import its draft first"
            % slug
        )
    request = intent.get("request")
    if not isinstance(request, dict):
        raise PublishError("core publication intent has no persisted request")
    if (
        intent.get("product_id") != product_id
        or intent.get("packet_sha256") != identity.get("packet_sha256")
        or request.get("_core_artifact_sha256")
        != identity.get("artifact_sha256")
    ):
        raise PublishError(
            "current core packet does not match the slug-bound persisted intent; "
            "refusing artifact drift"
        )
    if owner is not None and request.get("_core_owner_id") != owner:
        raise PublishError(
            "core publication intent belongs to a different Panda owner"
        )
    if api_origin is not None and request.get("_core_api_origin") != api_origin:
        raise PublishError(
            "core publication intent belongs to a different Panda API origin"
        )
    return product_id, intent


def _core_metadata(slug, listing):
    metadata = {
        "title": listing.get("title", slug),
        "status": "draft",
        "tags": list(listing.get("tags", [])),
    }
    optional = {
        "description": listing.get("description"),
        "category": listing.get("category", DEFAULT_CATEGORY),
        "prompt": listing.get("prompt"),
        "license": listing.get("license"),
    }
    for name, value in optional.items():
        if value:
            metadata[name] = value
    return metadata


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
        opener = urllib.request.build_opener(_NoRedirectHandler())
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read(MAX_HTTP_RESPONSE_BYTES + 1)
            if len(body) > MAX_HTTP_RESPONSE_BYTES:
                raise PublishError("Panda response exceeds the 2 MB safety limit")
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(MAX_HTTP_RESPONSE_BYTES + 1)
            if len(body) > MAX_HTTP_RESPONSE_BYTES:
                raise PublishError(
                    "Panda error response exceeds the 2 MB safety limit"
                )
            headers = dict(exc.headers or {})
        finally:
            exc.close()
        return exc.code, headers, body
    except urllib.error.URLError as exc:
        # TLS interception breaks urllib's cert chain on this machine (the
        # house lesson: "curl, not urllib" — same wound the novelty client
        # hit, and the reason g0003's first real import died at the wire).
        # curl honours the system trust store the interceptor patched, so
        # it is the working transport, not a workaround.
        if "CERTIFICATE_VERIFY" not in str(exc) and "SSL" not in str(exc):
            raise
        return _http_curl(method, url, headers=headers, data=data,
                          timeout=timeout)


def _http_curl(method, url, headers=None, data=None, timeout=HTTP_TIMEOUT_S):
    """curl transport for the same seam: (status, headers_dict, body).

    Request and response bodies use private temp files so multipart bytes do
    not hit argv limits and an untrusted response is never buffered without a
    bound. Headers use a private config file so bearer tokens do not appear in
    the process list.
    """
    import subprocess
    import tempfile

    argv = [
        "curl", "-sS", "-X", method,
        "--max-time", str(int(timeout)),
        "--max-filesize", str(MAX_HTTP_RESPONSE_BYTES),
        "--write-out", "%{http_code}",
    ]
    request_tmp = None
    response_tmp = None
    headers_tmp = None
    try:
        response_fd, response_tmp = tempfile.mkstemp(suffix=".response")
        os.close(response_fd)
        argv += ["--output", response_tmp]
        if headers:
            headers_fd, headers_tmp = tempfile.mkstemp(suffix=".headers")
            with os.fdopen(headers_fd, "w", encoding="utf-8") as fh:
                for key, val in headers.items():
                    fh.write("%s: %s\n" % (key, val))
            argv += ["--header", "@" + headers_tmp]
        if data:
            request_fd, request_tmp = tempfile.mkstemp(suffix=".body")
            with os.fdopen(request_fd, "wb") as fh:
                fh.write(data)
            argv += ["--data-binary", "@" + request_tmp]
        argv.append(url)
        proc = subprocess.run(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout + 30,
        )
        if proc.returncode == 63:
            raise PublishError("Panda response exceeds the 2 MB safety limit")
        if proc.returncode != 0:
            raise urllib.error.URLError(
                "curl transport failed (rc=%d): %s"
                % (proc.returncode,
                   proc.stderr.decode("utf-8", "replace")[-300:]))
        try:
            status = int(proc.stdout.strip())
        except ValueError as exc:
            raise urllib.error.URLError(
                "curl transport returned an invalid HTTP status"
            ) from exc
        with open(response_tmp, "rb") as fh:
            body = fh.read(MAX_HTTP_RESPONSE_BYTES + 1)
        if len(body) > MAX_HTTP_RESPONSE_BYTES:
            raise PublishError("Panda response exceeds the 2 MB safety limit")
        return status, {}, body
    finally:
        for tmp in (request_tmp, response_tmp, headers_tmp):
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)


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
    api_base = _validated_core_api_base()
    body = json.dumps({"refresh_token": auth["refresh_token"]}).encode()
    status, _, resp_body = _http(
        "POST", api_base + "/auth/refresh",
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


def _fresh_core_auth():
    """Refresh a minted account before a core effect; keep session bearers in memory."""
    auth = _load_auth()
    if not auth:
        raise PublishError("no auth on disk — mint the bob token first")
    if auth.get("source") == "env:BOB_FACTORY_TOKEN":
        return auth
    return refresh_auth()


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

    Rebuilds the core packet every run: validation must measure the current
    game tree, never a stale publish_payload left by an earlier tick.
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

    # -- the canonical core packet ------------------------------------------
    zip_path = os.path.join(gdir, "publish_payload", "%s.zip" % slug)
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
            identity = _core_packet_identity(zip_path)
        except (OSError, PublishError, zipfile.BadZipFile) as exc:
            identity = None
            problems.append(
                "zip: not an exact canonical core packet — rebuild with "
                "build_zip('%s'): %s" % (slug, exc)
            )
        if identity is not None and identity["entries"] > MAX_ZIP_ENTRIES:
            problems.append("zip: %d entries > %d backend cap"
                            % (identity["entries"], MAX_ZIP_ENTRIES))

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
    """Assemble games/<slug>/publish_payload/<slug>.zip through core.

    Bob chooses which product files ship, while Foundation owns the byte
    contract: no-follow regular-file staging, credential scanning, a
    content-addressed ``_inventor-artifact.json``, fixed ZIP metadata, and an
    exact packet hash. The project lives at the archive root, which Panda's
    importer accepts and which avoids pretending the core manifest is a
    second design folder.
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
        kept_dirs = []
        for dirname in sorted(dirs):
            if (dirname in STRIP_DIRS or dirname.startswith(".env")
                    or dirname.startswith(".")):
                continue
            directory_path = os.path.join(root, dirname)
            if os.path.islink(directory_path):
                raise PublishError(
                    "publishable artifact directory is a symlink: %s"
                    % os.path.relpath(directory_path, gdir)
                )
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs
        for name in sorted(files):
            if not _keep_entry(rel_parts, name):
                continue
            full = os.path.join(root, name)
            relative = "/".join(rel_parts + [name])
            entries.append((Path(full), relative))

    try:
        core_runtime.build_game_packet(
            entries, Path(zip_path), maximum_bytes=MAX_ZIP_BYTES
        )
    except Exception as exc:
        raise PublishError(
            "core could not build the publish packet for '%s': %s" % (slug, exc)
        ) from exc
    return zip_path


def core_packet_identity(slug):
    """Return Foundation's verified identity for Bob's current publish packet."""
    path = os.path.join(_game_dir(slug), "publish_payload", "%s.zip" % slug)
    if not os.path.exists(path):
        path = build_zip(slug)
    return _core_packet_identity(path)


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

def _is_non_authoritative_dry_projection(record):
    """Recognize Bob's no-effect rehearsal marker, never a remote receipt.

    Current writers stamp ``publication_authority=none`` explicitly.  The
    structural fallback accepts Bob's older dry stubs, which predate that
    field, only when they contain neither a design nor a core intent.
    """
    if not isinstance(record, dict) or record.get("dry_run") is not True:
        return False
    if record.get("publication_authority") not in (None, "none"):
        return False
    return not record.get("core_intent_id") and not record.get("design")


def _require_core_authority_for_existing_effect(slug, record):
    """Reject a remote receipt that predates Bob's durable core intent.

    A Panda design id proves that *an* effect happened, but without the local
    intent and content hashes it cannot prove which bytes were sent or grant
    Bob authority over the remote owner. Such a receipt must stay stranded;
    deleting it and retrying the same slug could create a duplicate design.
    """
    required = (
        "core_intent_id", "core_product_id", "core_artifact_sha256",
        "zip_sha256",
    )
    if (
        all(isinstance(record.get(name), str) and record.get(name)
            for name in required[:2])
        and all(isinstance(record.get(name), str)
                and re.fullmatch(r"[0-9a-f]{64}", record[name])
                for name in required[2:])
    ):
        return

    design = record.get("design") if isinstance(record.get("design"), dict) \
        else record
    author = design.get("author") if isinstance(design.get("author"), dict) \
        else {}
    design_id = design.get("id") or design.get("design_id") or "unknown"
    owner_id = design.get("owner_id") or author.get("id") or \
        record.get("owner_id") or "unknown"
    owner_name = author.get("display_name") or author.get("username")
    owner = "%s (%s)" % (owner_name, owner_id) if owner_name else owner_id
    raise PublishError(
        "legacy pre-core published.json for '%s' records Panda design %s "
        "owned by %s, but has no complete core intent/content identity. "
        "Bob cannot adopt, reconcile, or safely retry that effect. Have its "
        "current owner resolve, unpublish, or archive the legacy draft "
        "separately; provision and pin a distinct Bob marketplace principal; "
        "then re-import the product under a new slug so core records the "
        "first effect. Do not delete this receipt and retry the same slug."
        % (slug, design_id, owner)
    )


def import_draft(slug):
    """Import the game as a DRAFT design. The one function that moves bytes
    to the marketplace.

    A fully Foundation-backed games/<slug>/published.json is a compatibility no-op.
    A remote pre-core receipt is stranded with an actionable error because its
    owner, intent, and bytes cannot be adopted safely. A dry-run projection is
    explicitly non-authoritative: when real effects are armed it does not
    suppress the first Foundation-backed import. The crash-safe guard is Foundation's
    packet-bound SQLite outbox, which records the effect before HTTP and
    permanently blocks an ambiguous retry.

    Dry-run (default): validate + build_zip + write
    publish_payload/manifest.json, advance the queue with note 'dry-run',
    stop. Auth walls are recorded as warnings rather than blockers in
    dry-run — dry-run exists precisely because creds don't yet.
    """
    pub_path = _published_path(slug)
    dry = _dry_run()
    if os.path.exists(pub_path):
        existing_projection = _read_json(pub_path)
        non_authoritative = _is_non_authoritative_dry_projection(
            existing_projection
        )
        if not non_authoritative:
            _require_core_authority_for_existing_effect(
                slug, existing_projection
            )
        if dry or not non_authoritative:
            return {"noop": True, "reason": "published.json represents an "
                    "existing Foundation-bound effect or the current dry run — a "
                    "second import "
                    "would fork the game into a second design",
                    "published": existing_projection}

    problems = validate(slug)
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
    # Rebuild once more at the effect boundary. The content validators above
    # may take time, and a generator could otherwise leave us uploading the
    # packet they inspected instead of the game tree that exists now.
    zip_path = build_zip(slug)
    identity = _core_packet_identity(zip_path)
    n_entries = identity["entries"]
    zip_sha = identity["packet_sha256"]

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
            "publication_authority": "none",
            "at": _now_iso(),
            # The Go CLI's dry-run surfaces the description because "it is
            # what the store page shows under the title" — ours surfaces
            # every field the form would carry.
            "fields": dict(fields),
            "zip": {"path": os.path.relpath(zip_path, _home()),
                    "bytes": identity["bytes"], "entries": n_entries,
                    "sha256": zip_sha,
                    "artifact_sha256": identity["artifact_sha256"],
                    "contract": "inventor_core.artifacts/v1"},
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
    auth = _fresh_core_auth()
    runtime, store, coordinator, _owner = _core_publication_context(auth)
    product_id = _core_product(
        store, runtime, slug, identity["artifact_sha256"]
    )
    try:
        outcome = coordinator.import_draft(
            product_id, Path(zip_path), _core_metadata(slug, listing)
        )
    except runtime.AmbiguousPublishError as exc:
        raise PublishError(
            "%s — core recorded the unknown import in %s and blocks every "
            "retry; Panda must expose content/idempotency proof before this "
            "packet can be reconciled" % (exc, _core_store_path())
        ) from exc
    except (runtime.CorePublishError, runtime.ContractError,
            runtime.StateConflict) as exc:
        raise PublishError("core publication refused the draft import: %s" % exc) from exc

    intent = store.get_publish_intent(outcome.intent_id)
    design = intent.get("response") or {
        "id": outcome.receipt.design_id,
        "slug": outcome.receipt.slug,
        "owner_id": outcome.receipt.owner_id,
        "root_id": outcome.receipt.root_id,
        "current_history_id": outcome.receipt.current_history_id,
        "published_history_id": outcome.receipt.published_history_id,
        "status": outcome.receipt.status,
        "project_url": outcome.receipt.project_url,
    }

    # The 201 response IS the idempotency ledger. Persist before anything
    # else can fail — a crash after this line costs a retry of curation,
    # never a duplicate design.
    record = {
        "slug": slug,
        "design": design,
        "status": "draft",
        "imported_at": _now_iso(),
        "zip_sha256": zip_sha,
        "core_intent_id": outcome.intent_id,
        "core_product_id": product_id,
        "core_artifact_sha256": identity["artifact_sha256"],
        "core_store": os.path.relpath(_core_store_path(), _home()),
        "draft_receipt": outcome.receipt.to_dict(),
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
    url = _validated_panda_url(url)
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


def _authed_get(url):
    """Authenticated readback with the same one-refresh rule as JSON writes."""
    url = _validated_panda_url(url)
    auth = _load_auth()
    if not auth:
        raise PublishError("no auth on disk — mint the bob token first "
                           "(publish-contract §2)")
    status, hdrs, resp = _http("GET", url, headers=_bearer(auth))
    if status == 401:
        auth = refresh_auth()
        status, hdrs, resp = _http("GET", url, headers=_bearer(auth))
    return status, hdrs, resp


def _public_readback(slug, record):
    """Return an authenticated design receipt or fail closed.

    HTTP success from /publish proves only that a request returned. `live`
    requires the remote design to identify Bob's account and report that its
    exact current history entry is the published history entry.
    """
    local = record.get("design") or {}
    dslug = local.get("slug", slug)
    status, _, body = _authed_get(
        "%s/designs/%s" % (_api_base(), dslug))
    if status != 200:
        raise PublishError(
            "public readback failed (HTTP %s): %s — outcome is ambiguous; "
            "do not POST publish again. Run `bob reconcile-public %s`."
            % (status, body.decode("utf-8", "replace")[:300], slug))
    try:
        remote = json.loads(body.decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError) as exc:
        raise PublishError(
            "public readback returned invalid JSON (%s) — outcome is "
            "ambiguous; run `bob reconcile-public %s`" % (exc, slug))
    if not isinstance(remote, dict):
        raise PublishError("public readback was not a design object")
    for field in ("id", "root_id"):
        if local.get(field) and remote.get(field) != local.get(field):
            raise PublishError(
                "public readback %s %r does not match imported design %r"
                % (field, remote.get(field), local.get(field)))
    auth = _load_auth() or {}
    expected_owner = auth.get("bob_user_id") or \
        (auth.get("user") or {}).get("id")
    remote_owner = remote.get("owner_id") or \
        (remote.get("author") or {}).get("id")
    if not expected_owner or remote_owner != expected_owner:
        raise PublishError(
            "public readback owner %r does not match Bob's pinned account %r"
            % (remote_owner, expected_owner))
    current = remote.get("current_history_id")
    published = remote.get("published_history_id")
    if remote.get("status") != "public" or not current or published != current:
        raise PublishError(
            "public readback did not prove the current version live "
            "(status=%r current_history_id=%r published_history_id=%r) — "
            "run `bob reconcile-public %s` after the platform settles"
            % (remote.get("status"), current, published, slug))
    if not str(remote.get("project_url") or "").startswith("https://"):
        raise PublishError("public readback lacks an HTTPS project_url")
    return remote


def _record_verified_live(slug, record, remote, price=None):
    now = _now_iso()
    record["design"] = remote
    record["status"] = "public"
    if price is not None:
        record["price_cents"] = price
    record["flipped_at"] = record.get("flipped_at") or now
    record["verified_public_at"] = now
    record["publication_receipt"] = {
        key: remote.get(key) for key in (
            "id", "slug", "owner_id", "root_id", "current_history_id",
            "published_history_id", "status", "project_url")
    }
    record["flip_intent"] = {
        "state": "succeeded", "verified_at": now,
        "price_cents": record.get("price_cents"),
    }
    _write_json(_published_path(slug), record)
    try:
        current_state = (queue.load().get("games", {}).get(slug) or {}).get("state")
        if current_state == "published":
            queue.advance(slug, "live", "authenticated public readback")
    except (KeyError, ValueError) as exc:
        sys.stderr.write("publish: queue advance skipped: %s\n" % exc)
    return record


def _design_from_core_receipt(receipt, previous=None):
    """Translate Foundation's typed receipt back to Bob's long-lived JSON surface."""
    previous = previous or {}
    design = {
        "id": receipt.design_id,
        "slug": receipt.slug,
        "owner_id": receipt.owner_id,
        "root_id": receipt.root_id,
        "current_history_id": receipt.current_history_id,
        "published_history_id": receipt.published_history_id,
        "status": receipt.status,
        "project_url": receipt.project_url,
    }
    if previous.get("thumbnail_urls"):
        design["thumbnail_urls"] = previous["thumbnail_urls"]
    if receipt.listing_active is not None:
        design["listing"] = {
            "active": receipt.listing_active,
            "price_cents": receipt.listing_price_cents,
            "currency": receipt.listing_currency,
            "sku": receipt.listing_sku,
        }
    return design


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
    # The endpoint takes an OBJECT wrapping the array, not a bare array —
    # a bare list returns 400 "cannot unmarshal array into
    # apis.storyBlocksReq" (measured against the live API 2026-08-23 while
    # importing Clearance).
    status, _, resp = _authed_call(
        "PUT", "%s/designs/%s/story-blocks" % (base, dslug),
        {"story_blocks": blocks})
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
    # Rebuild before consulting the outbox.  This is the current product, not a
    # possibly stale publish_payload left by an earlier validation pass.
    build_zip(slug)
    current_identity = core_packet_identity(slug)
    runtime = _require_core()
    local_store = runtime.InventorStore(Path(_core_store_path()))
    core_product_id, intent = _bound_core_intent(
        local_store, slug, current_identity
    )
    core_intent_id = intent["id"]
    projected_intent_id = record.get("core_intent_id")
    if projected_intent_id and projected_intent_id != core_intent_id:
        raise PublishError(
            "published.json points at a different intent than the slug-bound "
            "core outbox; refusing the mutable projection"
        )
    auth = _fresh_core_auth()
    runtime, store, coordinator, owner = _core_publication_context(auth)
    core_product_id, persisted_intent = _bound_core_intent(
        store,
        slug,
        current_identity,
        owner=owner,
        api_origin=coordinator.client.api_origin,
    )
    if persisted_intent["id"] != core_intent_id:
        raise PublishError("slug-bound core intent changed during publication setup")
    if persisted_intent.get("state") == "live":
        live_request = persisted_intent.get("live_request") or {}
        listing_request = live_request.get("listing") or {}
        if listing_request.get("price_cents") != price:
            raise PublishError(
                "core already recorded this intent live at a different price"
            )
    record["flip_intent"] = {
        "state": "sending", "started_at": _now_iso(), "price_cents": price,
        "core_intent_id": core_intent_id,
    }
    _write_json(pub_path, record)
    try:
        receipt = coordinator.publish_live(core_intent_id, price)
    except runtime.AmbiguousPublishError as exc:
        record["flip_intent"]["state"] = "unknown"
        record["flip_intent"]["failed_at"] = _now_iso()
        _write_json(pub_path, record)
        raise PublishError(
            "%s — do not POST publish again; run `bob reconcile-public %s`"
            % (exc, slug)
        ) from exc
    except (runtime.CorePublishError, runtime.ContractError,
            runtime.StateConflict) as exc:
        record["flip_intent"]["state"] = "rejected"
        record["flip_intent"]["failed_at"] = _now_iso()
        _write_json(pub_path, record)
        raise PublishError("core publication refused the public flip: %s" % exc) from exc

    remote = _design_from_core_receipt(receipt, record.get("design"))
    record = _record_verified_live(slug, record, remote, price=price)
    record["core_intent_id"] = core_intent_id
    record["core_product_id"] = core_product_id
    record["core_artifact_sha256"] = current_identity["artifact_sha256"]
    record["zip_sha256"] = current_identity["packet_sha256"]
    record["publication_receipt"] = receipt.to_dict()
    record["flip_intent"]["core_intent_id"] = core_intent_id
    _write_json(pub_path, record)
    design = remote

    ledger.append({"slug": slug, "kind": "publish", "stage": "flip_public",
                   "notes": "verified public at %d cents" % price})

    listing = _load_listing(slug) or {}
    telegram.send(
        "Bob published '%s' at $%.2f — %s\nUndo any time: bob unpublish %s"
        % (listing.get("title", slug), price / 100.0,
           design.get("project_url", ""), slug),
        buttons=["unpublish %s" % slug])
    return record


def reconcile_public(slug):
    """Reconcile a Foundation-recorded ambiguous public flip by authenticated GET.

    This command may rotate auth, but never sends /publish, so it is safe after
    a timeout or crash. A human click without the persisted core price intent
    cannot satisfy the exact-listing receipt and remains deliberately blocked.
    """
    pub_path = _published_path(slug)
    if not os.path.exists(pub_path):
        raise PublishError("no published.json for '%s' — nothing to reconcile"
                           % slug)
    record = _read_json(pub_path)
    build_zip(slug)
    current_identity = core_packet_identity(slug)
    runtime = _require_core()
    local_store = runtime.InventorStore(Path(_core_store_path()))
    core_product_id, intent = _bound_core_intent(
        local_store, slug, current_identity
    )
    core_intent_id = intent["id"]
    projected_intent_id = record.get("core_intent_id")
    if projected_intent_id and projected_intent_id != core_intent_id:
        raise PublishError(
            "published.json points at a different intent than the slug-bound "
            "core outbox; refusing the mutable projection"
        )
    auth = _fresh_core_auth()
    runtime, store, coordinator, owner = _core_publication_context(auth)
    core_product_id, intent = _bound_core_intent(
        store,
        slug,
        current_identity,
        owner=owner,
        api_origin=coordinator.client.api_origin,
    )
    if intent["id"] != core_intent_id:
        raise PublishError("slug-bound core intent changed during reconciliation setup")
    try:
        if intent["state"] == "live":
            receipt = runtime.PublicationReceipt(**intent["receipt"])
            receipt.assert_owner(owner)
        else:
            receipt = coordinator.reconcile_live(core_intent_id)
    except runtime.AmbiguousPublishError as exc:
        raise PublishError(
            "%s — the exact core live intent remains ambiguous" % exc
        ) from exc
    except (runtime.CorePublishError, runtime.ContractError,
            runtime.StateConflict, KeyError) as exc:
        raise PublishError("core cannot reconcile the public flip: %s" % exc) from exc
    remote = _design_from_core_receipt(receipt, record.get("design"))
    record = _record_verified_live(
        slug, record, remote, price=receipt.listing_price_cents)
    record["core_intent_id"] = core_intent_id
    record["core_product_id"] = core_product_id
    record["core_artifact_sha256"] = current_identity["artifact_sha256"]
    record["zip_sha256"] = current_identity["packet_sha256"]
    record["publication_receipt"] = receipt.to_dict()
    _write_json(pub_path, record)
    ledger.append({"slug": slug, "kind": "publish",
                   "stage": "reconcile_public",
                   "notes": "authenticated readback proved public"})
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
