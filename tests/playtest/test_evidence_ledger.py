"""The cross-run evidence ledger: rows, ranking, write-back, review, harvest."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.playtest.test_native_playtested import NativePlaytestedTest
from workshop.errors import ContractError, StateConflict
from workshop.playtest.evidence_ledger import (
    MAX_LEDGER_BYTES,
    append_rows,
    build_rows,
    harvest,
    ledger_path,
    provenance_weight,
    read_ledger,
    recall,
    review_queue,
    write_back,
)


LEAD = {"id": "a" * 16, "kind": "risk", "nodes": ["mechanisms/hand-off", "anti-patterns/idle-player"]}
LEAD_B = {"id": "b" * 16, "kind": "risk", "nodes": ["mechanisms/hand-off", "anti-patterns/turtling"]}


def playtested_document(*, confirm=True, extra_feedback=()):
    checks = [
        {
            "check_id": "agent-playtest",
            "evidence_ref": "results/agent-playtest.json",
            "observed_at": "2026-08-27T10:00:00Z",
            "observations": {
                "evidence_class": "codex-authored-digital-game-assessment",
                "vault_leads": [
                    {"lead": LEAD["id"], "verdict": "confirmed" if confirm else "dismissed",
                     "why": "Seen at the table." if confirm else "No exposure.",
                     "feedback_code": "idle-seat" if confirm else None},
                    {"lead": LEAD_B["id"], "verdict": "dismissed", "why": "Competitive game.", "feedback_code": None},
                ],
            },
        },
        {
            "check_id": "mechanical-check",
            "evidence_ref": "results/mechanical-check.json",
            "observed_at": "2026-08-27T11:00:00Z",
            "observations": {"evidence_class": "deterministic-digital-check"},
        },
    ]
    feedback = [
        {"code": "idle-seat", "area": "play", "severity": "improve", "finding": "One seat idles.",
         "change": "Add a simultaneous reveal.", "evidence_refs": ["results/agent-playtest.json"]},
        {"code": "loose-fit", "area": "make", "severity": "block", "finding": "The lid rattles.",
         "change": "Tighten the lip by 0.2 mm.", "evidence_refs": ["results/mechanical-check.json"]},
        {"code": "no-refs", "area": "play", "severity": "note", "finding": "Fine.", "change": "None.",
         "evidence_refs": []},
        *extra_feedback,
    ]
    return {"checks": checks, "feedback": feedback}


class BuildRowsTest(unittest.TestCase):
    def test_weights_symptoms_and_refs(self):
        rows = build_rows("wish-a", 2, playtested_document(), [LEAD, LEAD_B], ["mechanisms/hand-off", "", "mechanisms/hand-off"])
        self.assertEqual([row["ref"] for row in rows], ["wish-a#r2:idle-seat", "wish-a#r2:loose-fit", "wish-a#r2:no-refs"])
        self.assertEqual([row["weight"] for row in rows], [2, 3, 1])
        self.assertEqual([row["symptom"] for row in rows], ["anti-patterns/idle-player", None, None])
        self.assertEqual(rows[0]["evidence_class"], "codex-authored-digital-game-assessment")
        self.assertIsNone(rows[2]["evidence_class"])
        self.assertEqual(rows[0]["mechanisms"], ["mechanisms/hand-off"])
        self.assertEqual(rows[0]["observed_at"], "2026-08-27T11:00:00Z")
        self.assertEqual(build_rows("wish-a", 1, {"checks": [], "feedback": []}, [], []), [])
        dismissed = build_rows("wish-a", 1, playtested_document(confirm=False), [LEAD], [])
        self.assertIsNone(dismissed[0]["symptom"])
        malformed_lead = build_rows("wish-a", 1, playtested_document(), [{"id": LEAD["id"], "nodes": ["only-one"]}], [])
        self.assertIsNone(malformed_lead[0]["symptom"])
        for kind, weight in (("physical-receipt", 4), ("deterministic-digital-check", 3), ("codex-authored", 2), ("agent-playtest", 2), ("other", 1), (None, 1)):
            self.assertEqual(provenance_weight(kind), weight)
        with self.assertRaisesRegex(ContractError, "product_id"):
            build_rows("bad id!", 1, playtested_document(), [], [])
        with self.assertRaisesRegex(ContractError, "round"):
            build_rows("wish-a", 0, playtested_document(), [], [])


class LedgerFileTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.rows = build_rows("wish-a", 1, playtested_document(), [LEAD, LEAD_B], ["mechanisms/hand-off"])

    def test_append_is_idempotent_and_private(self):
        self.assertEqual(read_ledger(self.home), [])
        self.assertEqual(append_rows(self.home, self.rows), {"written": 3, "kept": 0})
        self.assertEqual(append_rows(self.home, self.rows), {"written": 0, "kept": 3})
        self.assertEqual(oct(ledger_path(self.home).stat().st_mode & 0o777), oct(0o600))
        self.assertEqual([row["ref"] for row in read_ledger(self.home)], [row["ref"] for row in self.rows])
        more = build_rows("wish-b", 1, playtested_document(), [LEAD], ["mechanisms/hand-off"])
        self.assertEqual(append_rows(self.home, more + self.rows), {"written": 3, "kept": 3})

    def test_ledger_validation_fails_closed(self):
        path = ledger_path(self.home)
        path.parent.mkdir()
        path.write_text('{"ref": "x"}\n', encoding="utf-8")
        with self.assertRaisesRegex(StateConflict, "row fields are invalid"):
            read_ledger(self.home)
        path.write_text("not json\n", encoding="utf-8")
        with self.assertRaisesRegex(StateConflict, "line 1 is not JSON"):
            read_ledger(self.home)
        bad = dict(self.rows[0]); bad["round"] = "1"
        path.write_text(json.dumps(bad) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(StateConflict, "row identity is invalid"):
            read_ledger(self.home)
        bad = dict(self.rows[0]); bad["weight"] = "3"
        path.write_text(json.dumps(bad) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(StateConflict, "row tags are invalid"):
            read_ledger(self.home)
        path.write_text("\n\n", encoding="utf-8")
        self.assertEqual(read_ledger(self.home), [])
        path.unlink()
        path.symlink_to(self.home / "elsewhere")
        with self.assertRaisesRegex(StateConflict, "regular file"):
            read_ledger(self.home)
        path.unlink()
        with path.open("wb") as handle:
            handle.truncate(MAX_LEDGER_BYTES + 1)
        with self.assertRaisesRegex(StateConflict, "size limit"):
            read_ledger(self.home)
        with self.assertRaisesRegex(StateConflict, "row fields are invalid"):
            append_rows(self.home / "fresh", [{"ref": "x"}])
        path.unlink()
        path.mkdir()
        with self.assertRaisesRegex(StateConflict, "regular file"):
            read_ledger(self.home)

    def test_recall_ranks_by_weight_overlap_recency_and_excludes_self(self):
        a = build_rows("wish-a", 1, playtested_document(), [LEAD], ["mechanisms/hand-off", "mechanisms/x"])
        b = build_rows("wish-b", 1, playtested_document(), [LEAD], ["mechanisms/hand-off"])
        for row in b:
            row["observed_at"] = "2026-09-01T00:00:00Z"
        c = build_rows("wish-c", 1, playtested_document(), [LEAD], ["mechanisms/other"])
        append_rows(self.home, a + b + c)
        got = recall(self.home, ["mechanisms/hand-off", "mechanisms/x"], exclude_product="wish-z")
        self.assertEqual(
            [row["ref"] for row in got],
            [
                "wish-a#r1:loose-fit",   # weight 3, shares 2
                "wish-b#r1:loose-fit",   # weight 3, shares 1
                "wish-a#r1:idle-seat",   # weight 2, shares 2
                "wish-b#r1:idle-seat",   # weight 2, shares 1
                "wish-a#r1:no-refs",
                "wish-b#r1:no-refs",
            ],
        )
        self.assertEqual([row["product_id"] for row in recall(self.home, ["mechanisms/hand-off"], exclude_product="wish-a")], ["wish-b"] * 3)
        self.assertEqual(recall(self.home, []), [])
        self.assertEqual(recall(self.home, ["mechanisms/none"]), [])
        self.assertEqual(len(recall(self.home, ["mechanisms/hand-off"], limit=2)), 2)
        self.assertEqual(recall(self.home, ["mechanisms/hand-off"], limit=-1), [])
        same_tier = build_rows("wish-d", 1, playtested_document(), [LEAD], ["mechanisms/hand-off"])
        for row in same_tier:
            row["observed_at"] = "2026-09-01T00:00:00Z"
        append_rows(self.home, same_tier)
        tier = [row["ref"] for row in recall(self.home, ["mechanisms/hand-off"]) if row["weight"] == 3 and len(row["mechanisms"]) == 1]
        self.assertEqual(tier, ["wish-b#r1:loose-fit", "wish-d#r1:loose-fit"])


class WriteBackTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.rows = build_rows("wish-a", 1, playtested_document(), [LEAD, LEAD_B], ["mechanisms/hand-off"])
        self.dismissals = [{"lead": LEAD_B["id"], "nodes": LEAD_B["nodes"], "why": "Competitive game."}]

    def test_nothing_without_a_host_vault(self):
        self.assertEqual(write_back(self.home, self.rows, self.dismissals, product_id="wish-a", round_index=1), {"banked": 0, "queued": 0})
        self.assertEqual(review_queue(self.home), [])

    def test_banks_confirmed_rows_once_and_queues_dismissals_once(self):
        vault = self.home / "vault"
        (vault / "anti-patterns").mkdir(parents=True)
        node = vault / "anti-patterns" / "idle-player.md"
        node.write_text("---\ntype: anti-pattern\nname: Idle Player\n---\n\n## Definition\nx\n\n## Notes\n- existing note\n", encoding="utf-8")
        report = write_back(self.home, self.rows, self.dismissals, product_id="wish-a", round_index=1)
        self.assertEqual(report, {"banked": 1, "queued": 1})
        text = node.read_text(encoding="utf-8")
        self.assertIn("- [wish-a#r1:idle-seat] improve: One seat idles. (fix tried: Add a simultaneous reveal.)", text)
        self.assertEqual(write_back(self.home, self.rows, self.dismissals, product_id="wish-a", round_index=1), {"banked": 0, "queued": 0})
        self.assertEqual(text, node.read_text(encoding="utf-8"))
        queue = review_queue(self.home)
        self.assertEqual(queue, [{"file": "wish-a-r1.md", "dismissals": 1}])
        body = (vault / "_review" / "wish-a-r1.md").read_text(encoding="utf-8")
        self.assertIn("mechanisms/hand-off -> anti-patterns/turtling -> " + LEAD_B["id"] + ": Competitive game.", body)
        # a node without a Notes section gains one; unknown symptoms and links are skipped
        other = vault / "anti-patterns" / "turtling.md"
        other.write_text("---\ntype: anti-pattern\nname: Turtling\n---\n\n## Definition\ny\n", encoding="utf-8")
        rows = [dict(self.rows[0], ref="wish-b#r1:t", symptom="anti-patterns/turtling"),
                dict(self.rows[0], ref="wish-b#r1:u", symptom="mechanisms/hand-off"),
                dict(self.rows[0], ref="wish-b#r1:v", symptom="anti-patterns/missing")]
        (vault / "anti-patterns" / "link.md").symlink_to(node)
        rows.append(dict(self.rows[0], ref="wish-b#r1:w", symptom="anti-patterns/link"))
        self.assertEqual(write_back(self.home, rows, [], product_id="wish-b", round_index=1), {"banked": 1, "queued": 0})
        self.assertIn("## Notes\n- [wish-b#r1:t]", other.read_text(encoding="utf-8"))
        (vault / "_review" / "link.md").symlink_to(vault / "_review" / "wish-a-r1.md")
        self.assertEqual(review_queue(self.home), [{"file": "wish-a-r1.md", "dismissals": 1}])


class HarvestTest(unittest.TestCase):
    def test_rebuilds_from_verified_receipts_and_reports_the_rest(self):
        fixture = NativePlaytestedTest("test_round_trip_covers_blueprint_and_rehashes_evidence")
        fixture.setUp()
        self.addCleanup(fixture.temporary.cleanup)
        playtested = fixture._playtested(verdict="improve", failed="mechanical-check")
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            runs, state = home / "runs", home / "state"
            self.assertEqual(harvest(home, runs, state), {"rows": 0, "products": 0, "unreadable": []})

            def seal(product, checks, *, content=None, gate_only=False):
                gates = state / product / "gates"
                gates.mkdir(parents=True, exist_ok=True)
                relative = "artifacts/playtest/r0001/playtested.json"
                payload = content if content is not None else json.dumps(playtested.to_dict()).encode()
                if not gate_only:
                    target = runs / product / "workspace" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(payload)
                (gates / "0004-playtest.json").write_text(json.dumps({"evidence": {
                    "artifact_path": relative,
                    "artifact_sha256": hashlib.sha256(payload).hexdigest(),
                    "checks": checks}}), encoding="utf-8")

            seal("wish-good", {"round": 1, "mechanisms": ["mechanisms/hand-off"], "vault_leads": []})
            seal("wish-no-round", {"mechanisms": []})
            seal("wish-missing", {"round": 1}, gate_only=True)
            seal("wish-tampered", {"round": 1}, content=b"{}")
            (state / "wish-tampered" / "gates" / "0004-playtest.json").write_text(
                json.dumps({"evidence": {"artifact_path": "artifacts/playtest/r0001/playtested.json",
                                          "artifact_sha256": "0" * 64, "checks": {"round": 1}}}), encoding="utf-8")
            seal("wish-notcontract", {"round": 1}, content=b'{"not": "a contract"}')
            (state / "wish-broken" / "gates").mkdir(parents=True)
            (state / "wish-broken" / "gates" / "0004-playtest.json").write_text("{broken", encoding="utf-8")
            (state / "no-gates").mkdir()
            report = harvest(home, runs, state)
            self.assertEqual(report["rows"], 2)
            self.assertEqual(report["products"], 6)
            self.assertEqual(
                report["unreadable"],
                ["wish-broken/0004-playtest.json", "wish-missing/0004-playtest.json",
                 "wish-notcontract/0004-playtest.json", "wish-tampered/0004-playtest.json"],
            )
            rows = read_ledger(home)
            self.assertEqual({row["product_id"] for row in rows}, {"wish-good", "wish-no-round"})
            self.assertEqual(rows[0]["code"], "fix-mechanical-check")
            self.assertEqual(rows[0]["weight"], 1)
            self.assertEqual(harvest(home, runs, state)["rows"], 2)


if __name__ == "__main__":
    unittest.main()
