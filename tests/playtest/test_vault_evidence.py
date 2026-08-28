"""Playtest evidence rows and their game-vault write-back shapes."""

from __future__ import annotations

import unittest

from workshop.errors import ContractError
from workshop.playtest.vault_evidence import (
    build_rows,
    gamevault_dismissals,
    gamevault_rows,
    provenance_weight,
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


class VaultRowsTest(unittest.TestCase):
    def test_confirmed_rows_become_vault_evidence(self):
        rows = build_rows("wish-a", 1, playtested_document(), [LEAD, LEAD_B], ["mechanisms/hand-off"])
        posted = gamevault_rows(rows)
        self.assertEqual(
            posted,
            [
                {
                    "slug": "wish-a",
                    "id": "r0001-idle-seat",
                    "symptom": "anti-patterns/idle-player",
                    "claim": "One seat idles.",
                    "fix_tried": "Add a simultaneous reveal.",
                    "severity": "medium",
                    "survived_rounds": 1,
                    "source": "workshop-playtest",
                    "round": 1,
                }
            ],
        )
        blocking = gamevault_rows([dict(rows[0], severity="block", finding="  Two   seats\nidle ")])
        self.assertEqual((blocking[0]["severity"], blocking[0]["claim"]), ("high", "Two seats idle"))
        self.assertEqual(gamevault_rows([dict(rows[0], symptom="mechanisms/hand-off")]), [])
        self.assertEqual(gamevault_rows(build_rows("wish-a", 1, playtested_document(confirm=False), [LEAD], [])), [])

    def test_dismissed_leads_become_review_rows(self):
        dismissals = [
            {"lead": LEAD_B["id"], "nodes": LEAD_B["nodes"], "why": "  Competitive\n game. "},
            {"lead": "c" * 16, "nodes": ["only-one"], "why": "malformed lead"},
            {"lead": "d" * 16, "nodes": LEAD["nodes"]},
        ]
        self.assertEqual(
            gamevault_dismissals(dismissals, product_id="wish-a", round_index=2),
            [
                {"slug": "wish-a", "id": "r0002-" + LEAD_B["id"], "symptom": "anti-patterns/turtling", "why": "Competitive game."},
                {"slug": "wish-a", "id": "r0002-" + "d" * 16, "symptom": "anti-patterns/idle-player", "why": "no reason given"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
