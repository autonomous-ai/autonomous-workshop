"""One host-owned token allowance for the complete product, across resumes."""

import copy

from workshop.errors import ContractError
from workshop.runtime.codex_usage import COUNTERS
from workshop.workflow.budgets import LifetimeBudget, LifetimeTurnBudget

TOKEN_BUDGET_CAPABILITY_PATH = ".agents/skills/autonomous-workshop/references/token-budget-v1.md"
DEFAULT_PRODUCT_TOKENS = 30_000_000
MAX_PRODUCT_TOKENS = 200_000_000


def validate_limit(value):
    if type(value) is not int or not 1_000 <= value <= MAX_PRODUCT_TOKENS:
        raise ContractError("product token limit must be an integer from 1,000 to 200,000,000")
    return value


class ProductTokenBudget(LifetimeBudget):
    def __init__(self, limit=DEFAULT_PRODUCT_TOKENS):
        super().__init__()
        self.limit = validate_limit(limit)
        self.observation = None
        self.previous_budget = None

    def to_dict(self):
        return {
            "schema_version": 3, "unit": "tokens",
            "limit_tokens": self.limit,
            "used_tokens": 0 if self.observation is None else self.observation["total_tokens"],
            "usage_status": "unavailable" if self.observation is None else "observed",
            "observation": self.observation, "previous_budget": self.previous_budget,
        }

    def observe(self, value):
        if (not isinstance(value, dict) or value.get("source") != "codex-native-rollout-v1"
                or type(value.get("schema_version")) is not int or value["schema_version"] != 1
                or value.get("status") != "observed"):
            raise ContractError("product token observation source is invalid")
        threads = value.get("threads")
        if not isinstance(threads, list) or not threads:
            raise ContractError("product token thread coverage is invalid")
        totals = {key: 0 for key in COUNTERS}
        seen = set()
        for thread in threads:
            if not isinstance(thread, dict) or not isinstance(thread.get("thread_id"), str):
                raise ContractError("product token thread identity is invalid")
            if thread["thread_id"] in seen:
                raise ContractError("duplicate product token thread")
            seen.add(thread["thread_id"])
            if thread.get("status") not in ("pending", "observed"):
                raise ContractError("product token thread reporting status is invalid")
            counters = thread.get("tokens")
            if not isinstance(counters, dict) or set(counters) != set(COUNTERS):
                raise ContractError("product token counters are missing")
            if any(type(v) is not int or not 0 <= v <= 10**12 for v in counters.values()):
                raise ContractError("product token counters are invalid")
            if counters["cached_input_tokens"] + counters["cache_write_input_tokens"] > counters["input_tokens"] or counters["reasoning_output_tokens"] > counters["output_tokens"]:
                raise ContractError("product token counters are inconsistent")
            if thread["status"] == "pending" and any(counters.values()):
                raise ContractError("pending token usage cannot contain observed counters")
            for key in COUNTERS:
                totals[key] += counters[key]
        total = totals["input_tokens"] + totals["output_tokens"]
        if value.get("tokens") != totals or type(value.get("total_tokens")) is not int or value["total_tokens"] != total or value.get("root_thread_id") not in seen:
            raise ContractError("product token total is inconsistent")
        if self.observation is not None:
            if value["root_thread_id"] != self.observation["root_thread_id"]:
                raise ContractError("product token root session changed")
            current = {t["thread_id"]: t["tokens"] for t in threads}
            for previous in self.observation["threads"]:
                if previous["thread_id"] not in current or any(current[previous["thread_id"]][k] < previous["tokens"][k] for k in COUNTERS):
                    raise ContractError("product token observation lost prior usage")
        self.observation = copy.deepcopy(value)

    def restore(self, value):
        if not isinstance(value, dict) or set(value) != {"schema_version", "unit", "limit_tokens", "used_tokens", "usage_status", "observation", "previous_budget"} or type(value["schema_version"]) is not int or value["schema_version"] != 3 or value["unit"] != "tokens":
            raise ContractError("invalid product token budget")
        self.limit = validate_limit(value["limit_tokens"])
        self.observation = None
        if value["observation"] is not None:
            self.observe(value["observation"])
        self.previous_budget = value["previous_budget"]
        if self.previous_budget is not None:
            if not isinstance(self.previous_budget, dict):
                raise ContractError("invalid prior product budget")
            prior = LifetimeTurnBudget() if self.previous_budget.get("unit") == "native_turns" else LifetimeBudget()
            prior.restore(self.previous_budget)
        if type(value["used_tokens"]) is not int or self.to_dict() != value:
            raise ContractError("inconsistent product token budget")

    def exhausted(self, step):
        return "run" if self.to_dict()["used_tokens"] >= self.limit else None

    def reserve(self, stage, seconds):
        if self.exhausted(stage):
            raise ContractError("product token budget exhausted")

    def settle(self, stage, reserved, elapsed):
        pass  # Observed native usage, not wall time, advances this budget.

    def turn_timeout_seconds(self, step):
        return None  # Product execution is bounded by observed tokens, not time.

    def exhausted_message(self, step, which, product_id):
        return "This product reached its persistent token limit; observed usage remains charged across resume."
