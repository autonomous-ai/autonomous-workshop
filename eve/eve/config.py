"""Configuration and environment loading for Eve.

Values have sane defaults so the core is runnable offline; anything that
needs a credential (Claude CLI, Telegram, Panda backend) is read from
environment / .env and degrades to an explicit "*_configured" flag.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def repo_root() -> Path:
    return REPO_ROOT


@dataclass
class Config:
    # --- paths -----------------------------------------------------------
    root: Path = REPO_ROOT
    games_dir: Path = field(default_factory=lambda: REPO_ROOT / "games")
    loops_dir: Path = field(default_factory=lambda: REPO_ROOT / "loops")
    seed_dir: Path = field(default_factory=lambda: REPO_ROOT / "corpus" / "seed")
    corpus_db: Path = field(default_factory=lambda: REPO_ROOT / "corpus" / "db" / "corpus.json")
    ledger_path: Path = field(default_factory=lambda: REPO_ROOT / "loops" / "ledger.json")
    queue_path: Path = field(default_factory=lambda: REPO_ROOT / "loops" / "queue.json")
    journal_path: Path = field(default_factory=lambda: REPO_ROOT / "loops" / "journal.md")
    taste_path: Path = field(default_factory=lambda: REPO_ROOT / "taste" / "taste.md")
    arch_state: Path = field(default_factory=lambda: REPO_ROOT / "loops" / "arch" / "state.json")
    corpus_state: Path = field(default_factory=lambda: REPO_ROOT / "loops" / "corpus" / "state.json")

    # --- cadence (constraints, not reward) ------------------------------
    ship_every_days: int = 7              # must ship >= 1 game per week
    min_stages_per_day: int = 1           # daily progress floor

    # --- reward (see DESIGN.md ss.3) -------------------------------------
    gamma: float = 0.95
    w_novelty: float = 1.0
    w_rules: float = 2.0
    w_fun: float = 4.0
    w_print: float = 1.5
    w_cogs: float = 1.5
    w_ship: float = 10.0
    p_repair_fail: float = -0.5
    p_rework: float = -0.3
    p_dead: float = -2.0
    cogs_budget_usd: float = 30.0          # reference budget per game

    repair_budget: int = 2                 # repaired rounds per game
    rework_budget: int = 3                 # rules rework rounds per game
    builder_max_minutes: int = 90           # CAD build ceiling (large multi-part sets)
    brief_max_minutes: int = 40            # print-brief engineer ceiling (multi-part spec)

    # --- tooling flags ---------------------------------------------------
    claude_cli: str = "claude"
    telegram_configured: bool = False
    playtest_configured: bool = False

    # --- real LLM-player table (see playtest.run_player_table) --------------
    run_llm_table: bool = False          # enable live claude -p 4-seat table runs
    table_games: int = 4                 # games per table run
    table_players: int = 4               # seats per game
    table_parallel: int = 2              # concurrent seats (bounded by DAYBOOK quota)
    table_seed: int = 11                 # base rng seed for replayability

    # --- Vibe / Panda store publish (see publish.py) -----------------------
    store_base_url: str = "https://panda-social-api.autonomous.ai"
    store_upload_base: str = "http://178.128.89.39:8090"   # admindash for /uploads
    store_upload_token: str = ""    # admindash bearer (uploads -> CDN)
    store_bearer: str = ""          # platform bearer token (API calls)
    panda_owner_id: str = ""        # 24-hex owner id for imported designs
    store_configured: bool = False

    @classmethod
    def load(cls) -> "Config":
        _load_dotenv(REPO_ROOT / ".env")
        c = cls()
        c.ship_every_days = int(os.environ.get("EVE_SHIP_EVERY_DAYS", c.ship_every_days))
        c.min_stages_per_day = int(os.environ.get("EVE_MIN_STAGES_PER_DAY", c.min_stages_per_day))
        c.gamma = float(os.environ.get("EVE_GAMMA", c.gamma))
        c.w_novelty = float(os.environ.get("EVE_W_NOVELTY", c.w_novelty))
        c.w_rules = float(os.environ.get("EVE_W_RULES", c.w_rules))
        c.w_fun = float(os.environ.get("EVE_W_FUN", c.w_fun))
        c.w_print = float(os.environ.get("EVE_W_PRINT", c.w_print))
        c.w_cogs = float(os.environ.get("EVE_W_COGS", c.w_cogs))
        c.w_ship = float(os.environ.get("EVE_W_SHIP", c.w_ship))
        c.p_repair_fail = float(os.environ.get("EVE_P_REPAIR_FAIL", c.p_repair_fail))
        c.p_rework = float(os.environ.get("EVE_P_REWORK", c.p_rework))
        c.p_dead = float(os.environ.get("EVE_P_DEAD", c.p_dead))
        c.cogs_budget_usd = float(os.environ.get("EVE_COGS_BUDGET_USD", c.cogs_budget_usd))
        c.repair_budget = int(os.environ.get("EVE_REPAIR_BUDGET", c.repair_budget))
        c.rework_budget = int(os.environ.get("EVE_REWORK_BUDGET", c.rework_budget))
        c.builder_max_minutes = int(os.environ.get("EVE_BUILDER_MAX_MINUTES", c.builder_max_minutes))
        c.brief_max_minutes = int(os.environ.get("EVE_BRIEF_MAX_MINUTES", c.brief_max_minutes))
        c.telegram_configured = bool(os.environ.get("EVE_TELEGRAM_TOKEN"))
        c.store_base_url = os.environ.get("EVE_STORE_BASE_URL", c.store_base_url)
        c.store_upload_base = os.environ.get("EVE_STORE_UPLOAD_BASE", c.store_upload_base)
        c.store_upload_token = os.environ.get("ADMIN_TOKEN", "").strip()
        c.store_bearer = os.environ.get("EVE_STORE_BEARER", "").strip()
        c.panda_owner_id = os.environ.get("PANDA_OWNER_ID", "").strip()
        c.store_configured = bool(c.store_bearer)
        c.playtest_configured = bool(
            os.environ.get("PLAYTEST_BASE_URL")
            and os.environ.get("PLAYTEST_API_KEY")
            and os.environ.get("PLAYTEST_MODEL")
        )
        c.run_llm_table = bool(int(os.environ.get("EVE_RUN_LLM_TABLE", "0")))
        c.table_games = int(os.environ.get("EVE_TABLE_GAMES", c.table_games))
        c.table_players = int(os.environ.get("EVE_TABLE_PLAYERS", c.table_players))
        c.table_parallel = int(os.environ.get("EVE_TABLE_PARALLEL", c.table_parallel))
        c.table_seed = int(os.environ.get("EVE_TABLE_SEED", c.table_seed))
        return c


class _ConfigExtras:
    """Static-helper accessors layered onto Config (kept out of the dataclass
    so the state stays a clean value object but callers get named weights)."""
    @staticmethod
    def weights(cfg) -> dict:
        return {
            "novelty_pass": cfg.w_novelty,
            "rules_pass": cfg.w_rules,
            "fun_pass": cfg.w_fun,
            "print_pass": cfg.w_print,
            "cogs_ok": cfg.w_cogs,
            "ship": cfg.w_ship,
            "repair_fail": cfg.p_repair_fail,
            "rework": cfg.p_rework,
            "dead_game": cfg.p_dead,
        }


def weights(cfg) -> dict:
    """Named reward weights from a Config, so callers never duplicate them."""
    return _ConfigExtras.weights(cfg)
