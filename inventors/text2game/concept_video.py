#!/usr/bin/env python3
"""Concept video for a DISCOVER winner — MiniMax-H3 t2va, delivered to Telegram.

    ./concept_video.py out/<slug> [--dry-run] [--force]

Runs at the end of every ./discover.py (kill switch: CONCEPT_VIDEO=off). The
human gates the build on it: a 12-second moving picture of the game being
PLAYED says more about a physical-play concept than a slug and a paragraph,
and the whole genre was chosen for demonstrability — if H3 cannot stage the
mechanism from the panel's own words, that is itself a finding about the pitch.

The prompt is a deterministic TEMPLATE over the winner block of discover.md
(NAME / FIRST-LOOK / MECHANISM / PITCH), no LLM: those fields were already
written to be legible to a stranger, and the first hand-built video
(dead-stop, 2026-08-22) proved the template shape works. Style constants
mirror the content pipeline's hard-won lesson: say "FDM printed, visible
layer lines" or everything drifts CGI.

Gateway facts this code is built on are measured, not assumed — see
/root/docs/minimax-h3-gateway.md on this box: cold start can sit `queued`
35+ min; jobs can zombie mid-`processing`; there is NO cancel, so
abandon-and-resubmit is the only remedy; python-urllib's User-Agent is
WAF-blocked, hence curl subprocesses throughout.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

GATEWAY = os.environ.get("MEDIA_GATEWAY", "https://2x4090-9091.eternalai.org")
KEY_FILE = os.environ.get("MEDIA_GATEWAY_KEY_FILE",
                          "/root/panda-secrets/media-gateway.env")
SHARED = os.environ.get("SHARED_REPORTS", "/root/shared-reports")
SHARED_URL = os.environ.get("SHARED_REPORTS_URL", "http://178.128.89.39")

DURATION_S = int(os.environ.get("CONCEPT_VIDEO_SECONDS", "12"))  # 12 verified
QUEUE_GIVE_UP_S = 40 * 60      # cold start observed at 35+ min; past 40 it is dead
STALL_GIVE_UP_S = 10 * 60      # progress frozen this long while processing = zombie
POLL_S = 5
ATTEMPTS = 2                   # abandon-and-resubmit once; there is no cancel


def gateway_key() -> str:
    k = os.environ.get("MEDIA_GATEWAY_KEY", "").strip()
    if k:
        return k
    f = Path(KEY_FILE)
    if f.is_file():
        m = re.search(r"^MEDIA_GATEWAY_API_KEY=(\S+)", f.read_text(), re.M)
        if m:
            return m.group(1)
    raise RuntimeError(f"no MEDIA_GATEWAY_KEY and no key in {KEY_FILE}")


def fields(discover_md: str) -> dict:
    """NAME / PITCH / BOX-FACE / FIRST-LOOK / MECHANISM out of the winner block.

    The pitch is the first non-empty line after `WINNER:`; the labelled lines
    follow it. Everything is single-line by the panel's own output contract.
    """
    m = re.search(r"^WINNER:\s*([a-z0-9-]+)\s*$(.*?)(?=^PROMPT:|\Z)",
                  discover_md, re.M | re.S)
    if not m:
        return {}
    slug, body = m.group(1), m.group(2)
    out = {"slug": slug}
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    labelled = {"Name": "name", "Box face": "box_face",
                "First look": "first_look", "Mechanism": "mechanism"}
    for ln in lines:
        k, _, v = ln.partition(":")
        if k.strip() in labelled:
            out[labelled[k.strip()]] = v.strip()
        elif "pitch" not in out:
            out["pitch"] = ln
    # "banded hull launch into sprung jaws — 7 parts." -> drop the part count
    out["mechanism"] = re.sub(r"\s*[—-]\s*\d+\s*parts\.?\s*$", "",
                              out.get("mechanism", ""))
    return out


def build_prompt(f: dict) -> str:
    """One H3 prompt in the repo's proven 3-part shape (visual/soundscape/music)."""
    name = f.get("name") or f["slug"].replace("-", " ").title()
    first_look = f.get("first_look", "")
    return (
        "A cozy tabletop board game session filmed like a playful product ad, "
        f"showing a fully FDM 3D-printed board game called \"{name}\" - crisp "
        "plastic parts with visible print layer lines, on a wooden dining "
        "table in warm afternoon window light, shallow depth of field. "
        + (f"The first thing on the table: {first_look} " if first_look else "")
        + "Two friends play one full turn. The game's physical mechanism, "
        f"acted out by their hands: {f.get('mechanism', '')}. The camera "
        "starts low behind the active piece and follows its motion, then cuts "
        "to a close top-down shot as the physical consequence lands on the "
        "board, then the second player answers with their own move, and the "
        "shot ends pulled back on the whole board as both players lean in "
        f"and laugh. What the game is about: {f.get('pitch', '')} "
        "Overall soundscape: printed plastic pieces sliding and clacking on "
        "printed tiles, one sharp mechanical snap at the climax of the turn, "
        "two friends reacting and laughing, quiet living-room ambience. "
        "Non-diegetic music: light playful ukulele and hand percussion, "
        "upbeat, product-ad energy.")


