"""Novelty evidence — BGG candidates + corpus hits, packaged for the judge.

G4 novelty is the only gate that can KILL a game, and its kill rule is
evidentiary: "kill requires a URL the judge actually opened" (REWARD.md).
So this module's whole job is to hand the novelty judge real, openable
evidence — the top BGG matches with URLs, plus grep hits from Bob's own
corpus — and to be honest when it can't: network errors return a warning
row, never raise, and never fake an empty result as "nothing similar
exists" (an absent lookup is not a passing one; the judge must work from
corpus only AND SAY SO).

The judge itself lives in prompts; this module is deterministic plumbing
(CONTRACTS §6). All network goes through one `_http()` seam so tests
monkeypatch it — zero real BGG calls in tests.
"""

import hashlib
import html
import json
import os
import re
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# 24h cache (CONTRACTS §6): BGG's XML API is rate-limited and slow; a
# novelty question rarely changes within a day, and re-asking on every
# judge re-run would hammer a free community API for identical answers.
CACHE_TTL_S = 24 * 3600

# Top-5: the reward spec scores distance from *3 named nearest neighbors*;
# five candidates gives the judge slack to discard false matches and still
# name three.
TOP_N = 5

# 20s: BGG regularly takes 5-10s under load; a hung socket must not eat a
# tick, and the error path is a legal answer here.
HTTP_TIMEOUT_S = 20

SNIPPET_CHARS = 300  # enough to tell mechanism from theme, not a data dump

BGG_API = "https://boardgamegeek.com/xmlapi2"


def _home():
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _cache_dir():
    return os.path.join(_home(), "state", "bgg_cache")


def _now():
    return datetime.now(timezone.utc)


