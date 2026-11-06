"""Listing Update: append one version to a public Factory design (ADR 0097).

A Listing Update keeps a published toy's listing, slug, URL and SKU and
replaces what Factory weighs and bills. It is one host effect in four steps:

1. an authenticated preflight read of the design, its current measurement
   and, for a reprice, the live version's own product facts;
2. ``POST /designs/{slug}/import`` with the new handoff and no extras;
3. a bounded wait until Factory's slice of that new version is ``done``;
4. ``PUT /designs/{slug}/extra-materials`` with the new list, then readback.

The extras wait for the slice, so Factory never shows a price computed from
the old mass and the new extras. The version POST has no server-side
idempotency, so the ledger intent carries the base ``current_history_id``
(a compare-and-swap) and a rerun reconciles by readback, never by resending.

Nothing here decides whether an update should happen: the owner previews it,
sees the current and predicted price, and confirms that one run with its
confirmation code.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence

from workshop._validation import require_sha256
from workshop.errors import (
    AmbiguousEffectError,
    ContractError,
    EffectError,
    ReceiptError,
    StateConflict,
)
from workshop.integrations.factory import (
    DEFAULT_FACTORY_API,
    FACTORY_RELEASE_PAGE_PATH,
    FactoryAgentSession,
    FactoryClient,
    _api_origin,
    _factory_product_page_url,
    _factory_receipt,
    _json_body,
)
from workshop.runtime.contracts import Receipt
from workshop.runtime.effects import EffectIntent, EffectLedger


LISTING_UPDATE_KIND = "factory-import-version"
LISTING_UPDATE_REASONS = ("fix", "reprice")
# Factory's shop process infill. A version whose project.json carries no
# print override is measured and printed at this infill
# (panda-social-backend models/design_print_overrides.go).
FACTORY_DEFAULT_INFILL_PERCENT = 15
SLICE_WAIT_SECONDS = 1800
SLICE_POLL_SECONDS = 20

# Factory's price, per unit (panda-social-backend aea8c67,
# models/slice_job.go:135-217 and services/listing_pricing.go:200-225).
_RATE_TENTH_CENTS_PER_GRAM = 40 + 12  # print + freight/duty
_OPS_FEE_CENTS = 1500
_PACKAGING_FEE_CENTS = 0
_MARGIN_PERCENT = 0
_MIN_LISTING_CENTS = 100
_MAX_LISTING_CENTS = 1_000_000


def factory_sale_price_cents(weight_g: Optional[float], extras_cents: int) -> Optional[int]:
    """The price Factory lists a platform-priced design at, or None if unweighed."""

    if weight_g is None or weight_g <= 0:
        return None
    material = int(math.ceil(weight_g * _RATE_TENTH_CENTS_PER_GRAM / 10))
    cost = material + _PACKAGING_FEE_CENTS + _OPS_FEE_CENTS + max(int(extras_cents), 0)
    sale = (cost * 100 + (100 - _MARGIN_PERCENT) - 1) // (100 - _MARGIN_PERCENT)
    sale = (sale + 99) // 100 * 100
    return min(max(sale, _MIN_LISTING_CENTS), _MAX_LISTING_CENTS)


def _extras(value: Any) -> tuple[dict[str, Any], ...]:
    """Normalize an extra-materials list to ``{name, price_cents}`` pairs."""

    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ReceiptError("Factory extra materials must be an array")
    items = []
    for item in value:
        if (
            not isinstance(item, Mapping)
            or not isinstance(item.get("name"), str)
            or type(item.get("price_cents")) is not int
        ):
            raise ReceiptError("Factory extra material is malformed")
        items.append({"name": item["name"], "price_cents": item["price_cents"]})
    return tuple(items)


def _extras_cents(items: Sequence[Mapping[str, Any]]) -> int:
    return sum(int(item["price_cents"]) for item in items)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@dataclass(frozen=True)
class SliceState:
    history_id: Optional[str]
    status: Optional[str]
    will_retry: bool
    weight_g: Optional[float]
    error: Optional[str]


def _slice_state(value: Mapping[str, Any]) -> SliceState:
    totals = value.get("totals") if isinstance(value.get("totals"), Mapping) else {}
    weight = totals.get("weight_g")
    error = value.get("error") if isinstance(value.get("error"), Mapping) else {}
    stage = error.get("stage")
    return SliceState(
        history_id=value.get("history_id") if isinstance(value.get("history_id"), str) else None,
        status=value.get("status") if isinstance(value.get("status"), str) else None,
        will_retry=value.get("will_retry") is True,
        weight_g=float(weight) if isinstance(weight, (int, float)) and weight > 0 else None,
        error=stage if isinstance(stage, str) else None,
    )


@dataclass(frozen=True)
class ListingState:
    """What an authenticated read shows of one public design right now."""

    design: Mapping[str, Any] = field(repr=False)
    slice: SliceState
    live_primary_sha256: Optional[str]

    @property
    def slug(self) -> Optional[str]:
        return self.design.get("slug")

    @property
    def design_id(self) -> Optional[str]:
        return self.design.get("id")

    @property
    def owner_id(self) -> Optional[str]:
        author = self.design.get("author") if isinstance(self.design.get("author"), Mapping) else {}
        return self.design.get("owner_id") or author.get("id")

    @property
    def status(self) -> Optional[str]:
        return self.design.get("status")

    @property
    def current_history_id(self) -> Optional[str]:
        return self.design.get("current_history_id")

    @property
    def published_history_id(self) -> Optional[str]:
        return self.design.get("published_history_id")

    @property
    def listing(self) -> Mapping[str, Any]:
        value = self.design.get("listing")
        return value if isinstance(value, Mapping) else {}

    @property
    def price_cents(self) -> Optional[int]:
        value = self.listing.get("price_cents")
        return value if type(value) is int else None

    @property
    def listing_active(self) -> Optional[bool]:
        value = self.listing.get("active")
        return value if isinstance(value, bool) else None

    @property
    def extra_materials(self) -> tuple[dict[str, Any], ...]:
        return _extras(self.design.get("extra_materials"))

    @property
    def infill_percent(self) -> Optional[int]:
        settings = self.design.get("print_settings")
        if isinstance(settings, Mapping) and type(settings.get("infill_percent")) is int:
            return settings["infill_percent"]
        return None

    @property
    def weight_g(self) -> Optional[float]:
        if self.slice.status == "done" and self.slice.history_id == self.current_history_id:
            return self.slice.weight_g
        return None

    @property
    def formula_price_cents(self) -> Optional[int]:
        return factory_sale_price_cents(self.weight_g, _extras_cents(self.extra_materials))

    @property
    def price_follows_formula(self) -> Optional[bool]:
        if self.price_cents is None or self.formula_price_cents is None:
            return None
        return self.price_cents == self.formula_price_cents


def _design(client: FactoryClient, slug: str) -> Mapping[str, Any]:
    response = client.get_design(slug)
    if response.status != 200:
        raise AmbiguousEffectError(
            "authenticated Factory readback returned HTTP %s" % response.status
        )
    return _json_body(response, "Factory design readback")


def _slice(client: FactoryClient, slug: str) -> SliceState:
    response = client.get_slice(slug)
    if response.status != 200:
        raise AmbiguousEffectError(
            "Factory slice readback returned HTTP %s" % response.status
        )
    return _slice_state(_json_body(response, "Factory slice readback"))


def read_listing_state(session: FactoryAgentSession, slug: str) -> ListingState:
    """Authenticated reads only: the design, its measurement and live facts."""

    client = FactoryClient(session.authenticated_transport)
    design = _design(client, slug)
    measurement = _slice(client, slug)
    primary = None
    if design.get("project_url"):
        facts = session.read_product_facts(design.get("project_url"))
        model = (facts or {}).get("primary_model")
        if isinstance(model, Mapping) and isinstance(model.get("sha256"), str):
            primary = model["sha256"]
    return ListingState(design=design, slice=measurement, live_primary_sha256=primary)


@dataclass(frozen=True)
class ListingUpdatePlan:
    """What one Listing Update would send, before any Factory read.

    ``source_primary_sha256`` is the archive's or project's own primary STEP,
    the bytes the printed-only primary is derived from. The handoff bytes
    themselves carry timestamps, so the confirmation code binds this, the
    bodies kept and removed, and the extras rather than a pack hash.
    """

    reason: str
    slug: str
    source_primary_path: str
    source_primary_sha256: str
    kept_bodies: tuple[str, ...]
    stripped_bodies: tuple[str, ...]
    extra_materials: tuple[dict[str, Any], ...]
    predicted_weight_g: Optional[float] = None
    predicted_weight_source: Optional[str] = None
    recorded_source_primary_sha256: Optional[str] = None
    recorded_history_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.reason not in LISTING_UPDATE_REASONS:
            raise ContractError("--reason must be one of %s" % ", ".join(LISTING_UPDATE_REASONS))
        require_sha256(self.source_primary_sha256, "source primary sha256")
        object.__setattr__(self, "extra_materials", _extras(list(self.extra_materials)))
        if (self.predicted_weight_g is None) != (self.predicted_weight_source is None):
            raise ContractError(
                "--predicted-grams and --predicted-grams-source go together"
            )
        if self.predicted_weight_g is not None and not (
            isinstance(self.predicted_weight_g, (int, float))
            and math.isfinite(self.predicted_weight_g)
            and self.predicted_weight_g > 0
        ):
            raise ContractError("--predicted-grams must be a positive number of grams")

    @property
    def extras_cents(self) -> int:
        return _extras_cents(self.extra_materials)

    @property
    def predicted_price_cents(self) -> Optional[int]:
        return factory_sale_price_cents(self.predicted_weight_g, self.extras_cents)

    def problems(self, state: ListingState, owner_id: str) -> list[str]:
        """Everything that refuses this update against what Factory shows now."""

        found = []
        if state.slug != self.slug:
            found.append("Factory answered for slug %s, not %s" % (state.slug, self.slug))
        if state.status != "public":
            found.append("the design is %s, not public; a draft is root repair's job" % state.status)
        if state.owner_id != owner_id:
            found.append("the design's author is not this Inventor's Factory account")
        if not state.current_history_id or state.current_history_id != state.published_history_id:
            found.append("the design's current version is not its published one")
        if state.weight_g is None:
            found.append(
                "the current version's measurement is %s, not done; wait for it"
                % (state.slice.status or "absent")
            )
        if state.infill_percent not in (None, FACTORY_DEFAULT_INFILL_PERCENT):
            found.append(
                "the live version prints at %s%% infill and a new version would drop that "
                "override; Workshop does not carry print overrides yet"
                % state.infill_percent
            )
        if self.reason == "reprice":
            same_as_live = state.live_primary_sha256 == self.source_primary_sha256
            same_as_recorded = (
                self.recorded_history_id is not None
                and self.recorded_history_id == state.current_history_id
                and self.recorded_source_primary_sha256 == self.source_primary_sha256
            )
            if not (same_as_live or same_as_recorded):
                found.append(
                    "a reprice must publish the live printed geometry: %s is not the primary "
                    "the live version was made from (%s); publish it as --reason fix with "
                    "fresh gate evidence"
                    % (self.source_primary_path, state.live_primary_sha256 or "not recorded")
                )
        if self.predicted_price_cents is None:
            found.append(
                "no predicted price: pass --predicted-grams G --predicted-grams-source TEXT, "
                "measured with Factory's slice worker on the printed-only primary"
            )
        return found

    def confirmation_document(self, state: ListingState) -> dict[str, Any]:
        return {
            "kind": "workshop.factory-listing-update-confirmation",
            "slug": state.slug,
            "design_id": state.design_id,
            "base_history_id": state.current_history_id,
            "current_price_cents": state.price_cents,
            "current_weight_g": state.weight_g,
            "current_extra_materials": list(state.extra_materials),
            "reason": self.reason,
            "source_primary_sha256": self.source_primary_sha256,
            "kept_bodies": list(self.kept_bodies),
            "stripped_bodies": list(self.stripped_bodies),
            "extra_materials": list(self.extra_materials),
            "predicted_weight_g": self.predicted_weight_g,
            "predicted_price_cents": self.predicted_price_cents,
        }

    def confirmation_code(self, state: ListingState) -> Optional[str]:
        """A short code for exactly this update against exactly this state."""

        if self.predicted_price_cents is None:
            return None
        digest = hashlib.sha256(_canonical(self.confirmation_document(state))).hexdigest()
        return "lu-" + digest[:12]


@dataclass(frozen=True)
class ListingUpdateBindings:
    """The exact handoff and Release identities the ledger binds."""

    content: bytes = field(repr=False)
    pack_sha256: str
    handoff_artifact_sha256: str
    product_artifact_sha256: str
    release_sha256: str
    playtest_evidence_sha256: str
    product_page_sha256: str
    primary_model_sha256: str
    product_facts_sha256: str


class FactoryListingUpdate:
    """Run, or reconcile, one confirmed Listing Update through the ledger."""

    def __init__(
        self,
        ledger: EffectLedger,
        session: FactoryAgentSession,
        *,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        slice_wait_seconds: float = SLICE_WAIT_SECONDS,
        poll_seconds: float = SLICE_POLL_SECONDS,
    ) -> None:
        if not isinstance(ledger, EffectLedger):
            raise ContractError("Listing Update requires an EffectLedger")
        if not isinstance(session, FactoryAgentSession):
            raise ContractError("Listing Update requires an agent session")
        self.ledger = ledger
        self.session = session
        self.sleeper = sleeper
        self.clock = clock
        self.slice_wait_seconds = slice_wait_seconds
        self.poll_seconds = poll_seconds

    def preview(self, plan: ListingUpdatePlan) -> tuple[ListingState, list[str], Optional[str]]:
        identity = self.session.login()
        state = read_listing_state(self.session, plan.slug)
        return state, plan.problems(state, identity.owner_id), plan.confirmation_code(state)

    def pending(self, product_id: str) -> Optional[EffectIntent]:
        """The latest Listing Update intent of this product, if any."""

        intent = self.ledger.latest(product_id, LISTING_UPDATE_KIND)
        if intent is None or not isinstance(intent.request.get("listing_update"), Mapping):
            return None
        return intent

    def run(
        self,
        *,
        product_id: str,
        plan: ListingUpdatePlan,
        bindings: ListingUpdateBindings,
        confirm: str,
    ) -> Receipt:
        identity = self.session.login()
        earlier = self.pending(product_id)
        if earlier is not None and earlier.request["listing_update"].get("confirmation_code") == confirm:
            if earlier.state == "succeeded":
                assert earlier.receipt is not None
                return earlier.receipt
            if earlier.state == "rejected":
                raise EffectError("Factory rejected this exact Listing Update; preview again")
            if earlier.state in ("sending", "unknown"):
                if earlier.state == "sending":
                    earlier = self.ledger.strand_as_unknown(
                        earlier.intent_id, "host exited while the version was sending"
                    )
                return self._complete(earlier, identity.owner_id)
        if earlier is not None and earlier.state in ("sending", "unknown"):
            raise AmbiguousEffectError(
                "an earlier Listing Update (code %s) is unresolved: %s. Rerun with "
                "--confirm %s to reconcile it before any new update"
                % (earlier.request["listing_update"].get("confirmation_code"),
                   earlier.error or earlier.state,
                   earlier.request["listing_update"].get("confirmation_code"))
            )
        state = read_listing_state(self.session, plan.slug)
        problems = plan.problems(state, identity.owner_id)
        if problems:
            raise ContractError("Listing Update refused: %s" % "; ".join(problems))
        code = plan.confirmation_code(state)
        if code != confirm:
            raise ContractError(
                "confirmation code %s does not match this update now (%s): Factory or the "
                "bytes changed since the preview; preview again and confirm the new code"
                % (confirm, code)
            )
        if earlier is not None and earlier.state == "planned" and earlier.request[
            "listing_update"
        ].get("confirmation_code") == confirm and earlier.pack_sha256 == bindings.pack_sha256:
            intent = earlier
        else:
            intent = self.ledger.prepare(
                kind=LISTING_UPDATE_KIND,
                product_id=product_id,
                request=self._request(plan, state, bindings, code, identity.owner_id),
                pack_sha256=bindings.pack_sha256,
                handoff_artifact_sha256=bindings.handoff_artifact_sha256,
                product_artifact_sha256=bindings.product_artifact_sha256,
                release_sha256=bindings.release_sha256,
                playtest_evidence_sha256=bindings.playtest_evidence_sha256,
                supersede_settled=True,
            )
        if intent.state != "planned":
            raise StateConflict("Listing Update intent is %s, not planned" % intent.state)
        return self._send(intent, bindings, identity.owner_id)

    @staticmethod
    def _request(
        plan: ListingUpdatePlan,
        state: ListingState,
        bindings: ListingUpdateBindings,
        code: str,
        owner_id: str,
    ) -> dict[str, Any]:
        return {
            "method": "POST",
            "api_origin": _api_origin(DEFAULT_FACTORY_API),
            "path": "/designs/%s/import" % urllib.parse.quote(plan.slug, safe=""),
            "owner_id": owner_id,
            "design_id": state.design_id,
            "slug": plan.slug,
            "base_history_id": state.current_history_id,
            "product_page_sha256": bindings.product_page_sha256,
            "publication_anchor_path": FACTORY_RELEASE_PAGE_PATH,
            "publication_anchor_sha256": bindings.product_page_sha256,
            "primary_model_sha256": bindings.primary_model_sha256,
            "product_facts_sha256": bindings.product_facts_sha256,
            "listing_update": {
                "reason": plan.reason,
                "confirmation_code": code,
                "source_primary_path": plan.source_primary_path,
                "source_primary_sha256": plan.source_primary_sha256,
                "kept_bodies": list(plan.kept_bodies),
                "stripped_bodies": list(plan.stripped_bodies),
                "extra_materials": list(plan.extra_materials),
                "base_price_cents": state.price_cents,
                "base_weight_g": state.weight_g,
                "base_extra_materials": list(state.extra_materials),
                "predicted_weight_g": plan.predicted_weight_g,
                "predicted_weight_source": plan.predicted_weight_source,
                "predicted_price_cents": plan.predicted_price_cents,
            },
        }

    def _send(self, intent: EffectIntent, bindings: ListingUpdateBindings, owner_id: str) -> Receipt:
        client = FactoryClient(self.session.authenticated_transport)
        sending = self.ledger.begin(intent.intent_id)
        assert sending.effect_token is not None
        slug = sending.request["slug"]
        try:
            response = client.import_model_version(
                slug, content=bindings.content, idempotency_key=sending.idempotency_key
            )
        except Exception:  # noqa: BLE001 - any loss leaves the outcome unknown
            unknown = self.ledger.mark_unknown(
                sending.intent_id, sending.effect_token,
                "the version POST got no response; reconcile by readback",
            )
            return self._complete(unknown, owner_id)
        if 200 <= response.status < 300:
            unknown = self.ledger.mark_unknown(
                sending.intent_id, sending.effect_token,
                "the version was accepted; waiting for its slice and extras",
                response={"status": response.status},
            )
            return self._complete(unknown, owner_id)
        if 400 <= response.status < 500 and response.status not in (408, 429):
            try:
                design = _design(client, slug)
            except (AmbiguousEffectError, ContractError, EffectError) as exc:
                self.ledger.mark_unknown(
                    sending.intent_id, sending.effect_token,
                    "Factory refused the version with HTTP %s and readback failed" % response.status,
                )
                raise AmbiguousEffectError(
                    "Factory refused the version with HTTP %s and readback could not "
                    "prove nothing changed" % response.status
                ) from exc
            if design.get("current_history_id") == sending.request["base_history_id"]:
                self.ledger.mark_rejected(
                    sending.intent_id, sending.effect_token,
                    "Factory refused the version with HTTP %s" % response.status,
                    response={"status": response.status},
                )
                raise EffectError(
                    "Factory refused the version with HTTP %s; nothing changed" % response.status
                )
        unknown = self.ledger.mark_unknown(
            sending.intent_id, sending.effect_token,
            "the version POST returned HTTP %s; reconcile by readback" % response.status,
            response={"status": response.status},
        )
        return self._complete(unknown, owner_id)

    def _stay_unknown(self, intent: EffectIntent, message: str, **response: Any) -> None:
        self.ledger.note_unknown(intent.intent_id, message, response=response or None)
        raise AmbiguousEffectError(message)

    def _complete(self, intent: EffectIntent, owner_id: str) -> Receipt:
        """Steps 3 and 4 by readback alone. Never resends the version."""

        client = FactoryClient(self.session.authenticated_transport)
        request = intent.request
        update = request["listing_update"]
        slug = request["slug"]
        base = request["base_history_id"]
        design = _design(client, slug)
        if design.get("id") != request["design_id"] or design.get("slug") != slug:
            raise StateConflict("Factory readback names another design; the owner decides")
        current = design.get("current_history_id")
        if current == base:
            self._stay_unknown(
                intent,
                "Factory still shows the base version %s: the version may not have landed. "
                "Nothing is resent; the owner decides whether to preview again" % base,
            )
        try:
            anchor = self.session.verify_publication_anchor(
                design.get("project_url"), request["publication_anchor_sha256"]
            )
        except ReceiptError as exc:
            raise StateConflict(
                "Factory's current version %s is not this update's; the owner decides" % current
            ) from exc
        if design.get("status") != "public" or design.get("published_history_id") != current:
            self._stay_unknown(
                intent, "the new version %s is not the published one yet" % current,
                history_id=current,
            )
        measured = self._await_slice(client, intent, slug, current)
        extras = list(update["extra_materials"])
        if list(_extras(design.get("extra_materials"))) != extras:
            try:
                response = client.put_extra_materials(slug, extras)
            except Exception as exc:  # noqa: BLE001 - PUT is safe to resend
                self._stay_unknown(
                    intent, "the extras write got no response; rerun to send it again",
                    history_id=current,
                )
                raise AssertionError from exc  # pragma: no cover - _stay_unknown raises
            if not 200 <= response.status < 300:
                self._stay_unknown(
                    intent,
                    "the extras write returned HTTP %s; rerun to send it again" % response.status,
                    history_id=current,
                )
            design = _design(client, slug)
        if list(_extras(design.get("extra_materials"))) != extras:
            self._stay_unknown(
                intent, "Factory's extras read back different; rerun to send them again",
                history_id=current,
            )
        extras_cents = _extras_cents(extras)
        formula = factory_sale_price_cents(measured, extras_cents)
        listing = design.get("listing") if isinstance(design.get("listing"), Mapping) else {}
        price = listing.get("price_cents") if type(listing.get("price_cents")) is int else None
        details = {
            "kind": "factory-listing-update",
            "reason": update["reason"],
            "confirmation_code": update["confirmation_code"],
            "base_history_id": base,
            "history_id": current,
            "page_url": _factory_product_page_url(slug),
            "publication_mode": "make-output-v1",
            "publication_anchor_path": FACTORY_RELEASE_PAGE_PATH,
            "publication_anchor_sha256": request["publication_anchor_sha256"],
            "product_page_sha256": request["product_page_sha256"],
            "primary_model_sha256": request["primary_model_sha256"],
            "product_facts_sha256": request["product_facts_sha256"],
            "source_primary_sha256": update["source_primary_sha256"],
            "extra_materials": extras,
            "price_before_cents": update["base_price_cents"],
            "price_after_cents": price,
            "predicted_price_cents": update["predicted_price_cents"],
            "formula_price_cents": formula,
            "price_follows_formula": price is not None and price == formula,
            "weight_before_g": update["base_weight_g"],
            "weight_after_g": measured,
            "predicted_weight_g": update["predicted_weight_g"],
            **anchor,
        }
        receipt = _factory_receipt(design, intent, details)
        receipt.assert_owner(owner_id)
        if not receipt.is_verified_public:
            self._stay_unknown(
                intent,
                "the listing does not read back active after the update; the owner decides",
                history_id=current,
            )
        completed = self.ledger.resolve_succeeded(intent.intent_id, receipt, design)
        assert completed.receipt is not None
        return completed.receipt

    def _await_slice(
        self, client: FactoryClient, intent: EffectIntent, slug: str, history_id: str
    ) -> float:
        deadline = self.clock() + self.slice_wait_seconds
        while True:
            measured = _slice(client, slug)
            if measured.history_id == history_id:
                if measured.status == "done" and measured.weight_g is not None:
                    return measured.weight_g
                if measured.status == "failed" and not measured.will_retry:
                    self._stay_unknown(
                        intent,
                        "Factory's slice of the new version failed (%s); the extras were not "
                        "sent and Factory pauses a platform price. The owner decides"
                        % (measured.error or "no stage given"),
                        history_id=history_id,
                    )
            if self.clock() >= deadline:
                self._stay_unknown(
                    intent,
                    "Factory's slice of the new version is still %s; the extras wait for it. "
                    "Rerun the same command to keep waiting" % (measured.status or "absent"),
                    history_id=history_id,
                )
            self.sleeper(self.poll_seconds)


def listing_update_version(receipt: Receipt) -> dict[str, Any]:
    """One ``versions[]`` entry for a schema 2 PUBLICATION.json."""

    details = receipt.details
    return {
        "history_id": details["history_id"],
        "base_history_id": details["base_history_id"],
        "observed_at": receipt.observed_at,
        "reason": details["reason"],
        "confirmation_code": details["confirmation_code"],
        "pack_sha256": receipt.payload_sha256,
        "primary_model_sha256": details["primary_model_sha256"],
        "source_primary_sha256": details["source_primary_sha256"],
        "extra_materials": details["extra_materials"],
        "price_before_cents": details["price_before_cents"],
        "price_after_cents": details["price_after_cents"],
        "predicted_price_cents": details["predicted_price_cents"],
        "price_follows_formula": details["price_follows_formula"],
        "weight_before_g": details["weight_before_g"],
        "weight_after_g": details["weight_after_g"],
        "predicted_weight_g": details["predicted_weight_g"],
    }


def append_publication_version(record: Mapping[str, Any], version: Mapping[str, Any]) -> dict[str, Any]:
    """Return a schema 2 PUBLICATION.json with ``version`` appended.

    A schema 1 record (no ``versions``) is read as having none. The first
    publication's slug and page stay; ``listing`` becomes the latest price.
    """

    updated = json.loads(json.dumps(dict(record)))
    versions = list(updated.get("versions") or [])
    if any(entry.get("history_id") == version["history_id"] for entry in versions):
        return updated
    versions.append(dict(version))
    updated["schema_version"] = 2
    updated["versions"] = versions
    publication = dict(updated.get("publication") or {})
    if version.get("price_after_cents") is not None:
        listing = dict(publication.get("listing") or {})
        listing["price_cents"] = version["price_after_cents"]
        listing.setdefault("currency", "USD")
        publication["listing"] = listing
    updated["publication"] = publication
    return updated


__all__ = [
    "FACTORY_DEFAULT_INFILL_PERCENT",
    "FactoryListingUpdate",
    "ListingState",
    "ListingUpdateBindings",
    "ListingUpdatePlan",
    "append_publication_version",
    "factory_sale_price_cents",
    "listing_update_version",
    "read_listing_state",
]
