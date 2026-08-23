#!/usr/bin/env python3
"""doctor.py - can THIS machine run text2game, and which phases?

    ./doctor.py                    # every phase, offline checks only
    ./doctor.py --phase discover,1 # just the rules half (no CAD toolchain needed)
    ./doctor.py --probe            # also touch the network: claude, codex, the
                                   # video gateway, Telegram, admindash

One row per requirement: OK / MISSING / opt, which phases need it, and the fix.
Exit 1 when anything REQUIRED for the requested phases is missing. Run it right
after `git clone` and again after dropping in the owner's .env - the red rows
are the setup list, in order. SETUP.md is the prose version of the same list.

Everything here is a fact about the machine, never a guess about the pipeline:
the checks read the same env, the same helper functions and the same file paths
the phases do, so a green doctor and a failing phase is a bug in THIS file.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402

harness.load_env()

ALL = ("discover", "1", "2", "3", "publish")
HOME = Path.home()


def env(k: str) -> str:
    return os.environ.get(k, "").strip()


def which(name: str) -> str:
    return shutil.which(name) or (f"{HOME}/.local/bin/{name}"
                                   if Path(f"{HOME}/.local/bin/{name}").exists() else "")


def run(cmd: list, timeout: int = 60) -> tuple:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def py_imports(py: str, mods: tuple) -> tuple:
    if not Path(py).exists():
        return False, f"{py} does not exist"
    code = ("import importlib.util,sys\nbad=[m for m in sys.argv[1:] if not "
            "importlib.util.find_spec(m)]\nprint(','.join(bad))")
    rc, out = run([py, "-c", code, *mods], timeout=120)
    bad = out.strip().splitlines()[-1] if out.strip() else ""
    return (rc == 0 and not bad), (f"missing {bad}" if bad else "all importable")


def providers() -> dict:
    """Which provider each phase's representative job resolves to, from .env."""
    return {"discover": harness.provider_for("discover"),
            "1": harness.provider_for("gdd"),
            "2": harness.provider_for("build"),
            "3": harness.provider_for("rulebook")}


# ---------------------------------------------------------------------------
# Each check: (name, phases, required, fn, fix). fn -> (ok: bool, detail: str).
# `required` may be a callable taking the probe flag, for conditional needs.
# ---------------------------------------------------------------------------

