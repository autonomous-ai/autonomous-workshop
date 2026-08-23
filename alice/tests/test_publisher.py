import json
import tempfile
import unittest
from pathlib import Path

from alice.publisher import PublicationError, PublicationPacket, Publisher


def packet() -> PublicationPacket:
    return PublicationPacket(
        candidate_id="game-1",
        slug="river-council",
        version=1,
        title="River Council",
        one_line="Negotiate a river without owning it.",
        rules={"setup": "s", "turn": "t", "end": "e", "scoring": "p", "ties": "x"},
        components=({"kind": "tile", "count": 20},),
        evidence_summary={"blind_groups": 3},
        manufacturing={"print_yield": 0.98},
        price={"currency": "USD", "amount": 29},
    )


class PublisherTests(unittest.TestCase):
    def test_dry_run_is_immutable_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            publisher = Publisher(directory)
            first = publisher.publish(packet())
            second = publisher.publish(packet())
            self.assertEqual(first.packet_hash, second.packet_hash)
            self.assertEqual(first.status, "prepared")
            files = list(Path(directory).rglob("publication.json"))
            self.assertEqual(len(files), 1)

    def test_live_requires_explicit_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                Publisher(directory, mode="live")
            with self.assertRaises(ValueError):
                Publisher(directory, mode="live", command=["publisher"])

    def test_incomplete_rules_are_rejected(self) -> None:
        broken = packet()
        object.__setattr__(broken, "rules", {"setup": "s"})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PublicationError):
                Publisher(directory).publish(broken)


if __name__ == "__main__":
    unittest.main()
