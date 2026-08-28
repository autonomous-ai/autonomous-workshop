"""A fake game vault API at the outbound HTTP boundary, for host tests.

Serves the :data:`tests.invent.test_vault.FIXTURE` nodes (or any mapping of
node path to markdown) through the same request and response rules the real
client applies, and records every write so a test can assert what the host
banked.  ``install_fake_gamevault`` swaps the host's client for one over this
transport for the lifetime of a test case.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from workshop.invent.gamevault import GameVaultClient, GameVaultConfig, HttpResponse
from workshop.invent.vault import Vault, parse_node
from tests.invent.test_vault import FIXTURE, node

FAKE_TOKEN = "fake-vault-token"
# The end-to-end fixtures declare these mechanisms; each carries one risk so a
# run always receives leads and never a refusal.
E2E_NODES = {
    **FIXTURE,
    "mechanisms/stacking-and-balancing": node(
        "mechanism", "Stacking and Balancing",
        relations=(("risks", ("anti-patterns/handling-wipe",)),),
    ),
    "mechanisms/square-grid": node(
        "mechanism", "Square Grid", relations=(("risks", ("anti-patterns/idle-player",)),)
    ),
    "anti-patterns/handling-wipe": node(
        "anti-pattern", "Handling Wipe",
        relations=(("mitigated-by", ("rule-patterns/simultaneous-reveal",)),),
    ),
    "constraints/fdm-printed-components-only": node(
        "constraint", "FDM Printed Components Only",
        relations=(("component", ("components/token",)),),
    ),
}
FAKE_URL = "http://gamevault.test:8090"


class FakeGameVaultTransport:
    """Stateful double for ``/api/gamevault/*``; every call is recorded."""

    def __init__(self, nodes=None, *, token=FAKE_TOKEN, fail=False):
        self.nodes = dict(FIXTURE if nodes is None else nodes)
        self.token = token
        self.fail = fail
        self.calls = []
        self.evidence = []
        self.review = []

    def vault(self):
        return Vault({path: parse_node(text) for path, text in self.nodes.items()})

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url))
        if self.fail:
            raise OSError("fixture vault is down")
        if headers.get("Authorization") != "Bearer " + self.token:
            return self._json(401, {"error": "invalid or missing admin token"})
        path = url.split("?", 1)[0].replace(FAKE_URL, "", 1)
        payload = json.loads(body.decode("utf-8")) if body else {}
        if path == "/api/gamevault/export":
            return self._json(200, {"count": len(self.nodes), "nodes": self.nodes})
        if path == "/api/gamevault/check":
            query = url.split("?", 1)[1] if "?" in url else ""
            paths = [item for item in query.replace("paths=", "").replace("%2F", "/").split("%2C") if item]
            if not paths:
                return self._json(400, {"error": "paths must be a non-empty list of node paths"})
            return self._json(200, {"paths": paths, "findings": self.vault().check_compatibility(paths)})
        if path == "/api/gamevault/leads":
            concept = payload.get("concept") or {}
            vault = self.vault()
            resolved = vault.resolve_concept_mechanisms(concept)
            members = [node for node in resolved.values() if node is not None]
            members += [item for item in vault.constraints() if item not in members]
            return self._json(200, {"mechanisms": resolved, "members": members, "findings": vault.check_compatibility(members)})
        if path == "/api/gamevault/evidence":
            self.evidence.append(payload)
            return self._json(200, {"tally": {"did": len(payload.get("rows", [])), "skip": 0, "new": 0}, "lint": "clean", "committed": True})
        if path == "/api/gamevault/review":
            self.review.append(payload)
            return self._json(200, {"tally": {"did": len(payload.get("dismissals", [])), "skip": 0, "missing": 0}, "lint": "clean", "committed": True})
        return HttpResponse(404, {}, b"404 page not found")

    @staticmethod
    def _json(status, document):
        return HttpResponse(status, {"Content-Type": "application/json"}, json.dumps(document).encode("utf-8"))


def fake_client(transport):
    return GameVaultClient(GameVaultConfig(FAKE_URL, FAKE_TOKEN), transport)


def install_fake_gamevault(case, transport=None, *, targets=("workshop.workflow.native_run._gamevault_client",)):
    """Route the host's vault client through ``transport`` for one test case."""

    transport = FakeGameVaultTransport() if transport is None else transport
    for target in targets:
        patcher = mock.patch(target, return_value=fake_client(transport))
        patcher.start()
        case.addCleanup(patcher.stop)
    return transport


__all__ = ["E2E_NODES", "FAKE_TOKEN", "FAKE_URL", "FakeGameVaultTransport", "fake_client", "install_fake_gamevault"]