def caption(f: dict) -> str:
    """sendVideo caps captions at 1024 bytes; the command must survive a clip."""
    go = f"Build tiep:  ./text2game --slug {f['slug']}"
    head = f"text2game CONCEPT — {f.get('name', f['slug'])}\n"
    body = f"{f.get('box_face', '')}\n{f.get('pitch', '')}\n" \
           f"{SHARED_URL}/{f['slug']}-concept.mp4\n\n"
    room = 1024 - len((head + "\n\n" + go).encode()) - 8
    while len(body.encode()) > room:
        body = body[:len(body) - 16].rstrip() + "…\n"
    return head + body + go


def _curl(args: list, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(["curl", "-s", "-m", "120", *args],
                          capture_output=True, text=True, **kw)


def submit(prompt: str, key: str) -> str:
    payload = json.dumps({
        "model": "minimax/minimax-h3-t2va", "type": "text-to-video",
        "prompt": prompt, "duration": DURATION_S,
        "aspect_ratio": "16:9", "resolution": "480p"})
    r = _curl(["-X", "POST", f"{GATEWAY}/media/generations",
               "-H", f"Authorization: Bearer {key}",
               "-H", "Content-Type: application/json", "-d", payload])
    d = json.loads(r.stdout or "{}")
    if d.get("status") == "failed" or not d.get("request_id"):
        raise RuntimeError(f"submit rejected: {r.stdout[:200]}")
    return d["request_id"]


def poll(req: str, key: str) -> str:
    """file_url on completion. Raises on the give-up policy — the caller
    resubmits, because a stuck job can never be cancelled, only abandoned."""
    t0, last_prog, last_change = time.time(), None, time.time()
    while True:
        r = _curl([f"{GATEWAY}/media/generations/{req}",
                   "-H", f"Authorization: Bearer {key}"])
        try:
            d = json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            d = {}
        st, prog = d.get("status"), d.get("progress")
        if prog != last_prog:
            last_prog, last_change = prog, time.time()
        if st == "completed":
            return d["result_files"][0]["file_url"]
        if st == "failed":
            raise RuntimeError(f"{req} failed")
        if st == "queued" and time.time() - t0 > QUEUE_GIVE_UP_S:
            raise RuntimeError(f"{req} queued > {QUEUE_GIVE_UP_S // 60}min")
        if st == "processing" and time.time() - last_change > STALL_GIVE_UP_S:
            raise RuntimeError(f"{req} stalled at {prog}")
        time.sleep(POLL_S)


def verify_mp4(path: Path) -> None:
    """No ffprobe on this box: byte-scan for the four atoms a good file has."""
    data = path.read_bytes()
    missing = [a for a in (b"vide", b"soun", b"avc1", b"mp4a")
               if a not in data]
    if len(data) < 100_000 or missing:
        raise RuntimeError(f"bad mp4 ({len(data)}B, missing {missing})")


def send_video(path: Path, text: str) -> None:
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_DM", "").strip()
    if not (tok and chat):
        print("  telegram: skipped (no creds)")
        return
    r = _curl([f"https://api.telegram.org/bot{tok}/sendVideo",
               "-F", f"chat_id={chat}", "-F", f"video=@{path}",
               "-F", f"caption={text}"])
    ok = '"ok":true' in (r.stdout or "").replace(" ", "")
    if not ok:
        raise RuntimeError(f"sendVideo failed: {r.stdout[:200]}")


def run(out_dir: Path, force: bool = False, dry_run: bool = False) -> Path:
    dm = out_dir / "discover.md"
    f = fields(dm.read_text(encoding="utf-8")) if dm.is_file() else {}
    if not f:
        raise RuntimeError(f"{dm} has no parseable WINNER block")
    dst = out_dir / "concept_video.mp4"
    if dst.is_file() and not force:
        print(f"  concept video exists, skipping ({dst})")
        return dst
    prompt = build_prompt(f)
    if dry_run:
        print(prompt + "\n\n--- caption ---\n" + caption(f))
        return dst
    key = gateway_key()
    err = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            req = submit(prompt, key)
            print(f"  concept video: {req} (attempt {attempt}, "
                  f"{DURATION_S}s, warm ~3min, cold up to 40)", flush=True)
            url = poll(req, key)
            r = _curl(["-o", str(dst), url])
            if r.returncode != 0:
                raise RuntimeError(f"download failed: {r.stderr[:120]}")
            verify_mp4(dst)
            break
        except RuntimeError as e:
            err = e
            print(f"  concept video attempt {attempt}: {e}", flush=True)
            dst.unlink(missing_ok=True)
    else:
        raise RuntimeError(f"gave up after {ATTEMPTS} attempts: {err}")
    pub = Path(SHARED)
    if pub.is_dir():
        shutil.copy2(dst, pub / f"{f['slug']}-concept.mp4")
    send_video(dst, caption(f))
    print(f"  concept video sent: {SHARED_URL}/{f['slug']}-concept.mp4",
          flush=True)
    return dst


def main() -> int:
    import harness
    harness.load_env()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__.split("\n\n")[0])
        return 2
    run(Path(args[0]).resolve(), force="--force" in sys.argv,
        dry_run="--dry-run" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
