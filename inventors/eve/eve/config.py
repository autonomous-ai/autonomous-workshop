"""Configuration and environment loading for Eve.

Values have sane defaults so Eve's workshop is runnable offline; anything that
needs a credential (Claude CLI, Telegram, Shop Door) is read from
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


def env_with_fallbacks(primary: str, *fallbacks: str, default: str = "") -> str:
    """Read one canonical environment value with conflict-safe old names.

    Every explicitly set spelling participates, including an empty value. This
    prevents a scheduled Eve process from silently choosing between two Shop
    identities, endpoints, or credentials during migration.
    """

    observed = [
        (name, os.environ[name].strip())
        for name in (primary,) + fallbacks
        if name in os.environ
    ]
    if observed:
        selected = observed[0][1]
        conflicts = [name for name, value in observed[1:] if value != selected]
        if conflicts:
            raise ValueError(
                "%s conflicts with %s; remove old names or make them identical"
                % (primary, ", ".join(conflicts))
            )
        return selected
    return default


def env_with_legacy(primary: str, legacy: str, default: str = "") -> str:
    """Compatibility wrapper for callers migrating one environment name."""

    return env_with_fallbacks(primary, legacy, default=default)


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
    # Root TASTE.md is the one creative authority loaded by Workshop and
    # bound into every model prompt. No shadow Taste file may override it.
    taste_path: Path = field(default_factory=lambda: REPO_ROOT / "TASTE.md")
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

    # --- Send / Shop Door (see send.py) ------------------------------------
    # The default URL is the current external shop. Eve sees only the narrow,
    # provider-neutral Shop Door exposed by Workshop.
    shop_api: str = "https://panda-social-api.autonomous.ai"
    shop_token: str = ""
    shop_owner_id: str = ""
    shop_configured: bool = False

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
        c.shop_api = env_with_fallbacks(
            "EVE_SHOP_API",
            "EVE_PORTAL_API",
            "EVE_STORE_BASE_URL",
            default=c.shop_api,
        )
        c.shop_token = env_with_fallbacks(
            "EVE_SHOP_TOKEN",
            "EVE_PORTAL_TOKEN",
            "EVE_STORE_BEARER",
        )
        c.shop_owner_id = env_with_fallbacks(
            "EVE_SHOP_OWNER_ID",
            "EVE_PORTAL_OWNER_ID",
            "EVE_STORE_OWNER_ID",
            "PANDA_OWNER_ID",
        )
        c.shop_configured = bool(c.shop_token and c.shop_owner_id)
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

    # Compatibility attributes are deliberately properties, not stored
    # dataclass fields. New code and serialized configuration use ``shop_*``.
    @property
    def portal_api(self) -> str:
        return self.shop_api

    @portal_api.setter
    def portal_api(self, value: str) -> None:
        self.shop_api = value

    @property
    def portal_token(self) -> str:
        return self.shop_token

    @portal_token.setter
    def portal_token(self, value: str) -> None:
        self.shop_token = value

    @property
    def portal_owner_id(self) -> str:
        return self.shop_owner_id

    @portal_owner_id.setter
    def portal_owner_id(self, value: str) -> None:
        self.shop_owner_id = value

    @property
    def portal_configured(self) -> bool:
        return self.shop_configured

    @portal_configured.setter
    def portal_configured(self, value: bool) -> None:
        self.shop_configured = bool(value)

    @property
    def store_base_url(self) -> str:
        return self.shop_api

    @store_base_url.setter
    def store_base_url(self, value: str) -> None:
        self.shop_api = value

    @property
    def store_bearer(self) -> str:
        return self.shop_token

    @store_bearer.setter
    def store_bearer(self, value: str) -> None:
        self.shop_token = value

    @property
    def panda_owner_id(self) -> str:
        return self.shop_owner_id

    @panda_owner_id.setter
    def panda_owner_id(self, value: str) -> None:
        self.shop_owner_id = value

    @property
    def store_configured(self) -> bool:
        return self.shop_configured

    @store_configured.setter
    def store_configured(self, value: bool) -> None:
        self.shop_configured = bool(value)


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