def checks(probe: bool) -> list:
    t2c = harness.text2cad_dir()
    t2py = harness.text2cad_py()
    prov = providers()
    uses_codex = [p for p, v in prov.items() if v == "codex"]
    uses_claude = [p for p, v in prov.items() if v == "claude"]
    out = []

    def add(name, phases, required, fn, fix=""):
        out.append((name, tuple(phases), required, fn, fix))

    # --- the config file itself ---------------------------------------------
    add(".env present", ALL, True,
        lambda: ((HERE / ".env").is_file(), str(HERE / ".env")),
        "drop the owner's .env here (template: .env.example)")
    add("out/ and logs/ writable", ALL, True,
        lambda: (all(os.access(HERE, os.W_OK) for _ in (1,)),
                 "mkdir -p out logs is done by the scripts"), "chmod/chown the clone")

    # --- LLM providers --------------------------------------------------------
    def claude_ok():
        p = which("claude")
        if not p:
            return False, "not on PATH"
        rc, v = run([p, "--version"])
        return rc == 0, v.strip().splitlines()[0] if v.strip() else p
    add("claude CLI (Claude Code)", uses_claude or ("discover",), True, claude_ok,
        "npm i -g @anthropic-ai/claude-code  (then `claude` once to log in)")
    add("claude login", uses_claude or ("discover",), True,
        lambda: (((HOME / ".claude" / ".credentials.json").is_file()
                  or (HOME / ".claude.json").is_file()),
                 "credentials file present (use --probe to really call it)"),
        "run `claude` interactively once and sign in")
    if probe and which("claude"):
        def claude_probe():
            rc, out_ = run([which("claude"), "-p", "Reply with exactly: OK",
                            "--max-turns", "1", "--output-format", "json"], timeout=180)
            try:
                d = json.loads(out_.strip().splitlines()[-1])
                return (not d.get("is_error") and "OK" in str(d.get("result", ""))), \
                    f"subtype={d.get('subtype')} cost=${d.get('total_cost_usd', 0):.3f}"
            except (ValueError, IndexError):
                return False, out_.strip()[-160:]
        add("claude -p round trip (probe)", uses_claude or ("discover",), True,
            claude_probe, "claude login / network")
    add(f"codex CLI (CODEX_JOBS routes phases {','.join(uses_codex) or '-'})",
        uses_codex or ("2",), bool(uses_codex),
        lambda: ((harness.codex_ready() == ""),
                 harness.codex_ready() or (run([which("codex") or "codex", "--version"])[1].strip() or "ok")),
        "npm i -g @openai/codex && codex login   - or set CODEX_JOBS=none to run everything on claude")
    add("codex login", uses_codex or ("2",), bool(uses_codex),
        lambda: ((HOME / ".codex" / "auth.json").is_file(), str(HOME / ".codex" / "auth.json")),
        "codex login (ChatGPT Pro)")

    def mcp_ok():
        f = HOME / ".claude.json"
        try:
            servers = json.loads(f.read_text()).get("mcpServers", {})
        except (OSError, ValueError):
            servers = {}
        return "second-brain" in servers, f"mcpServers: {sorted(servers) or 'none'}"
    add("second-brain MCP (trend digests for the proposers)", ("discover",), False, mcp_ok,
        "claude mcp add second-brain ...  - without it the panel reads local digests only (narrower, not broken)")

    # --- Telegram (status + the decisions only a human can make) --------------
    add("TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_DM", ALL, False,
        lambda: (bool(env("TELEGRAM_BOT_TOKEN") and env("TELEGRAM_CHAT_DM")),
                 "set" if env("TELEGRAM_BOT_TOKEN") else "unset - decisions print to stdout only"),
        "from the owner's .env")
    if probe and env("TELEGRAM_BOT_TOKEN"):
        add("telegram getMe (probe)", ALL, False,
            lambda: ('"ok":true' in run(["curl", "-s", "-m", "20",
                     f"https://api.telegram.org/bot{env('TELEGRAM_BOT_TOKEN')}/getMe"])[1].replace(" ", ""),
                     "bot answers"), "check the token")

    # --- system python for this repo --------------------------------------------
    add("python3 packages for this repo (requirements.txt)", ("3",), True,
        lambda: py_imports(sys.executable, ("PIL",)),
        f"{sys.executable} -m pip install -r requirements.txt")

    # --- the text2cad sibling: CAD toolchain ------------------------------------
    add(f"TEXT2CAD_DIR = {t2c}", ("2", "3", "publish"), True,
        lambda: (t2c.is_dir(), "checkout present" if t2c.is_dir() else "missing"),
        "git clone https://github.com/nohope88/text2cad.git  (sibling of this repo) and set TEXT2CAD_DIR")
    for rel, phases in (("gate.py", ("2", "3")), ("concept_image.py", ("2",)),
                        ("skills/cadcode/SKILL.md", ("2",)),
                        ("skills/cadcode/scripts/measure/cli.py", ("2", "3")),
                        ("skills/cadcode/scripts/cad/cli.py", ("2",)),
                        ("gen_howto_video.py", ("3",)),
                        ("gcs_upload_project.py", ("publish",)),
                        ("bin/importdesign", ("publish",))):
        add(f"text2cad/{rel}", phases, True,
            (lambda rel=rel: ((t2c / rel).exists(), str(t2c / rel))),
            ("go build -o <text2cad>/bin/importdesign ./cmd/importdesign  inside panda-social-backend"
             if rel == "bin/importdesign" else "git pull the text2cad checkout"))
    for rel, phases in (("md2html.py", ("publish",)), ("fe_colors.py", ("publish",))):
        add(f"text2cad/{rel} (optional)", phases, False,
            (lambda rel=rel: ((t2c / rel).exists(), str(t2c / rel))), "git pull text2cad")
    add(f"TEXT2CAD_PY CAD venv = {t2py}", ("2", "3"), True,
        lambda: py_imports(t2py, ("cadquery", "trimesh", "numpy", "matplotlib")),
        "cd <text2cad> && uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python cadquery trimesh numpy manifold3d matplotlib pillow")
    add("~/.claude/skills/cadcode -> text2cad/skills/cadcode", ("2",),
        prov.get("2") == "claude",
        lambda: ((HOME / ".claude" / "skills" / "cadcode" / "SKILL.md").exists(),
                 str((HOME / ".claude" / "skills" / "cadcode").resolve())
                 if (HOME / ".claude" / "skills" / "cadcode").exists() else "missing"),
        f"mkdir -p ~/.claude/skills && ln -s {t2c}/skills/cadcode ~/.claude/skills/cadcode")
    add("uv (measure/cad runners, publish colour keying)", ("2", "publish"), True,
        lambda: (bool(which("uv")), which("uv") or "not on PATH"),
        "curl -LsSf https://astral.sh/uv/install.sh | sh")

    # --- phase 3: slicer, profile, video extras ---------------------------------
    add("prusa-slicer", ("3",), True,
        lambda: (bool(env("SLICER_BIN") or which("prusa-slicer")),
                 env("SLICER_BIN") or which("prusa-slicer") or "not on PATH"),
        "apt install prusa-slicer  (2.7.x) or set SLICER_BIN")
    prof = Path(env("SLICER_PROFILE") or HERE / "profiles" / "petg.ini")
    add(f"SLICER_PROFILE = {prof}", ("3",), True,
        lambda: (prof.is_file(), "present" if prof.is_file() else "missing"),
        "profiles/petg.ini ships in the repo; set SLICER_PROFILE to use another")
    add("node (FE-viewer renders; howto video extras)", ("3", "publish"), False,
        lambda: (bool(which("node")), which("node") or "not on PATH"), "apt install nodejs")
    add("ffmpeg (howto video mux)", ("3",), False,
        lambda: (bool(which("ffmpeg")), which("ffmpeg") or "not on PATH"), "apt install ffmpeg")

    # --- concept video gateway ---------------------------------------------------
    def gw_key():
        try:
            import concept_video
            return bool(concept_video.gateway_key()), "key resolved"
        except Exception as e:  # noqa: BLE001
            return False, str(e)[:100]
    add("MEDIA_GATEWAY_KEY (or MEDIA_GATEWAY_KEY_FILE) for concept videos", ("discover",),
        (env("CONCEPT_VIDEO") or "on").lower() not in ("off", "0", "no"), gw_key,
        "from the owner's .env - or CONCEPT_VIDEO=off; the panel itself never depends on it")
    if probe:
        add("video gateway /health (probe)", ("discover",), False,
            lambda: ('"ok"' in run(["curl", "-s", "-m", "20",
                     f"{env('MEDIA_GATEWAY') or 'https://2x4090-9091.eternalai.org'}/health"])[1],
                     "gateway answers"), "gateway down or URL wrong")

    # --- optional knowledge sources ---------------------------------------------
    gv = Path(env("GAMEVAULT") or "/root/gamevault")
    add(f"GAMEVAULT design vault = {gv} (critic leads)", ("1",), False,
        lambda: ((gv / "vault_tools.py").is_file(), "present" if (gv / "vault_tools.py").is_file() else "absent - critic runs without leads"),
        "git clone https://github.com/nohope88/gamevault.git and set GAMEVAULT, or CRITIC_VAULT=off")
    sr = Path(env("SHARED_REPORTS") or "/root/shared-reports")
    add(f"SHARED_REPORTS web dir = {sr}", ("discover", "publish"), False,
        lambda: (sr.is_dir(), "present" if sr.is_dir() else "absent - videos/reports stay local, Telegram still gets them"),
        "any dir served on port 80; set SHARED_REPORTS + SHARED_REPORTS_URL")

    # --- publish ----------------------------------------------------------------
    sec = Path(env("PANDA_SECRETS_ENV") or "/root/panda-secrets/.env")
    def mongo_ok():
        if env("MONGODB_URI"):
            return True, "MONGODB_URI in .env"
        if sec.is_file() and "MONGODB_URI=" in sec.read_text():
            return True, f"via {sec}"
        return False, f"not in .env and no {sec}"
    add("MONGODB_URI (+MONGODB_DBNAME)", ("publish",), True, mongo_ok, "from the owner's .env")
    add("GCS_BUCKET + GCS_CDN_URL", ("publish",), True,
        lambda: (bool((env("GCS_BUCKET") and env("GCS_CDN_URL"))
                      or (sec.is_file() and "GCS_BUCKET=" in sec.read_text())),
                 "set" if env("GCS_BUCKET") else f"via {sec}" if sec.is_file() else "unset"),
        "from the owner's .env")
    gsa = Path("/root/panda-secrets/gcs-sa.json")
    add("GCS service account at /root/panda-secrets/gcs-sa.json", ("publish",), True,
        lambda: (gsa.is_file(), "present" if gsa.is_file() else "missing - text2cad/gcs_upload_project.py hardcodes this exact path"),
        "place the owner's gcs-sa.json there (or symlink)")
    gpy = env("GCS_PY") or "/root/gcsvenv/bin/python"
    add(f"GCS_PY venv = {gpy} (google-cloud-storage)", ("publish",), True,
        lambda: py_imports(gpy, ("google.cloud.storage",)),
        "python3 -m venv /root/gcsvenv && /root/gcsvenv/bin/pip install google-cloud-storage  (or set GCS_PY)")
    add("ADMIN_TOKEN + PANDA_OWNER_ID", ("publish",), True,
        lambda: (bool(env("ADMIN_TOKEN") and env("PANDA_OWNER_ID")),
                 "set" if env("ADMIN_TOKEN") else "unset - publish.py refuses to run"),
        "from the owner's .env")
    bd = Path(env("BACKEND_DIR") or "/root/panda-social-backend")
    add(f"BACKEND_DIR panda-social-backend checkout = {bd}", ("publish",), True,
        lambda: (bd.is_dir(), "present" if bd.is_dir() else "missing (importdesign runs with this cwd)"),
        "git clone the backend (org autonomous-ecm, private) and set BACKEND_DIR")
    if probe:
        ad = env("ADMINDASH_URL") or "http://localhost:8090"
        add(f"admindash reachable at {ad} (probe)", ("publish",), False,
            lambda: (run(["curl", "-s", "-m", "10", "-o", "/dev/null", "-w", "%{http_code}", ad])[1].strip().startswith(("2", "3", "4")),
                     "answers"), "start admindash or set ADMINDASH_URL")
    return out


