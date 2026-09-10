from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from workshop.errors import StateConflict
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome
from workshop.workflow.proposals import AgentOutcomeProposal
from workshop.workflow import native_run as host


def rejection_fixture(stage, *, count=1, effort="spark", transition=None):
    directory = Path("/private/rejections")
    checkpoint = SimpleNamespace(
        product_id="fixture", round_index=1, checkpoint_sha256="a" * 64,
        effort=effort,
        input_sha256s={host.TOKEN_BUDGET_CAPABILITY_PATH: "b" * 64,
                      **({host._PRODUCT_RUN_EFFORT_ROUTES_INPUT: "c" * 64} if effort else {})},
    )
    proposal = AgentOutcomeProposal(
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        subject_sha256="d" * 64,
        outcome=AgentOutcome(
            stage=stage, status="ready",
            artifacts=(AgentArtifact("artifacts/%s/result.json" % stage, "e" * 64),),
            proposed_transition=transition or (
                host._checkpoint_next_stage(checkpoint, "make") if stage == "make" else "release"
            ),
        ),
    )
    proposal_bytes = host._canonical_json_bytes(proposal.to_dict()) + b"\n"
    file_hash = host._sha256(proposal_bytes)
    files = {directory / ("outcome-%s.json" % file_hash): proposal_bytes}
    previous = None
    for number in range(1, count + 1):
        code = stage + "-artifact-invalid"
        identity = {
            "schema_version": 1,
            "kind": getattr(host, "_%s_PROPOSAL_REJECTION_KIND" % stage.upper()),
            "product_id": checkpoint.product_id, "stage": stage, "round": 1,
            "rejection_number": number,
            "checkpoint_sha256": checkpoint.checkpoint_sha256,
            "subject_sha256": proposal.subject_sha256,
            "previous_rejection_sha256": previous,
            "rejected_proposal_sha256": proposal.sha256,
            "rejected_proposal_file_sha256": file_hash,
            "rejected_outcome_sha256": proposal.outcome.sha256,
            "rejected_artifacts": [item.to_dict() for item in proposal.outcome.artifacts],
            "failure_code": code,
            "feedback": getattr(host, "_%s_PROPOSAL_REJECTION_FEEDBACK" % stage.upper())[code],
        }
        record = {**identity, "rejection_sha256": host._sha256(host._canonical_json_bytes(identity))}
        previous = record["rejection_sha256"]
        files[directory / ("rejection-%s.json" % previous)] = host._canonical_json_bytes(record) + b"\n"
    return checkpoint, directory, record, files


@pytest.mark.parametrize("stage", ["make", "playtest"])
def test_more_than_one_thousand_rejections_validate_without_recursion(stage):
    checkpoint, directory, record, files = rejection_fixture(stage, count=1100)
    validator = getattr(host, "_validate_%s_proposal_rejection_record" % stage)
    with mock.patch.object(host, "_read_stable_private_bytes", side_effect=lambda path, **kwargs: files[path]) as reads:
        assert validator(None, checkpoint, record, directory=directory) == record
    assert reads.call_count == 2199  # every quarantine and every predecessor


@pytest.mark.parametrize("stage", ["make", "playtest"])
def test_adopted_host_token_authority_removes_old_rejection_count_cap(stage):
    checkpoint, directory, record, files = rejection_fixture(stage, count=40)
    checkpoint.input_sha256s.pop(host.TOKEN_BUDGET_CAPABILITY_PATH)
    checkpoint.token_budgeted = True
    validator = getattr(host, "_validate_%s_proposal_rejection_record" % stage)
    with mock.patch.object(host, "_read_stable_private_bytes", side_effect=lambda path, **kwargs: files[path]):
        assert validator(None, checkpoint, record, directory=directory) == record
        checkpoint.token_budgeted = False
        with pytest.raises(StateConflict, match="invalid"):
            validator(None, checkpoint, record, directory=directory)


@pytest.mark.parametrize("effort", [None, "spark", "forge", "quest"])
def test_make_rejection_preserves_exact_workflow_transition(effort):
    checkpoint, directory, record, files = rejection_fixture("make", effort=effort)
    with mock.patch.object(host, "_read_stable_private_bytes", side_effect=lambda path, **kwargs: files[path]):
        assert host._validate_make_proposal_rejection_record(None, checkpoint, record, directory=directory) == record


def test_spark_rejection_cannot_claim_skipped_playtest_transition():
    checkpoint, directory, record, files = rejection_fixture("make", transition="playtest")
    with mock.patch.object(host, "_read_stable_private_bytes", side_effect=lambda path, **kwargs: files[path]):
        with pytest.raises(StateConflict, match="disagrees"):
            host._validate_make_proposal_rejection_record(None, checkpoint, record, directory=directory)


@pytest.mark.parametrize("stage", ["make", "playtest"])
def test_rejection_chain_keeps_predecessor_hash_and_cycle_checks(stage):
    checkpoint, directory, record, files = rejection_fixture(stage, count=3)
    validator = getattr(host, "_validate_%s_proposal_rejection_record" % stage)
    with mock.patch.object(host, "_read_stable_private_bytes", side_effect=lambda path, **kwargs: files[path]):
        with pytest.raises(StateConflict, match="cycle"):
            validator(None, checkpoint, record, directory=directory,
                      seen=frozenset({record["previous_rejection_sha256"]}))
        previous_path = directory / ("rejection-%s.json" % record["previous_rejection_sha256"])
        files[previous_path] = host._canonical_json_bytes(record) + b"\n"
        with pytest.raises(StateConflict, match="cycle|predecessor"):
            validator(None, checkpoint, record, directory=directory)
