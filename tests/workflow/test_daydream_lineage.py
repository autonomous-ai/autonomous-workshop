import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import StateConflict
from workshop.workflow.agent_run import AgentArtifact, AgentRunCheckpoint
from workshop.workflow.native_run import (
    NativeRunPaths,
    _native_lineage,
    canonical_wish_bytes,
)
from workshop.wish import Wish


def _json_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


class DaydreamReceiptLineageTest(unittest.TestCase):
    def test_projects_only_current_hash_verified_contract_identities(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            state = root / "state"
            workspace.mkdir()
            state.mkdir()
            wish = Wish.create(
                "wish-lineage",
                "Build the exact Dream.",
                context={
                    "source": "workshop-daydream",
                    "inventor_id": "sample",
                    "daydream_id": "daydream-20260903-080000-00000001",
                    "idea_sha256": "a" * 64,
                    "daydream_sha256": "b" * 64,
                    "provenance_sha256": "c" * 64,
                    "route": "forge",
                },
            )
            (workspace / "WISH.json").write_bytes(canonical_wish_bytes(wish))
            documents = {
                "artifacts/invent/invented.json": {
                    "wish_sha256": hashlib.sha256(canonical_wish_bytes(wish)).hexdigest(),
                    "concept_sha256": "1" * 64,
                    "invented_sha256": "2" * 64,
                },
                "artifacts/make/r0001/made.json": {
                    "wish_sha256": hashlib.sha256(canonical_wish_bytes(wish)).hexdigest(),
                    "invented_sha256": "2" * 64,
                    "made_sha256": "3" * 64,
                    "product_artifact_sha256": "4" * 64,
                },
                "artifacts/release/release.json": {
                    "release_sha256": "5" * 64,
                    "made_sha256": "3" * 64,
                    "playtested_sha256": "9" * 64,
                    "product_artifact_sha256": "4" * 64,
                },
            }
            bindings = {}
            for relative, document in documents.items():
                path = workspace / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                content = _json_bytes(document)
                path.write_bytes(content)
                stage = relative.split("/")[1]
                bindings.setdefault(stage, []).append(
                    AgentArtifact(relative, hashlib.sha256(content).hexdigest())
                )
            checkpoint = AgentRunCheckpoint(
                product_id="wish-lineage",
                stage="release",
                status="complete",
                revision=4,
                round_index=1,
                max_rounds=4,
                wish_sha256=hashlib.sha256(canonical_wish_bytes(wish)).hexdigest(),
                run_root_sha256="6" * 64,
                host_state_root_sha256="7" * 64,
                checkpoint_sha256="8" * 64,
                input_sha256s={},
                inventor_roster=(),
                stage_artifacts={key: tuple(value) for key, value in bindings.items()},
                invalidated_stages=(),
                effort="forge",
            )
            lineage = _native_lineage(
                NativeRunPaths(workspace=workspace, host_state=state), checkpoint
            )
            self.assertEqual(lineage["origin"]["daydream_sha256"], "b" * 64)
            self.assertEqual(lineage["invented"]["concept_sha256"], "1" * 64)
            self.assertEqual(lineage["made"]["made_sha256"], "3" * 64)
            self.assertEqual(lineage["release"]["release_sha256"], "5" * 64)
            self.assertEqual(
                lineage["release"]["contract_sha256"],
                bindings["release"][0].sha256,
            )
            (workspace / "artifacts/make/r0001/made.json").write_bytes(b"{}")
            with self.assertRaisesRegex(StateConflict, "changed"):
                _native_lineage(
                    NativeRunPaths(workspace=workspace, host_state=state), checkpoint
                )

    def test_made_contract_may_leave_product_artifact_unbound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            state = root / "state"
            workspace.mkdir()
            state.mkdir()
            wish = Wish.create("wish-spark", "Build the exact Dream.")
            (workspace / "WISH.json").write_bytes(canonical_wish_bytes(wish))
            wish_sha256 = hashlib.sha256(canonical_wish_bytes(wish)).hexdigest()
            made = {
                "wish_sha256": wish_sha256,
                "invented_sha256": "2" * 64,
                "made_sha256": "3" * 64,
                "product_artifact_sha256": None,
            }
            relative = "artifacts/make/r0001/made.json"
            path = workspace / relative
            path.parent.mkdir(parents=True)
            content = _json_bytes(made)
            path.write_bytes(content)
            checkpoint = AgentRunCheckpoint(
                product_id="wish-spark",
                stage="make",
                status="complete",
                revision=1,
                round_index=1,
                max_rounds=4,
                wish_sha256=wish_sha256,
                run_root_sha256="6" * 64,
                host_state_root_sha256="7" * 64,
                checkpoint_sha256="8" * 64,
                input_sha256s={},
                inventor_roster=(),
                stage_artifacts={
                    "make": (AgentArtifact(relative, hashlib.sha256(content).hexdigest()),)
                },
                invalidated_stages=(),
                effort="spark",
            )
            lineage = _native_lineage(
                NativeRunPaths(workspace=workspace, host_state=state), checkpoint
            )
            self.assertIsNone(lineage["origin"])
            self.assertEqual(lineage["made"]["made_sha256"], "3" * 64)
            self.assertIsNone(lineage["made"]["product_artifact_sha256"])
            made["made_sha256"] = None
            path.write_bytes(_json_bytes(made))
            checkpoint = AgentRunCheckpoint(
                **{
                    **checkpoint.__dict__,
                    "stage_artifacts": {
                        "make": (
                            AgentArtifact(
                                relative, hashlib.sha256(_json_bytes(made)).hexdigest()
                            ),
                        )
                    },
                }
            )
            with self.assertRaisesRegex(StateConflict, "malformed"):
                _native_lineage(
                    NativeRunPaths(workspace=workspace, host_state=state), checkpoint
                )


if __name__ == "__main__":
    unittest.main()