def _http(url):
    """GET one URL, return body bytes. THE network seam — tests monkeypatch
    this; nothing else in the module opens a socket. Raises on any
    transport/HTTP failure; bgg_candidates() converts that into a warning
    row (the contract: errors never raise past this module)."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "bob-novelty/1 (autonomous.ai)"})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return resp.read()
    except Exception:
        # curl fallback: sandboxed/tick environments with TLS interception
        # break urllib's cert chain (house lesson "curl, not urllib"; seen
        # live on g0001's first novelty run — SSL cert error, six UNKNOWNs).
        # curl honors the system trust store the interceptor patched.
        import subprocess
        r = subprocess.run(
            ["curl", "-sfL", "--max-time", str(int(HTTP_TIMEOUT_S)),
             "-A", "bob-novelty/1 (autonomous.ai)", url],
            capture_output=True, timeout=HTTP_TIMEOUT_S + 10)
        if r.returncode != 0 or not r.stdout:
            raise
        return r.stdout


def _atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.tmp.%s" % (path, uuid.uuid4().hex[:8])
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _cache_key(title, keywords):
    raw = ("%s|%s" % (title, ",".join(sorted(k.lower() for k in keywords)))
           ).lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _read_cache(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _cache_fresh(cached):
    """False on ANY failure — this runs before bgg_candidates' own
    try/except, and that function's contract is "never raises", so the
    subtraction lives inside the try too: a tz-naive fetched_at (a
    corrupted or externally-written cache row) would otherwise raise
    TypeError against the tz-aware _now() (review 2026-08-22)."""
    try:
        fetched = datetime.fromisoformat(cached["fetched_at"])
        if fetched.tzinfo is None:
            # Naive stamps are treated as UTC — our own writer always
            # stamps tz-aware UTC, so a naive one is foreign; assuming UTC
            # at worst mis-ages it, never crashes the judge path.
            fetched = fetched.replace(tzinfo=timezone.utc)
        return (_now() - fetched).total_seconds() < CACHE_TTL_S
    except (KeyError, TypeError, ValueError):
        return False


def _search_ids(query):
    """search?query=... -> ordered list of (bgg_id, name, year). XML from a
    trusted, fixed host; ElementTree is fine (no DTD/entity expansion in
    the xmlapi2 responses, and expat ignores external entities anyway)."""
    url = "%s/search?%s" % (BGG_API, urllib.parse.urlencode(
        {"query": query, "type": "boardgame"}))
    root = ET.fromstring(_http(url))
    out = []
    for item in root.findall("item"):
        bgg_id = item.get("id")
        name_el = item.find("name")
        year_el = item.find("yearpublished")
        if not bgg_id:
            continue
        out.append((
            bgg_id,
            name_el.get("value") if name_el is not None else "",
            year_el.get("value") if year_el is not None else None,
        ))
    return out


def _thing_descriptions(ids):
    """thing?id=a,b,c -> {id: description_snippet}. One batched call —
    BGG allows comma-joined ids and per-id calls would 5x the rate-limit
    exposure for nothing."""
    if not ids:
        return {}
    url = "%s/thing?%s" % (BGG_API, urllib.parse.urlencode(
        {"id": ",".join(ids)}))
    root = ET.fromstring(_http(url))
    out = {}
    for item in root.findall("item"):
        desc_el = item.find("description")
        text = html.unescape(desc_el.text or "") if desc_el is not None else ""
        text = re.sub(r"\s+", " ", text).strip()
        out[item.get("id")] = text[:SNIPPET_CHARS]
    return out


def bgg_candidates(title, keywords):
    """Top-5 BGG matches for a game: [{name, year, bgg_id, url,
    description_snippet}], cached 24h in state/bgg_cache/.

    Error contract (CONTRACTS §6): NEVER raises. On failure returns a list
    whose rows carry only a 'warning' key (no candidates were fetched) —
    plus any stale-cache candidates we still hold, because day-old
    neighbors beat no neighbors when the judge must name three. A caller
    telling candidates from warnings: candidates have 'bgg_id', warnings
    have 'warning'.
    """
    keywords = list(keywords or [])
    cache_path = os.path.join(_cache_dir(), _cache_key(title, keywords)
                              + ".json")
    cached = _read_cache(cache_path)
    if cached is not None and _cache_fresh(cached):
        return cached.get("candidates", [])

    try:
        found = _search_ids(title)
        # Thin title match? Widen with the first couple of keywords —
        # mechanism words find re-themed twins a title search never will
        # (the themed-skin test is about mechanism, not name).
        if len(found) < TOP_N:
            seen = set(i for i, _, _ in found)
            for kw in keywords[:2]:
                for row in _search_ids(kw):
                    if row[0] not in seen:
                        seen.add(row[0])
                        found.append(row)
                if len(found) >= TOP_N:
                    break
        found = found[:TOP_N]
        descs = _thing_descriptions([i for i, _, _ in found])
        candidates = []
        for bgg_id, name, year in found:
            candidates.append({
                "name": name,
                "year": int(year) if year and str(year).lstrip("-").isdigit()
                        else None,
                "bgg_id": bgg_id,
                # The URL the judge must actually open before a kill.
                "url": "https://boardgamegeek.com/boardgame/%s" % bgg_id,
                "description_snippet": descs.get(bgg_id, ""),
            })
        _atomic_write_json(cache_path, {
            "fetched_at": _now().isoformat(),
            "title": title,
            "keywords": keywords,
            "candidates": candidates,
        })
        return candidates
    except Exception as exc:  # noqa: broad on purpose — the contract is
        # "network errors return [] with a warning field, never raise";
        # any exception past _http/ET here IS a lookup failure.
        warning = {"warning": (
            "BGG lookup failed (%s: %s) — novelty judge must work from "
            "corpus only and say so; a kill still requires a URL, so no "
            "kill can come from this run's web evidence."
            % (type(exc).__name__, exc))}
        if cached is not None and cached.get("candidates"):
            stale = list(cached["candidates"])
            stale.append({"warning": (
                "serving stale cache from %s (older than 24h) because the "
                "live lookup failed" % cached.get("fetched_at", "?"))})
            return stale
        return [warning]


def _corpus_hits(terms):
    """Grep corpus/INDEX.md for any term; return matching lines with their
    line numbers so the judge can pull the full card. INDEX.md is the
    scholar loop's product — missing file just means the corpus is young,
    which the evidence file states rather than hides."""
    path = os.path.join(_home(), "corpus", "INDEX.md")
    if not os.path.exists(path):
        return [], "corpus/INDEX.md missing — scholar loop has not built " \
                   "the index yet; corpus evidence unavailable"
    terms = [t.lower() for t in terms if len(t) >= 4]
    hits = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            low = line.lower()
            matched = [t for t in terms if t in low]
            if matched:
                hits.append({"line_no": lineno, "line": line.rstrip("\n"),
                             "terms": matched})
            if len(hits) >= 40:
                # 40 lines is already more neighbors than any judge can
                # weigh; past that the evidence file becomes noise.
                break
    return hits, None


def build_novelty_evidence(slug):
    """Package the judge's evidence file:
    games/<slug>/review/novelty_evidence.json.

    Carries the sha256 of the game doc it evidences — every verdict
    artifact embeds the hash of what it judged (vibe-ideas got burned
    twice by mtime-only staleness checks), so a judge reading this file
    against a since-edited game.json can refuse it as stale.
    """
    gdir = os.path.join(_home(), "games", slug)
    doc_path = os.path.join(gdir, "game.json")  # budgets.GAME_DOC
    doc, doc_sha = {}, None
    if os.path.exists(doc_path):
        with open(doc_path, "rb") as fh:
            raw = fh.read()
        doc_sha = hashlib.sha256(raw).hexdigest()
        try:
            doc = json.loads(raw.decode("utf-8"))
        except ValueError:
            doc = {}

    title = doc.get("title") or slug.replace("-", " ")
    # Mechanism words, not theme words: the themed-skin test scores
    # mechanism distance, so the search terms are action types and declared
    # mechanisms first, explicit keywords second.
    keywords = []
    for key in ("action_types", "mechanisms", "keywords"):
        val = doc.get(key) or []
        keywords.extend(str(v) for v in val if v)

    raw_rows = bgg_candidates(title, keywords)
    candidates = [r for r in raw_rows if "bgg_id" in r]
    warnings = [r["warning"] for r in raw_rows if "warning" in r]

    terms = list(keywords) + [w for w in re.split(r"[^A-Za-z0-9]+", title)
                              if w]
    hits, corpus_warning = _corpus_hits(terms)
    if corpus_warning:
        warnings.append(corpus_warning)

    evidence = {
        "slug": slug,
        "title": title,
        "game_doc_sha256": doc_sha,
        "generated_at": _now().isoformat(),
        "bgg_candidates": candidates,
        "corpus_hits": hits,
        "warnings": warnings,
        "search_terms": {"title": title, "keywords": keywords},
    }
    out_path = os.path.join(gdir, "review", "novelty_evidence.json")
    _atomic_write_json(out_path, evidence)
    return evidence
