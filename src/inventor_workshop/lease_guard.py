"""Renewable product leases for long-running Workshop stages.

``InventorStore`` fencing tokens make state mutations safe, but one Invent,
Make, or Playtest job may outlive a fixed lease.  :class:`LeaseGuard` keeps one
token alive while the owner is working and permanently fails closed if renewal
becomes uncertain.  Call :meth:`LeaseGuard.assert_current` immediately before
publishing a checkpoint, committing a transition, or beginning an external
effect; the durable operation must still receive the returned fencing token.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional, Protocol

from .errors import ContractError, StateConflict


DEFAULT_LEASE_TTL_SECONDS = 300
DEFAULT_RENEW_INTERVAL_SECONDS = 60


class LeaseRuntime(Protocol):
    """The narrow durable lease surface used by :class:`LeaseGuard`."""

    def acquire_lease(
        self, product_id: str, holder: str, ttl_seconds: int = 2700
    ) -> str: ...

    def renew_lease(
        self, product_id: str, token: str, ttl_seconds: int = 2700
    ) -> str: ...

    def release_lease(self, product_id: str, token: str) -> bool: ...


Wait = Callable[[float], bool]


def _method(runtime: Any, name: str) -> Callable[..., Any]:
    operation = getattr(runtime, name, None)
    if not callable(operation):
        raise ContractError("LeaseGuard runtime must implement %s()" % name)
    return operation


def _identifier(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 512
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("LeaseGuard %s must be a bounded identifier" % label)
    return value


def _timing(ttl_seconds: int, renew_interval_seconds: float) -> tuple[int, float]:
    if (
        type(ttl_seconds) is not int
        or ttl_seconds < 2
        or ttl_seconds > 24 * 60 * 60
    ):
        raise ContractError(
            "LeaseGuard ttl_seconds must be an integer from 2 to 86400"
        )
    if (
        not isinstance(renew_interval_seconds, (int, float))
        or isinstance(renew_interval_seconds, bool)
        or not 0 < float(renew_interval_seconds) <= ttl_seconds / 2
    ):
        raise ContractError(
            "LeaseGuard renew_interval_seconds must be positive and no more than half the TTL"
        )
    return ttl_seconds, float(renew_interval_seconds)


class LeaseGuard:
    """Own and renew one product fencing token until work finishes.

    A renewal or injected-wait failure is latched permanently.  This deliberate
    fail-closed rule prevents a transiently disconnected worker from accepting
    output after another worker could have acquired the product.  The backing
    store remains the final authority: callers must pass the token returned by
    :meth:`assert_current` into every fenced durable operation.
    """

    def __init__(
        self,
        runtime: LeaseRuntime,
        product_id: str,
        token: str,
        *,
        ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
        renew_interval_seconds: float = DEFAULT_RENEW_INTERVAL_SECONDS,
        release_on_close: bool = True,
        wait: Optional[Wait] = None,
    ) -> None:
        self._runtime = runtime
        self._product_id = product_id
        self._token = token
        self._ttl_seconds, self._renew_interval_seconds = _timing(
            ttl_seconds, renew_interval_seconds
        )
        _identifier(product_id, "product_id")
        _identifier(token, "fencing token")
        for name in ("renew_lease", "release_lease"):
            _method(runtime, name)
        if not isinstance(release_on_close, bool):
            raise ContractError("LeaseGuard release_on_close must be boolean")
        if wait is not None and not callable(wait):
            raise ContractError("LeaseGuard wait must be callable")

        self._release_on_close = release_on_close
        self._stop = threading.Event()
        self._wait = wait or self._stop.wait
        self._state_lock = threading.Lock()
        self._renew_lock = threading.Lock()
        self._failure: Optional[BaseException] = None
        self._closed = False
        self._released: Optional[bool] = None
        self._thread = threading.Thread(
            target=self._heartbeat,
            name="workshop-lease-%s" % product_id[:48],
            daemon=True,
        )

    @classmethod
    def acquire(
        cls,
        runtime: LeaseRuntime,
        product_id: str,
        holder: str,
        *,
        ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
        renew_interval_seconds: float = DEFAULT_RENEW_INTERVAL_SECONDS,
        release_on_close: bool = True,
        wait: Optional[Wait] = None,
    ) -> "LeaseGuard":
        """Acquire a new lease and begin renewal without bypassing LeaseBusy."""

        ttl_seconds, renew_interval_seconds = _timing(
            ttl_seconds, renew_interval_seconds
        )
        acquire = _method(runtime, "acquire_lease")
        release = _method(runtime, "release_lease")
        _method(runtime, "renew_lease")
        _identifier(product_id, "product_id")
        _identifier(holder, "holder")
        if not isinstance(release_on_close, bool):
            raise ContractError("LeaseGuard release_on_close must be boolean")
        if wait is not None and not callable(wait):
            raise ContractError("LeaseGuard wait must be callable")
        token = acquire(product_id, holder, ttl_seconds=ttl_seconds)
        try:
            guard = cls(
                runtime,
                product_id,
                token,
                ttl_seconds=ttl_seconds,
                renew_interval_seconds=renew_interval_seconds,
                release_on_close=release_on_close,
                wait=wait,
            )
            guard._thread.start()
        except BaseException:
            try:
                release(product_id, token)
            except Exception:
                pass
            raise
        return guard

    @classmethod
    def hold(
        cls,
        runtime: LeaseRuntime,
        product_id: str,
        token: str,
        *,
        ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
        renew_interval_seconds: float = DEFAULT_RENEW_INTERVAL_SECONDS,
        release_on_close: bool = True,
        wait: Optional[Wait] = None,
    ) -> "LeaseGuard":
        """Verify, extend, and renew an existing fencing token."""

        guard = cls(
            runtime,
            product_id,
            token,
            ttl_seconds=ttl_seconds,
            renew_interval_seconds=renew_interval_seconds,
            release_on_close=release_on_close,
            wait=wait,
        )
        try:
            guard._renew_or_latch()
            guard._raise_if_unavailable()
            guard._thread.start()
        except BaseException:
            if release_on_close:
                try:
                    _method(runtime, "release_lease")(product_id, token)
                except BaseException:
                    pass
            raise
        return guard

    @property
    def token(self) -> str:
        """The opaque fencing token; durable mutations must still validate it."""

        return self._token

    @property
    def lost(self) -> bool:
        """Whether renewal became uncertain or the guard was closed."""

        with self._state_lock:
            return self._failure is not None or self._closed

    def _latch(self, failure: BaseException) -> None:
        with self._state_lock:
            if self._failure is None:
                self._failure = failure

    def _raise_if_unavailable(self) -> None:
        with self._state_lock:
            failure = self._failure
            closed = self._closed
        if failure is not None:
            raise StateConflict(
                "Workshop product lease renewal failed; this worker may not commit output"
            ) from failure
        if closed:
            raise StateConflict(
                "Workshop product lease guard is closed; this worker may not commit output"
            )

    def _renew_or_latch(self) -> None:
        try:
            with self._renew_lock:
                _method(self._runtime, "renew_lease")(
                    self._product_id,
                    self._token,
                    ttl_seconds=self._ttl_seconds,
                )
        except BaseException as exc:
            self._latch(exc)

    def _heartbeat(self) -> None:
        while True:
            try:
                stopping = self._wait(self._renew_interval_seconds)
            except BaseException as exc:
                self._latch(exc)
                return
            if stopping or self._stop.is_set():
                return
            with self._state_lock:
                if self._failure is not None or self._closed:
                    return
            self._renew_or_latch()
            with self._state_lock:
                if self._failure is not None:
                    return

    def assert_current(self) -> str:
        """Synchronously prove ownership before accepting any durable effect."""

        self._raise_if_unavailable()
        self._renew_or_latch()
        self._raise_if_unavailable()
        return self._token

    def close(self) -> bool:
        """Stop renewal and release this guard's token exactly once."""

        with self._state_lock:
            if self._closed:
                return bool(self._released) if self._release_on_close else True
            self._closed = True
        self._stop.set()
        if self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join()
        if not self._release_on_close:
            with self._state_lock:
                self._released = True
            return True
        try:
            released = bool(
                _method(self._runtime, "release_lease")(
                    self._product_id, self._token
                )
            )
        except BaseException as exc:
            self._latch(exc)
            raise StateConflict("Workshop product lease could not be released") from exc
        with self._state_lock:
            self._released = released
        if not released:
            failure = StateConflict(
                "Workshop product lease was already missing or replaced during release"
            )
            self._latch(failure)
            raise failure
        return True

    def __enter__(self) -> "LeaseGuard":
        try:
            self._raise_if_unavailable()
        except StateConflict:
            try:
                self.close()
            except StateConflict:
                pass
            raise
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        del traceback
        if exc_type is None:
            self.close()
        else:
            try:
                self.close()
            except StateConflict:
                # Preserve the job failure; the guard remains permanently lost.
                pass
        return False


__all__ = [
    "DEFAULT_LEASE_TTL_SECONDS",
    "DEFAULT_RENEW_INTERVAL_SECONDS",
    "LeaseGuard",
    "LeaseRuntime",
]
