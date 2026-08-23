#!/usr/bin/env python3
"""Daily autonomous cycle: discover -> build -> output, no human gate.

Cron (panda, UTC):  15 0 * * *  cd /root/text2cad && ./autoloop.py >> logs/autoloop.log 2>&1

- Idempotent: one cycle per day (marker file), safe to re-run.
- Auto-commits ONLY the lessons tier (lessons.md, discover_lessons.md) — code
  changes belong to improve.py's PR flow.
- Heartbeat file for watchdog.sh (dead-man pattern: silence must be alarmable).
"""
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE / "logs"
MARKERS = HERE / "out" / ".cycles"
LESSON_FILES = ["lessons.md", "discover_lessons.md"]


def sh(cmd, **kw):
    return subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, **kw)


def telegram(text):
    env = os.environ
    tok, chat = env.get("TELEGRAM_BOT_TOKEN", ""), env.get("TELEGRAM_CHAT_DM", "")
    if tok and chat:
        sh(["curl", "-s", f"https://api.telegram.org/bot{tok}/sendMessage",
            "-d", f"chat_id={chat}", "--data-urlencode", f"text={text}"], timeout=30)


def load_env():
    for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


MCP_URL = "http://100.82.132.78:8848/mcp"


def mcp_call(method: str, params: dict, token: str, timeout: int = 20):
    """One JSON-RPC call to the second-brain MCP. Returns the result dict or None."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    r = sh(["curl", "-s", "--max-time", str(timeout), "-X", "POST", MCP_URL,
            "-H", f"Authorization: {token}", "-H", "Content-Type: application/json",
            "-H", "Accept: application/json, text/event-stream", "-d", body],
           timeout=timeout + 10)
    # the endpoint answers SSE: the payload is the last `data:` line
    for line in reversed((r.stdout or "").splitlines()):
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip()).get("result")
            except json.JSONDecodeError:
                return None
    return None


def trend_source_health() -> tuple:
    """(usable, explanation) — does DISCOVER actually have fresh trends to read?

    The old check was an UNAUTHENTICATED GET that only treated a dead socket as
    failure. The endpoint answers `403 {"error":"forbidden"}` without a token,
    which sailed through as "reachable" — so an expired token, or a scraper that
    quietly stopped, would both have been discovered only after the propose
    lanes had already been paid for. Verify what DISCOVER actually needs: a
    digest from today or yesterday, fetched with the real credentials.
    """
    try:
        cfg = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
        token = cfg["mcpServers"]["second-brain"]["headers"]["Authorization"]
    except Exception as e:  # noqa: BLE001
        return False, f"no second-brain credentials in ~/.claude.json ({e})"

    if not mcp_call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                   "clientInfo": {"name": "autoloop", "version": "1"}}, token):
        return False, "MCP did not complete a handshake (personal VM down, or token rejected)"

    # autoloop runs at 00:15 UTC and the x-scrape lands ~00:06, but hn-morning
    # not until ~06:03 — so yesterday's digest is a legitimate pass, and only a
    # gap on BOTH days means the scraper is dead.
    today = datetime.date.today()
    for day in (today, today - datetime.timedelta(days=1)):
        for kind in ("x-scrape", "hn-morning"):
            path = f"raw/{day.isoformat()}-{kind}.md"
            res = mcp_call("tools/call",
                           {"name": "memory_get", "arguments": {"path": path}}, token)
            text = json.dumps(res) if res else ""
            if res and "not found" not in text.lower() and len(text) > 400:
                return True, f"{path} readable"
    return False, ("MCP is up but no trend digest exists for today or yesterday — "
                   "the scraper on the personal VM has stopped")


def main() -> int:
    load_env()
    LOGS.mkdir(exist_ok=True)
    MARKERS.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    (HERE / ".heartbeat").write_text(today + "\n", encoding="utf-8")
    marker = MARKERS / today
    if marker.exists():
        print(f"[{today}] cycle already ran — skip")
        return 0

    # trend source lives on the personal VM (tailnet) — alarm early if dark, a
    # dead MCP would otherwise surface as a confusing discover failure.
    ok, why = trend_source_health()
    if not ok:
        msg = f"text2cad autoloop: trend source not usable — {why}. Cycle skipped, will retry tomorrow."
        print(msg)
        telegram(msg)
        return 1
    print(f"[{today}] trend source OK: {why}")

    print(f"[{today}] cycle start")
    env = dict(os.environ)
    env["PATH"] = f"{Path.home()}/.local/bin:" + env.get("PATH", "")
    # 6h (was 3h): 08-14 and 08-15 both finished the build right at the 3h
    # kill, so publish never ran and the whole spend was lost. On timeout,
    # alert instead of dying with a silent traceback.
    # 8h, not 6h: raising the turn caps on 2026-08-17 let phases run to
    # completion instead of dying early, and wall-clock roughly doubled with
    # them (draft 26m->53m, build 74m->86m, repairs ~50m each). The scram cycle
    # ran 5h12m and was still going. A ceiling sized for truncated phases now
    # kills healthy ones, and a kill loses the entire spend.
    cycle_timeout = int(os.environ.get("CYCLE_TIMEOUT_S", str(8 * 3600)))
    log = LOGS / f"cycle-{today}.log"
    # Stream to the log instead of capturing: capture_output buffered EVERYTHING
    # until the process exited, so for up to 8 hours there was no live log at
    # all and a running cycle could only be inspected through out/*/run.json.
    try:
        with log.open("w", encoding="utf-8") as fh:
            r = subprocess.run([str(HERE / "text2cad"), "--discover", "--auto"],
                               cwd=HERE, env=env, stdout=fh,
                               stderr=subprocess.STDOUT, timeout=cycle_timeout)
    except subprocess.TimeoutExpired:
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"\n--- KILLED: exceeded {cycle_timeout}s ---\n")
        marker.write_text("", encoding="utf-8")
        msg = (f"text2cad autoloop STUCK [{today}]: cycle exceeded "
               f"{cycle_timeout // 3600}h and was killed — no publish ran. "
               f"Check {log} on panda.")
        print(msg)
        telegram(msg)
        return 1
    marker.write_text("", encoding="utf-8")

    # summarize from the tail of the run (the log already holds every line)
    stdout = log.read_text(encoding="utf-8", errors="replace")
    tail = "\n".join(stdout.strip().splitlines()[-6:])
    slug = cost = gate = "?"
    ship = False
    for ln in stdout.splitlines():
        if ln.startswith("== DONE "):
            slug = ln.split()[2].rstrip(":")
            gate = "PASS" if "gate=PASS" in ln else "FAIL"
            # `ship=` is the pipeline's own publish decision: gate PASS *and*
            # every lens returned *and* none failed. Publishing on gate alone
            # shipped one-way-newsreel with an empty panel — the mesh was
            # provably printable and nothing had judged it against the concept.
            ship = "ship=YES" in ln
        if "total LLM cost" in ln:
            cost = ln.split("$")[-1].split()[0]
    status = "OK" if r.returncode == 0 and ship else "NEEDS ATTENTION"
    telegram(f"text2cad daily cycle [{status}]\n{tail[:2500]}")

    # green cycle -> import into Panda Social as DRAFT (human flips public)
    if ship and slug not in ("?", ""):
        pub = subprocess.run([sys.executable, str(HERE / "publish.py"), slug],
                             cwd=HERE, capture_output=True, text=True, timeout=600)
        print("publish:", (pub.stdout or pub.stderr).strip()[-200:])
    elif gate == "PASS" and slug not in ("?", ""):
        # Held back deliberately, and said out loud: a silent skip here looks
        # exactly like a publish that failed, and the run is worth reviewing by
        # hand rather than losing.
        msg = (f"text2cad {slug}: gate PASSED but NOT published — the panel did "
               f"not clear it. Review out/{slug}/postmortem.md, then publish by "
               f"hand with ./publish.py {slug} if you disagree.")
        print(msg)
        telegram(msg)

    # lessons tier auto-commit (code tier is improve.py's PR flow)
    changed = [f for f in LESSON_FILES
               if sh(["git", "diff", "--quiet", "--", f]).returncode != 0]
    if changed:
        sh(["git", "add", *changed])
        sh(["git", "commit", "-m", f"loop: lessons update {today} ({slug}, ${cost})"])
        p = sh(["git", "push"])
        print("lessons committed+pushed" if p.returncode == 0 else f"push failed: {p.stderr[-200:]}")

    print(f"[{today}] cycle done: {slug} gate={gate} ship={'YES' if ship else 'NO'} cost=${cost}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