def main() -> int:
    args = sys.argv[1:]
    probe = "--probe" in args
    want = set(ALL)
    if "--phase" in args:
        raw = args[args.index("--phase") + 1]
        want = {p.strip() for p in raw.split(",") if p.strip()}
        unknown = want - set(ALL)
        if unknown:
            print(f"unknown phase(s) {sorted(unknown)} - choose from {ALL}")
            return 2
    prov = providers()
    print(f"text2game doctor - phases {','.join(p for p in ALL if p in want)}"
          f"{' (+network probe)' if probe else ''}")
    print("providers: " + "  ".join(f"{k}={v}" for k, v in prov.items()) + "\n")
    missing, rows = [], []
    for name, phases, required, fn, fix in checks(probe):
        if not (set(phases) & want):
            continue
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001 - a check must never crash the doctor
            ok, detail = False, f"check crashed: {type(e).__name__}: {e}"
        req = required(probe) if callable(required) else bool(required)
        tag = "OK " if ok else ("MISSING" if req else "opt")
        rows.append((tag, "/".join(phases), name, detail, fix if not ok else ""))
        if not ok and req:
            missing.append(name)
    w = max(len(r[2]) for r in rows)
    for tag, ph, name, detail, fix in rows:
        print(f"  {tag:<8} {ph:<18} {name:<{w}}  {detail}")
        if fix:
            print(f"  {'':<8} {'':<18} {'':<{w}}  -> {fix}")
    print()
    if missing:
        print(f"{len(missing)} REQUIRED item(s) missing for the requested phases:")
        for m in missing:
            print(f"  - {m}")
        return 1
    print("ready: every requirement for the requested phases is in place")
    return 0


if __name__ == "__main__":
    sys.exit(main())
