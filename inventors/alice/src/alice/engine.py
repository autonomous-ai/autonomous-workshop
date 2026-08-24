"""Restartable scheduler and one-task-at-a-time Alice worker."""

from __future__ import annotations

import hashlib
import json
import re
import socket
import threading
import time
import uuid
from dataclasses import asdict
from typing import Any, Mapping

from inventor_workshop import Taste, load_taste

from .adapters import AdapterError, CommandAdapter, adapter_input_sha256
from .config import DATA_ROOT
from .domain import TERMINAL_STATES, WorkItem
from .fulfillment import (
    FulfillmentValidationError,
    build_fulfillment_intents,
    fulfillment_intent_from_payload,
    print_job_receipt_from_payload,
    validate_print_job_receipts,
    validate_qa_ship_receipts,
)
from .loops import (
    LEGACY_TASK_KIND_ALIASES,
    LOOPS,
    OUTPUT_CONTRACTS,
    PACK_PRODUCT,
    SEND_TO_SHOP,
    SEND_VERIFY_SHOP,
    canonical_task_kind,
    validate_output_semantics,
    work_for_state,
)
from .page_builder import PageBuilderError, validate_printable_artifact_hashes
from .learning import ContextualThompsonBandit
from .policy import next_progress_state, release_policy_from_config
from .providers import AgentProvider, AgentRequest, ProviderError
from .release import (
    ArtifactSnapshot,
    ReleaseAssemblyError,
    artifact_manifest,
    assess_release,
    build_publication_packet,
    validate_blind_human_evidence,
    validate_blind_kit,
    validate_distinct_manufacturing_receipts,
    validate_manufacturing_receipt,
    validate_production_manifest,
)
from .roles import ROLE_CARDS
from .store import DurableStore, LeaseLostError, StateConflictError, TaskRecord
from .transitions import TransitionEvidence, advance_with_evidence


class EngineError(RuntimeError):
    pass


_EFFECT_RECONCILE_OPERATIONS = {
    "physical.cad": "physical.reconcile_cad",
    "physical.prototype_print": "physical.reconcile_prototype_print",
    "physical.production_run": "physical.reconcile_production_run",
    "orders.create_print_job": "orders.reconcile_print_job",
    "orders.qa_ship": "orders.reconcile_qa_ship",
}

_CANDIDATE_PHYSICAL_EFFECT_STATES = {
    "physical.cad": "human_validated",
    "physical.prototype_print": "physical_ready",
    "physical.production_run": "physical_ready",
}

# Input-only compatibility for older deployment dictionaries. ``self.adapters``
# contains only the current keys after construction.
_LEGACY_ADAPTER_KEYS = {
    "publishing_pipeline": "shop_door",
    "factory_order": "delivery",
}


class AliceEngine:
    def __init__(
        self,
        store: DurableStore,
        provider: AgentProvider,
        config: Mapping[str, Any],
        *,
        worker_id: str | None = None,
        adapters: Mapping[str, Any] | None = None,
        taste: Taste | None = None,
    ) -> None:
        self.store = store
        self.provider = provider
        self.config = config
        self.worker_id = worker_id or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        self.adapters = _canonical_adapter_map(adapters or {})
        self.taste = taste or load_taste(DATA_ROOT)
        self.release_policy = release_policy_from_config(config)

    def schedule(self, *, now: float | None = None) -> int:
        """Seed current cadence buckets, resume incomplete graphs, and route candidates."""

        at = time.time() if now is None else float(now)
        before = self.store.task_counts()["queued"]
        active_count = len(
            [
                candidate
                for candidate in self.store.list_candidates(limit=1_000)
                if candidate.state not in TERMINAL_STATES
            ]
        )
        max_active = int(self.config["runtime"]["max_active_candidates"])
        for spec in LOOPS.values():
            if spec.name == "orders":
                if not self._effect_mode_allows("orders.poll_paid"):
                    continue
                if "order_to_print_job" not in set(self._shop_capabilities()):
                    # Missing commerce credentials are a deployment preflight
                    # condition, not 288 failed polling tasks per day.
                    continue
            if spec.name == "invention" and active_count >= max_active:
                continue
            bucket = int(at // spec.cadence_seconds)
            run_id = f"loop:{spec.name}:{bucket}"
            self._schedule_graph(spec.name, run_id, now=at)

        # A task is not considered fully applied until its artifacts, derived
        # facts, transitions, and graph successors are durable.  This query has
        # no historical window, so years of old rows cannot hide new recovery.
        for task in self.store.list_unapplied_succeeded_tasks():
            try:
                self._record_result(task)
            except (EngineError, ValueError, TypeError, KeyError) as exc:
                self._quarantine_result(task, exc)

        # A final lease expiry can fail a task without returning through this
        # process's exception handler.  Preserve the outward-effect uncertainty
        # explicitly instead of leaving a durable `sending` claim that looks
        # recoverable forever.
        for task in self.store.list_tasks(state="failed", limit=1_000):
            if task.kind in _EFFECT_RECONCILE_OPERATIONS:
                self._mark_irreversible_task_effect_ambiguous(
                    task, "task exhausted its attempts before reconciliation"
                )

        for candidate in self.store.list_candidates(limit=1_000):
            if candidate.state in TERMINAL_STATES:
                continue
            self._schedule_candidate(candidate.id, now=at)
        after = self.store.task_counts()["queued"]
        return max(0, after - before)

    def _schedule_graph(self, loop_name: str, run_id: str, *, now: float) -> None:
        spec = LOOPS[loop_name]
        tasks = _tasks_by_current_kind(
            self.store.list_tasks(run_id=run_id, limit=100)
        )
        for item in spec.work:
            if item.action in tasks:
                continue
            if not self._effect_mode_allows(item.action):
                continue
            dependencies = {name: tasks.get(name) for name in item.depends_on}
            if any(task is None or task.state != "succeeded" for task in dependencies.values()):
                continue
            if any(
                self._task_is_quarantined(task.id)
                for task in dependencies.values()
                if task is not None
            ):
                continue
            dependency_results = {
                name: {
                    "output_sha256": task.output_sha256,
                    "result": task.result,
                }
                for name, task in dependencies.items()
                if task is not None
            }
            task = self._enqueue_work(
                item,
                run_id=run_id,
                idempotency_key=f"{run_id}:{item.action}",
                dependency_results=dependency_results,
                now=now,
            )
            tasks[item.action] = task

    def _schedule_candidate(self, candidate_id: str, *, now: float) -> None:
        candidate = self.store.get_candidate(candidate_id)
        if candidate.state in TERMINAL_STATES:
            return
        run_id = f"candidate:{candidate.id}:v{candidate.version}"
        tasks = _tasks_by_current_kind(
            self.store.list_tasks(run_id=run_id, limit=100)
        )
        for item in work_for_state(candidate.state, candidate.id):
            if item.action in tasks:
                continue
            if not self._effect_mode_allows(item.action):
                continue
            dependencies = {name: tasks.get(name) for name in item.depends_on}
            if any(
                dependency is None or dependency.state != "succeeded"
                for dependency in dependencies.values()
            ):
                continue
            if any(
                self._task_is_quarantined(dependency.id)
                for dependency in dependencies.values()
                if dependency is not None
            ):
                continue
            # A completed task result and its accepted candidate artifact are
            # separate durable writes.  Do not let a child (especially the
            # release gate) run in the crash window between those writes.
            if any(
                self.store.get_candidate_artifact_for_task(dependency.id) is None
                for dependency in dependencies.values()
                if dependency is not None
            ):
                continue
            dependency_results = {
                name: {
                    "output_sha256": dependency.output_sha256,
                    "result": dependency.result,
                }
                for name, dependency in dependencies.items()
                if dependency is not None
            }
            task = self._enqueue_work(
                item,
                run_id=run_id,
                idempotency_key=(
                    f"candidate:{candidate.id}:v{candidate.version}:{item.action}"
                ),
                dependency_results=dependency_results,
                now=now,
            )
            tasks[item.action] = task

    def _enqueue_work(
        self,
        item: WorkItem,
        *,
        run_id: str,
        idempotency_key: str,
        dependency_results: Mapping[str, Any],
        now: float,
    ) -> TaskRecord:
        payload: dict[str, Any] = {
            "loop": item.loop,
            "action": item.action,
            "role": item.role,
            "objective": item.objective,
            "depends_on": list(item.depends_on),
            "dependencies": dict(dependency_results),
            "work_payload": dict(item.payload or {}),
        }
        if item.loop == "library":
            payload["library_manifest"] = self.config.get("knowledge", {}).get(
                "library", {}
            )
        if item.loop in {"invention", "market"}:
            payload["market_signals"] = self.config.get("knowledge", {}).get(
                "market_signals", {}
            )
        if item.candidate_id:
            candidate = self.store.get_candidate(item.candidate_id)
            payload["candidate_id"] = candidate.id
            payload["candidate_version"] = candidate.version
            payload["candidate"] = candidate.content
            payload["candidate_content_sha256"] = _canonical_sha256(
                candidate.content
            )
            payload["candidate_metadata"] = dict(candidate.metadata)
            payload["accepted_artifacts"] = self._accepted_artifacts_payload(
                candidate.id,
                candidate.metadata,
            )
        return self.store.enqueue_task(
            item.action,
            payload,
            idempotency_key=idempotency_key,
            run_id=run_id,
            candidate_id=item.candidate_id,
            priority=_priority(item),
            max_attempts=int(self.config["runtime"]["max_attempts"]),
            now=now,
        )

    def work_once(self, *, now: float | None = None) -> TaskRecord | None:
        deterministic_clock = now is not None
        at = time.time() if now is None else float(now)
        self.schedule(now=at)
        lease_seconds = float(self.config["runtime"]["lease_seconds"])
        task = self.store.lease_task(
            self.worker_id,
            lease_seconds=lease_seconds,
            now=at,
        )
        if task is None:
            return None
        assert task.lease_token is not None
        try:
            result = self._execute_with_heartbeat(
                task,
                lease_seconds=lease_seconds,
                enabled=not deterministic_clock,
            )
        except (ProviderError, AdapterError, TimeoutError) as exc:
            error_message = _durable_error_message(exc)
            if (
                task.kind in _EFFECT_RECONCILE_OPERATIONS
                and task.attempt_count >= task.max_attempts
            ):
                self._mark_irreversible_task_effect_ambiguous(task, error_message)
            failure_at = self._renew_before_finalize(
                task,
                lease_seconds=lease_seconds,
                deterministic_at=at + 0.001 if deterministic_clock else None,
            )
            return self.store.fail_task(
                task.id,
                self.worker_id,
                task.lease_token,
                stage=task.kind,
                error_code=type(exc).__name__,
                error_message=error_message,
                # Once an effect has a durable `sending` claim, every later
                # attempt uses its read-by-operation-key reconciliation
                # operation.  It never blindly repeats the original write.
                retryable=True,
                retry_delay=_retry_delay(task.attempt_count),
                now=failure_at,
            )
        except LeaseLostError:
            # Another worker may now own the task. Fencing must remain loud: do
            # not mutate the task or pretend the abandoned attempt failed.
            raise
        except Exception as exc:
            error_message = _durable_error_message(exc)
            if task.kind in _EFFECT_RECONCILE_OPERATIONS:
                self._mark_irreversible_task_effect_ambiguous(task, error_message)
            failure_at = self._renew_before_finalize(
                task,
                lease_seconds=lease_seconds,
                deterministic_at=at + 0.001 if deterministic_clock else None,
            )
            return self.store.fail_task(
                task.id,
                self.worker_id,
                task.lease_token,
                stage=task.kind,
                error_code=type(exc).__name__,
                error_message=error_message,
                retryable=False,
                now=failure_at,
            )

        completion_at = self._renew_before_finalize(
            task,
            lease_seconds=lease_seconds,
            deterministic_at=at + 0.001 if deterministic_clock else None,
        )
        completed = self.store.complete_task(
            task.id,
            self.worker_id,
            task.lease_token,
            result,
            now=completion_at,
        )
        # Recording derived facts happens only after the task result is durable.
        # If this step crashes, schedule() can reconstruct graph successors from
        # the committed task rather than trying to fail an already-finished one.
        try:
            self._record_result(completed)
        except (EngineError, ValueError, TypeError, KeyError) as exc:
            self._quarantine_result(completed, exc)
        return completed

    def _execute_with_heartbeat(
        self,
        task: TaskRecord,
        *,
        lease_seconds: float,
        enabled: bool,
    ) -> dict[str, Any]:
        if not enabled:
            return self._execute(task)
        assert task.lease_token is not None
        heartbeat = _LeaseHeartbeat(
            self.store,
            task.id,
            self.worker_id,
            task.lease_token,
            lease_seconds,
        )
        heartbeat.start()
        execution_error: Exception | None = None
        result: dict[str, Any] | None = None
        try:
            result = self._execute(task)
        except Exception as exc:
            execution_error = exc
        finally:
            heartbeat.stop()
        heartbeat.raise_if_failed()
        if execution_error is not None:
            raise execution_error
        assert result is not None
        return result

    def _renew_before_finalize(
        self,
        task: TaskRecord,
        *,
        lease_seconds: float,
        deterministic_at: float | None,
    ) -> float:
        if deterministic_at is not None:
            return deterministic_at
        assert task.lease_token is not None
        at = time.time()
        self.store.renew_task_lease(
            task.id,
            self.worker_id,
            task.lease_token,
            lease_seconds=lease_seconds,
            now=at,
        )
        return time.time()

    def _execute(self, task: TaskRecord) -> dict[str, Any]:
        self._validate_task_fence(task)
        self._enforce_effect_mode(task.kind)
        current_kind = canonical_task_kind(task.kind)
        if current_kind == "release.evaluate":
            content = self._evaluate_release(task)
            _validate_required(content, OUTPUT_CONTRACTS[current_kind])
            return {"executor": "release_policy", "content": content}
        if current_kind == PACK_PRODUCT:
            self._require_current_live_capabilities()
            content = self._build_publication_packet(task)
            _validate_required(content, OUTPUT_CONTRACTS[current_kind])
            return {"executor": "release_policy", "content": content}
        if current_kind == "candidate.choose_mutation":
            content = self._choose_mutation(task)
            _validate_required(content, OUTPUT_CONTRACTS[current_kind])
            return {"executor": "learning_policy", "content": content}
        if current_kind == "policy.shadow":
            content = self._update_learning_policy(task)
            _validate_required(content, OUTPUT_CONTRACTS[current_kind])
            return {"executor": "learning_policy", "content": content}
        adapter = self._adapter_for(task.kind)
        required_adapter = _required_adapter_name(task.kind)
        if required_adapter is not None and adapter is None:
            raise EngineError(
                f"{task.kind} requires configured {required_adapter!r} adapter; "
                "a model response cannot stand in for an external effect or receipt"
            )
        if adapter is not None:
            if current_kind == SEND_TO_SHOP:
                self._require_current_live_capabilities()
            adapter_operation = task.kind
            adapter_payload = dict(task.payload)
            if task.kind in _EFFECT_RECONCILE_OPERATIONS:
                (
                    adapter_operation,
                    adapter_payload,
                    cached_result,
                ) = self._prepare_irreversible_task_effect(task)
                if cached_result is not None:
                    self._validate_fulfillment_result(task, cached_result)
                    return cached_result
            receipt = adapter.invoke(adapter_operation, adapter_payload)
            expected_input_sha256 = adapter_input_sha256(
                adapter_operation, adapter_payload
            )
            if receipt.input_sha256 != expected_input_sha256:
                raise EngineError(
                    f"{task.kind} adapter receipt is bound to a different input"
                )
            expected_evidence_class = _required_evidence_class(task.kind)
            if (
                expected_evidence_class is not None
                and receipt.evidence_class != expected_evidence_class
            ):
                raise EngineError(
                    f"{task.kind} adapter returned evidence class "
                    f"{receipt.evidence_class!r}; expected "
                    f"{expected_evidence_class!r}"
                )
            _reject_sensitive_adapter_payload(receipt.payload)
            contract = OUTPUT_CONTRACTS.get(task.kind, {})
            _validate_required(receipt.payload, contract)
            _validate_adapter_payload_shape(task.kind, receipt.payload, contract)
            _validate_action_semantics(task.kind, receipt.payload)
            _validate_task_lineage(task, receipt.payload)
            durable_result = {
                "executor": "adapter",
                "role": task.payload["role"],
                "receipt": asdict(receipt),
            }
            self._validate_fulfillment_result(task, durable_result)
            if task.kind in _EFFECT_RECONCILE_OPERATIONS:
                return self._confirm_irreversible_task_effect(task, durable_result)
            return durable_result

        role_name = str(task.payload["role"])
        role = ROLE_CARDS.get(role_name)
        if role is None:
            raise EngineError(f"unknown role {role_name!r}")
        self.taste.assert_current()
        request = AgentRequest(
            request_id=f"{task.id}:{task.lease_attempt_id}",
            role=role_name,
            objective=str(task.payload["objective"]),
            context={
                "mandate": role.mandate,
                "forbidden": list(role.forbidden),
                "action": task.kind,
                "candidate": task.payload.get("candidate"),
                "candidate_content_sha256": task.payload.get(
                    "candidate_content_sha256"
                ),
                "accepted_artifacts": task.payload.get("accepted_artifacts", []),
                "dependencies": task.payload.get("dependencies", {}),
                "library_manifest": task.payload.get("library_manifest"),
                "market_signals": task.payload.get("market_signals"),
                "recent_knowledge": self._recent_knowledge(task),
                "taste": self.taste.to_binding(),
                "work_payload": task.payload.get("work_payload", {}),
                "evidence_rule": (
                    "Identify every surrogate. Never label model or fixture output as "
                    "human, manufacturing, or market evidence."
                ),
            },
            output_contract=OUTPUT_CONTRACTS.get(task.kind, {}),
        )
        response = self.provider.run(request)
        self.taste.assert_current()
        response_content = _bind_agent_lineage(task, response.content)
        _validate_required(response_content, OUTPUT_CONTRACTS.get(task.kind, {}))
        _validate_action_semantics(task.kind, response_content)
        _validate_task_lineage(task, response_content)
        if task.kind == "concept.select":
            candidate = response_content.get("candidate")
            if not isinstance(candidate, Mapping):
                raise EngineError("concept.select must return one candidate object")
            _validate_3d_game_candidate(candidate)
        response_payload = asdict(response)
        response_payload["content"] = response_content
        return {
            "executor": "agent",
            "role": role_name,
            "response": response_payload,
        }

    def _validate_task_fence(self, task: TaskRecord) -> None:
        """Reject work captured from an older candidate state before dispatch.

        Candidate tasks are immutable snapshots.  Rework, blocking, killing, or
        editing a candidate increments its version, so an already queued print
        or publish task must never be allowed to act on the newer candidate.
        """

        if task.candidate_id is None:
            return
        candidate = self.store.get_candidate(task.candidate_id)
        payload_candidate_id = task.payload.get("candidate_id")
        payload_version = task.payload.get("candidate_version")
        if payload_candidate_id != candidate.id:
            raise EngineError("candidate task id does not match its durable candidate")
        if (
            isinstance(payload_version, bool)
            or not isinstance(payload_version, int)
            or payload_version != candidate.version
        ):
            raise EngineError(
                f"stale candidate task v{payload_version!r}; "
                f"current candidate is v{candidate.version}"
            )
        allowed_actions = {
            item.action for item in work_for_state(candidate.state, candidate.id)
        }
        if canonical_task_kind(task.kind) not in allowed_actions:
            raise EngineError(
                f"stale candidate task {task.kind!r}; "
                f"candidate is now {candidate.state!r}"
            )
        expected_content_hash = task.payload.get("candidate_content_sha256")
        if expected_content_hash is not None and expected_content_hash != _canonical_sha256(
            candidate.content
        ):
            raise EngineError("candidate content changed after task capture")

    def _enforce_effect_mode(self, action: str) -> None:
        mode = str(self.config["runtime"]["effect_mode"])
        required = _required_effect_mode(action)
        if not self._effect_mode_allows(action):
            raise EngineError(
                f"{action} requires effect mode {required!r}; current mode is {mode!r}"
            )

    def _effect_mode_allows(self, action: str) -> bool:
        required = _required_effect_mode(action)
        if required is None:
            return True
        mode = str(self.config["runtime"]["effect_mode"])
        rank = {"dry-run": 0, "draft": 1, "live": 2}
        if mode not in rank:
            raise EngineError(f"unknown runtime effect mode {mode!r}")
        return rank[mode] >= rank[required]

    def _artifact_snapshots(
        self,
        candidate_id: str,
        *,
        task_ids: set[str] | None = None,
    ) -> list[ArtifactSnapshot]:
        snapshots: list[ArtifactSnapshot] = []
        for artifact in self.store.list_candidate_artifacts(
            candidate_id=candidate_id,
            limit=1_000,
        ):
            if task_ids is not None and artifact.task_id not in task_ids:
                continue
            task = self.store.get_task(artifact.task_id)
            content, executor, evidence_class = _result_content_provenance(task.result)
            if self.store.sha256_json(content) != artifact.content_sha256:
                raise EngineError(
                    f"candidate artifact {artifact.id!r} content no longer matches its task"
                )
            snapshots.append(
                ArtifactSnapshot(
                    action=artifact.action,
                    task_id=artifact.task_id,
                    candidate_version=artifact.candidate_version,
                    output_sha256=artifact.output_sha256,
                    content_sha256=artifact.content_sha256,
                    executor=executor,
                    evidence_class=evidence_class,
                    content=content,
                )
            )
        return snapshots

    def _accepted_artifacts_payload(
        self,
        candidate_id: str,
        metadata: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        task_ids: set[str] = set()
        manifests = metadata.get("accepted_manifests", [])
        if isinstance(manifests, list):
            for accepted in manifests:
                entries = accepted.get("artifacts") if isinstance(accepted, Mapping) else None
                if isinstance(entries, list):
                    for entry in entries:
                        task_id = entry.get("task_id") if isinstance(entry, Mapping) else None
                        if isinstance(task_id, str) and task_id:
                            task_ids.add(task_id)
        payload: list[dict[str, Any]] = []
        for artifact in self.store.list_candidate_artifacts(
            candidate_id=candidate_id,
            limit=1_000,
        ):
            if artifact.task_id not in task_ids:
                continue
            task = self.store.get_task(artifact.task_id)
            content, executor, evidence_class = _result_content_provenance(task.result)
            payload.append(
                {
                    "action": artifact.action,
                    "task_id": artifact.task_id,
                    "candidate_version": artifact.candidate_version,
                    "output_sha256": artifact.output_sha256,
                    "content_sha256": artifact.content_sha256,
                    "executor": executor,
                    "evidence_class": evidence_class,
                    "content": content,
                }
            )
        payload.sort(
            key=lambda item: (
                item["candidate_version"],
                item["action"],
                item["task_id"],
            )
        )
        return payload

    def _evaluate_release(self, task: TaskRecord) -> dict[str, Any]:
        if task.candidate_id is None:
            raise EngineError("release.evaluate is not bound to a candidate")
        candidate = self.store.get_candidate(task.candidate_id)
        task_ids: set[str] = set()
        for accepted in candidate.metadata.get("accepted_manifests", []):
            entries = accepted.get("artifacts") if isinstance(accepted, Mapping) else None
            if isinstance(entries, list):
                for entry in entries:
                    artifact_task_id = (
                        entry.get("task_id") if isinstance(entry, Mapping) else None
                    )
                    if isinstance(artifact_task_id, str):
                        task_ids.add(artifact_task_id)
        current_run_id = f"candidate:{candidate.id}:v{candidate.version}"
        for current_task in self.store.list_tasks(run_id=current_run_id, limit=1_000):
            if current_task.kind == "release.evaluate":
                continue
            if current_task.state == "succeeded":
                task_ids.add(current_task.id)
        snapshots = self._artifact_snapshots(task.candidate_id, task_ids=task_ids)
        for artifact in snapshots:
            reward_evidence = artifact.content.get("reward_evidence")
            if not isinstance(reward_evidence, list):
                continue
            for evidence in reward_evidence:
                if isinstance(evidence, Mapping):
                    event_id = evidence.get("event_id") or evidence.get("evidence_id")
                    if isinstance(event_id, str):
                        self._reject_ineligible_market_signal(event_id, "release")
        try:
            decision = assess_release(
                snapshots,
                effect_mode=str(self.config["runtime"]["effect_mode"]),
                factory_capabilities=self._shop_capabilities(),
                policy=self.release_policy,
            )
        except ReleaseAssemblyError as exc:
            raise EngineError(f"release evidence assembly failed: {exc}") from exc
        decision["candidate_id"] = task.candidate_id
        decision["candidate_version"] = task.payload["candidate_version"]
        decision["target_state"] = "publish_ready"
        return decision

    def _build_publication_packet(self, task: TaskRecord) -> dict[str, Any]:
        if task.candidate_id is None:
            raise EngineError("pack.product is not bound to a candidate")
        candidate = self.store.get_candidate(task.candidate_id)
        decision = candidate.metadata.get("release_decision")
        if not isinstance(decision, Mapping):
            raise EngineError("candidate has no pinned release decision")
        if decision.get("candidate_id") != candidate.id:
            raise EngineError("pinned release decision candidate mismatch")
        if decision.get("candidate_version") != candidate.version - 1:
            raise EngineError("pinned release decision version mismatch")
        try:
            return build_publication_packet(
                candidate_id=candidate.id,
                candidate_version=candidate.version,
                candidate_content_sha256=_canonical_sha256(candidate.content),
                release_decision=decision,
            )
        except ReleaseAssemblyError as exc:
            raise EngineError(f"publication packet assembly failed: {exc}") from exc

    def _shop_capabilities(self) -> tuple[str, ...]:
        capabilities: set[str] = set()
        sender = self.adapters.get("shop_door")
        capability_reader = (
            getattr(sender, "release_capabilities", None) if sender else None
        )
        try:
            declared = capability_reader() if callable(capability_reader) else ()
        except Exception:
            # A capability read is safe, but uncertainty cannot be converted
            # into release authority.
            declared = ()
        if isinstance(declared, (tuple, list, set, frozenset)) and all(
            isinstance(item, str) for item in declared
        ):
            capabilities.update(declared)

        order_capabilities = self._adapter_diagnostic_capabilities("delivery")
        fulfillment_capabilities = self._adapter_diagnostic_capabilities(
            "print_fulfillment"
        )
        if (
            {"paid_order_readback"}.issubset(order_capabilities)
            and {
                "authenticated_manufacturing_readback",
                "idempotent_print_by_operation_key",
                "reconcile_print_by_operation_key",
                "reconcile_qa_ship_by_operation_key",
            }.issubset(fulfillment_capabilities)
        ):
            capabilities.add("order_to_print_job")
        return tuple(sorted(capabilities))

    def _adapter_diagnostic_capabilities(self, name: str) -> set[str]:
        adapter = self.adapters.get(name)
        diagnostic_reader = (
            getattr(adapter, "diagnostics", None) if adapter is not None else None
        )
        if not callable(diagnostic_reader):
            return set()
        try:
            diagnostic = diagnostic_reader()
        except Exception:
            return set()
        if (
            not isinstance(diagnostic, Mapping)
            or diagnostic.get("ready") is not True
            or diagnostic.get("authenticated") is not True
            or not isinstance(diagnostic.get("contract_version"), str)
            or not diagnostic.get("contract_version")
        ):
            return set()
        declared = diagnostic.get("capabilities")
        if not isinstance(declared, (tuple, list, set, frozenset)) or any(
            not isinstance(item, str) or not item.strip() for item in declared
        ):
            return set()
        return set(declared)

    def shop_capabilities(self) -> tuple[str, ...]:
        """Return currently observed Shop and Delivery capabilities."""

        return self._shop_capabilities()

    def factory_capabilities(self) -> tuple[str, ...]:
        """Compatibility alias for callers predating Workshop vocabulary."""

        return self.shop_capabilities()

    def _require_current_live_capabilities(self) -> None:
        required = set(self.release_policy.config.required_factory_capabilities)
        current = set(self._shop_capabilities())
        missing = sorted(required - current)
        if missing:
            raise EngineError(
                "live factory capabilities disappeared before publication: "
                + ", ".join(missing)
            )

    def _new_learning_policy(self) -> ContextualThompsonBandit:
        learning = self.config["learning"]
        return ContextualThompsonBandit(
            learning["actions"],
            seed=int(learning["seed"]),
            exploration_probability=float(learning["exploration_probability"]),
            control_action=(
                "simplify_rules"
                if "simplify_rules" in learning["actions"]
                else None
            ),
            control_rate=0.10,
        )

    def _load_learning_policy(
        self,
    ) -> tuple[ContextualThompsonBandit, int | None]:
        record = self.store.get_state("alice.learning-policy")
        if record is None:
            return self._new_learning_policy(), None
        return ContextualThompsonBandit.from_state(record.value), record.version

    def _choose_mutation(self, task: TaskRecord) -> dict[str, Any]:
        if task.candidate_id is None:
            raise EngineError("candidate.choose_mutation is not candidate-bound")
        candidate = self.store.get_candidate(task.candidate_id)
        context = {
            "stage": candidate.state,
            "kind": candidate.kind,
            "failed_gate": candidate.metadata.get("last_gate_failure"),
            "mechanism_family": candidate.content.get("mechanism_family")
            if isinstance(candidate.content, Mapping)
            else None,
            "player_count": candidate.content.get("player_count")
            if isinstance(candidate.content, Mapping)
            else None,
            "duration_minutes": candidate.content.get("duration_minutes")
            if isinstance(candidate.content, Mapping)
            else None,
            "audience": candidate.content.get("audience")
            if isinstance(candidate.content, Mapping)
            else None,
        }
        for _ in range(5):
            learner, version = self._load_learning_policy()
            selection = learner.recommend(context, explore=True)
            try:
                state = self.store.put_state(
                    "alice.learning-policy",
                    learner.to_state(),
                    version,
                )
            except StateConflictError:
                continue
            return {
                "action": selection.action,
                "context": context,
                "selection": selection.to_state(),
                "state_version": state.version,
                "expectation_required": True,
            }
        raise EngineError("learning policy changed repeatedly during mutation selection")

    def _update_learning_policy(self, task: TaskRecord) -> dict[str, Any]:
        dependencies = task.payload.get("dependencies")
        outcome_dependency = (
            dependencies.get("outcomes.ingest")
            if isinstance(dependencies, Mapping)
            else None
        )
        result = (
            outcome_dependency.get("result")
            if isinstance(outcome_dependency, Mapping)
            else None
        )
        content, executor, evidence_class = _result_content_provenance(result)
        if executor != "adapter" or evidence_class != "external":
            raise EngineError("learning updates require the external outcomes adapter")
        outcomes = content.get("outcomes")
        if not isinstance(outcomes, list):
            raise EngineError("outcomes adapter did not return an outcomes array")

        for _ in range(5):
            learner, version = self._load_learning_policy()
            updates = []
            for raw in outcomes:
                if not isinstance(raw, Mapping):
                    raise EngineError("outcome entries must be objects")
                event_id = raw.get("event_id")
                if not isinstance(event_id, str) or not event_id:
                    raise EngineError("external outcomes require unique event_id values")
                self._reject_ineligible_market_signal(event_id, "learning")
                update = learner.observe(
                    str(raw.get("action") or ""),
                    raw.get("outcome"),
                    raw.get("context"),
                    evidence_source=raw.get("source"),
                    verified=True,
                    surrogate=bool(raw.get("surrogate", False)),
                    same_model=bool(raw.get("same_model", False)),
                    evaluator_id=(
                        str(raw["evaluator_id"])
                        if raw.get("evaluator_id") is not None
                        else None
                    ),
                    candidate_model_id=(
                        str(raw["candidate_model_id"])
                        if raw.get("candidate_model_id") is not None
                        else None
                    ),
                    weight=raw.get("weight", 1.0),
                    event_id=event_id,
                )
                updates.append(update.to_state())
            try:
                state = self.store.put_state(
                    "alice.learning-policy",
                    learner.to_state(),
                    version,
                )
            except StateConflictError:
                continue
            return {
                "accepted": sum(1 for update in updates if update["accepted"]),
                "rejected": sum(1 for update in updates if not update["accepted"]),
                "state_version": state.version,
                "updates": updates,
            }
        raise EngineError("learning policy changed repeatedly during outcome update")

    def _reject_ineligible_market_signal(self, event_id: str, purpose: str) -> None:
        knowledge = self.config.get("knowledge")
        market = knowledge.get("market_signals") if isinstance(knowledge, Mapping) else None
        signals = market.get("signals") if isinstance(market, Mapping) else None
        if not isinstance(signals, list):
            return
        for signal in signals:
            if not isinstance(signal, Mapping) or signal.get("id") != event_id:
                continue
            if (
                signal.get("release_evidence_eligible") is False
                or signal.get("learning_outcome_eligible") is False
            ):
                raise EngineError(
                    f"configured pre-Alice market signal {event_id!r} is not "
                    f"eligible for {purpose}"
                )

    def _recent_knowledge(self, current: TaskRecord) -> list[dict[str, Any]]:
        """Feed verified loop outputs forward without turning chat into memory."""

        prefixes = (
            "library.",
            "history.",
            "harness.",
            "outcomes.",
            "orders.outcome",
            "policy.shadow",
            "candidate.prior_art",
        )
        snapshot: list[dict[str, Any]] = []
        tasks = self.store.list_tasks(state="succeeded", limit=1_000)
        for task in reversed(tasks):
            if task.id == current.id or not task.kind.startswith(prefixes):
                continue
            try:
                content, _, _ = _result_content_provenance(task.result)
            except EngineError:
                continue
            snapshot.append(
                {
                    "action": task.kind,
                    "candidate_id": task.candidate_id,
                    "output_sha256": task.output_sha256,
                    "content": _compact_knowledge_content(content),
                }
            )
            if len(snapshot) >= 12:
                break
        return snapshot

    def _adapter_for(self, action: str) -> CommandAdapter | None:
        action = canonical_task_kind(action)
        if action == "library.read":
            return self.adapters.get("library")
        if action in {
            "concept.prior_art",
            "candidate.prior_art",
            "candidate.safety_ip",
            "market.final_safety_ip",
        }:
            return self.adapters.get("research")
        if action in {"rules.lint", "rules.adversary"}:
            return self.adapters.get("rules_validator")
        if action.startswith("simulation."):
            return self.adapters.get("digital_playtest")
        if action in {"human.prepare_blind_kit", "human.collect_blind_results"}:
            return self.adapters.get("human_playtest")
        if action in {"physical.cad", "physical.dfm"}:
            return self.adapters.get("cad")
        if action == "physical.create_rich_draft":
            return self.adapters.get("page_builder")
        if action in {"physical.prototype_print", "physical.production_run"}:
            return self.adapters.get("print_fulfillment")
        if action.startswith("orders."):
            if action == "orders.poll_paid":
                return self.adapters.get("delivery")
            return self.adapters.get("print_fulfillment")
        if action in {SEND_TO_SHOP, SEND_VERIFY_SHOP}:
            return self.adapters.get("shop_door")
        if action == "publish.effect":  # durable compatibility only
            return self.adapters.get("shop_door")
        if action == "market.validate_offer":
            return self.adapters.get("market_validation")
        if action == "outcomes.ingest":
            return self.adapters.get("outcomes")
        if action in {"history.scan_traditional", "history.scan_modern"}:
            return self.adapters.get("history")
        return None

    def _record_result(self, task: TaskRecord) -> None:
        if self.store.get_task_derived_application(task.id) is not None:
            return
        if task.state != "succeeded" or task.output_sha256 is None:
            raise EngineError("only an exact succeeded task result can be applied")
        content, _, _ = _result_content_provenance(task.result)
        if task.candidate_id:
            candidate_version = task.payload.get("candidate_version")
            if isinstance(candidate_version, bool) or not isinstance(
                candidate_version, int
            ):
                raise EngineError("candidate result lacks its captured version")
            self.store.record_candidate_artifact(
                task.candidate_id,
                task.id,
                task.kind,
                candidate_version,
                task.output_sha256,
                content,
            )
            verdict = content.get("verdict") if isinstance(content, dict) else None
            if isinstance(verdict, dict):
                verdict_name = str(verdict.get("status") or "recorded")
                score = verdict.get("score")
                score_value = float(score) if isinstance(score, (int, float)) else None
            else:
                verdict_name = "recorded"
                score_value = None
            self.store.add_evaluation(
                task.candidate_id,
                str(task.payload["role"]),
                score=score_value,
                verdict=verdict_name,
                metrics=content,
                idempotency_key=f"task-result:{task.id}:{task.output_sha256}",
            )
        if task.kind == "concept.select" and isinstance(content, dict):
            candidate = content.get("candidate")
            if isinstance(candidate, dict):
                self._create_selected_candidate(task, candidate)
        if task.kind == "candidate.apply_mutation" and task.candidate_id:
            self._apply_mutation_result(task, content)
        if task.kind.startswith("orders."):
            self._record_order_result(task)
        if task.candidate_id:
            self._maybe_advance_candidate(task.candidate_id)

        graph_at = time.time()
        if task.candidate_id:
            self._schedule_candidate(task.candidate_id, now=graph_at)
        if task.run_id and task.run_id.startswith("loop:"):
            parts = task.run_id.split(":", 2)
            if len(parts) == 3 and parts[1] in LOOPS:
                self._schedule_graph(parts[1], task.run_id, now=graph_at)
        self.store.mark_task_derived_applied(task.id, task.output_sha256)

    def _irreversible_task_effect_identity(
        self, task: TaskRecord
    ) -> tuple[str, str, dict[str, Any]]:
        if task.kind not in _EFFECT_RECONCILE_OPERATIONS:
            raise EngineError(f"{task.kind} is not a managed external effect")
        identity: dict[str, Any] = {
            "schema_version": 1,
            "task_id": task.id,
            "task_input_sha256": task.input_sha256,
            "action": task.kind,
        }
        if task.kind.startswith("orders."):
            intent = fulfillment_intent_from_payload(
                task.payload.get("fulfillment_intent")
            )
            operation_key = intent.operation_key
            identity["intent_sha256"] = intent.intent_sha256
            key = f"alice.effect:fulfillment:{operation_key}:{task.kind}"
        else:
            candidate_id = task.candidate_id
            candidate_version = task.payload.get("candidate_version")
            candidate_content_sha256 = task.payload.get(
                "candidate_content_sha256"
            )
            candidate_state = _CANDIDATE_PHYSICAL_EFFECT_STATES.get(task.kind)
            if (
                not isinstance(candidate_id, str)
                or not candidate_id
                or isinstance(candidate_version, bool)
                or not isinstance(candidate_version, int)
                or candidate_version <= 0
                or not isinstance(candidate_content_sha256, str)
                or candidate_state is None
            ):
                raise EngineError(
                    f"{task.kind} lacks its immutable candidate effect fence"
                )
            identity.update(
                {
                    "candidate_id": candidate_id,
                    "candidate_state": candidate_state,
                    "candidate_version": candidate_version,
                    "candidate_content_sha256": candidate_content_sha256,
                }
            )
            operation_key = (
                f"alice:physical-effect:v1:{task.kind}:{task.input_sha256}"
            )
            key = f"alice.effect:task:{task.kind}:{task.input_sha256}"
        identity["operation_key"] = operation_key
        return key, operation_key, identity

    @staticmethod
    def _validate_effect_state_identity(
        task: TaskRecord,
        value: Any,
        identity: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise EngineError(f"{task.kind} effect state is malformed")
        for name, expected in identity.items():
            if value.get(name) != expected:
                raise EngineError(
                    f"{task.kind} effect state has a mismatched {name}"
                )
        return dict(value)

    def _prepare_irreversible_task_effect(
        self, task: TaskRecord
    ) -> tuple[str, dict[str, Any], dict[str, Any] | None]:
        """Claim a write once; all later attempts are reconciliation-only."""

        key, operation_key, identity = self._irreversible_task_effect_identity(task)
        is_candidate_physical = task.kind in _CANDIDATE_PHYSICAL_EFFECT_STATES
        while True:
            state = self.store.get_state(key)
            if state is None:
                try:
                    if is_candidate_physical:
                        self.store.claim_candidate_physical_effect_send(
                            key,
                            candidate_id=str(identity["candidate_id"]),
                            candidate_state=str(identity["candidate_state"]),
                            candidate_version=int(identity["candidate_version"]),
                            candidate_content_sha256=str(
                                identity["candidate_content_sha256"]
                            ),
                            action=task.kind,
                            identity=identity,
                            send_attempt_id=task.lease_attempt_id,
                        )
                    else:
                        self.store.put_state(
                            key, {**identity, "status": "prepared"}, None
                        )
                except StateConflictError as exc:
                    if is_candidate_physical and self.store.get_state(key) is None:
                        raise EngineError(str(exc)) from exc
                    continue
                if not is_candidate_physical:
                    continue
                payload = dict(task.payload)
                payload.update(
                    {
                        "reconcile_only": False,
                        "original_operation": task.kind,
                        "effect_operation_key": operation_key,
                        "task_input_sha256": task.input_sha256,
                    }
                )
                return task.kind, payload, None
            value = self._validate_effect_state_identity(
                task, state.value, identity
            )
            status = value.get("status")
            if status == "prepared":
                try:
                    if is_candidate_physical:
                        self.store.claim_candidate_physical_effect_send(
                            key,
                            candidate_id=str(identity["candidate_id"]),
                            candidate_state=str(identity["candidate_state"]),
                            candidate_version=int(identity["candidate_version"]),
                            candidate_content_sha256=str(
                                identity["candidate_content_sha256"]
                            ),
                            action=task.kind,
                            identity=identity,
                            send_attempt_id=task.lease_attempt_id,
                        )
                    else:
                        value["status"] = "sending"
                        value["send_attempt_id"] = task.lease_attempt_id
                        self.store.put_state(key, value, state.version)
                except StateConflictError as exc:
                    if is_candidate_physical:
                        latest = self.store.get_state(key)
                        if latest is None or latest.version == state.version:
                            raise EngineError(str(exc)) from exc
                    continue
                payload = dict(task.payload)
                payload.update(
                    {
                        "reconcile_only": False,
                        "original_operation": task.kind,
                        "effect_operation_key": operation_key,
                        "task_input_sha256": task.input_sha256,
                    }
                )
                return task.kind, payload, None
            if status == "sending":
                payload = dict(task.payload)
                payload.update(
                    {
                        "reconcile_only": True,
                        "original_operation": task.kind,
                        "effect_operation_key": operation_key,
                        "task_input_sha256": task.input_sha256,
                    }
                )
                return _EFFECT_RECONCILE_OPERATIONS[task.kind], payload, None
            if status == "confirmed":
                result = value.get("result")
                result_sha256 = value.get("result_sha256")
                if (
                    not isinstance(result, dict)
                    or not isinstance(result_sha256, str)
                    or _canonical_sha256(result) != result_sha256
                ):
                    raise EngineError(
                        f"{task.kind} confirmed effect result is corrupt"
                    )
                return task.kind, dict(task.payload), dict(result)
            if status == "ambiguous":
                raise EngineError(
                    f"{task.kind} effect is ambiguous and requires reconciliation"
                )
            raise EngineError(f"{task.kind} effect has invalid status {status!r}")

    def _confirm_irreversible_task_effect(
        self, task: TaskRecord, result: Mapping[str, Any]
    ) -> dict[str, Any]:
        key, _, identity = self._irreversible_task_effect_identity(task)
        durable_result = dict(result)
        result_sha256 = _canonical_sha256(durable_result)
        while True:
            state = self.store.get_state(key)
            if state is None:
                raise EngineError(f"{task.kind} effect claim disappeared")
            value = self._validate_effect_state_identity(
                task, state.value, identity
            )
            status = value.get("status")
            if status == "confirmed":
                cached = value.get("result")
                cached_sha256 = value.get("result_sha256")
                if (
                    not isinstance(cached, dict)
                    or _canonical_sha256(cached) != cached_sha256
                ):
                    raise EngineError(
                        f"{task.kind} confirmed effect result is corrupt"
                    )
                return dict(cached)
            if status != "sending":
                raise EngineError(
                    f"{task.kind} cannot confirm effect from {status!r}"
                )
            value.update(
                {
                    "status": "confirmed",
                    "result": durable_result,
                    "result_sha256": result_sha256,
                }
            )
            try:
                self.store.put_state(key, value, state.version)
            except StateConflictError:
                continue
            return durable_result

    def _mark_irreversible_task_effect_ambiguous(
        self, task: TaskRecord, reason: str
    ) -> None:
        try:
            key, _, identity = self._irreversible_task_effect_identity(task)
        except (EngineError, FulfillmentValidationError, TypeError, ValueError):
            return
        reason_sha256 = hashlib.sha256(reason.encode("utf-8")).hexdigest()
        while True:
            state = self.store.get_state(key)
            if state is None:
                return
            try:
                value = self._validate_effect_state_identity(
                    task, state.value, identity
                )
            except EngineError:
                return
            if value.get("status") in {"confirmed", "ambiguous"}:
                return
            value.update(
                {"status": "ambiguous", "error_sha256": reason_sha256}
            )
            try:
                self.store.put_state(key, value, state.version)
            except StateConflictError:
                continue
            return

    def _validate_fulfillment_result(
        self, task: TaskRecord, result: Mapping[str, Any]
    ) -> None:
        if task.kind == "orders.poll_paid":
            build_fulfillment_intents(
                result,
                self.store.list_publications(
                    target="vibe_pipeline", state="confirmed", limit=10_000
                ),
            )
            return
        if task.kind not in {"orders.create_print_job", "orders.qa_ship"}:
            return
        intent = fulfillment_intent_from_payload(
            task.payload.get("fulfillment_intent")
        )
        if task.kind == "orders.create_print_job":
            receipts = validate_print_job_receipts([intent], result)
            receipt = receipts[0]
            try:
                self.store.bind_manufacturing_job(
                    receipt.job_id,
                    order_id=intent.order_id,
                    operation_key=intent.operation_key,
                    intent_sha256=intent.intent_sha256,
                    task_input_sha256=task.input_sha256,
                    receipt_sha256=receipt.receipt_sha256,
                )
            except StateConflictError as exc:
                raise EngineError(str(exc)) from exc
            return
        print_receipt = print_job_receipt_from_payload(
            task.payload.get("print_job_receipt")
        )
        validate_qa_ship_receipts([intent], [print_receipt], result)

    def _record_order_result(self, task: TaskRecord) -> None:
        if task.output_sha256 is None:
            raise EngineError("order result lacks output hash")
        if task.kind == "orders.poll_paid":
            intents = build_fulfillment_intents(
                task.result,
                self.store.list_publications(
                    target="vibe_pipeline", state="confirmed", limit=10_000
                ),
            )
            for intent in intents:
                intent_payload = intent.as_payload()
                self._put_immutable_state(
                    f"alice.fulfillment-intent:{intent.operation_key}",
                    intent_payload,
                )
                self.store.enqueue_task(
                    "orders.create_print_job",
                    {
                        "loop": "orders",
                        "action": "orders.create_print_job",
                        "role": "fulfillment_planner",
                        "objective": "Create exactly one packet-bound print job.",
                        "depends_on": [],
                        "dependencies": {},
                        "work_payload": {},
                        "fulfillment_intent": intent_payload,
                    },
                    idempotency_key=(
                        f"fulfillment:{intent.operation_key}:create-print-job"
                    ),
                    run_id=f"order:{intent.operation_key}",
                    priority=100,
                    max_attempts=int(self.config["runtime"]["max_attempts"]),
                )
            return
        intent = fulfillment_intent_from_payload(
            task.payload.get("fulfillment_intent")
        )
        if task.kind == "orders.create_print_job":
            receipts = validate_print_job_receipts([intent], task.result)
            try:
                self.store.bind_manufacturing_job(
                    receipts[0].job_id,
                    order_id=intent.order_id,
                    operation_key=intent.operation_key,
                    intent_sha256=intent.intent_sha256,
                    task_input_sha256=task.input_sha256,
                    receipt_sha256=receipts[0].receipt_sha256,
                )
            except StateConflictError as exc:
                raise EngineError(str(exc)) from exc
            receipt_payload = receipts[0].as_payload()
            self._put_immutable_state(
                f"alice.fulfillment-print:{intent.operation_key}", receipt_payload
            )
            self.store.enqueue_task(
                "orders.qa_ship",
                {
                    "loop": "orders",
                    "action": "orders.qa_ship",
                    "role": "dfm_verifier",
                    "objective": "QA and ship the exact completed print job.",
                    "depends_on": [],
                    "dependencies": {},
                    "work_payload": {},
                    "fulfillment_intent": intent.as_payload(),
                    "print_job_receipt": receipt_payload,
                },
                idempotency_key=f"fulfillment:{intent.operation_key}:qa-ship",
                run_id=f"order:{intent.operation_key}",
                priority=100,
                max_attempts=int(self.config["runtime"]["max_attempts"]),
            )
            return
        if task.kind == "orders.qa_ship":
            printed = print_job_receipt_from_payload(
                task.payload.get("print_job_receipt")
            )
            shipments = validate_qa_ship_receipts(
                [intent], [printed], task.result
            )
            shipment_payload = shipments[0].as_payload()
            self._put_immutable_state(
                f"alice.fulfillment-shipment:{intent.operation_key}",
                shipment_payload,
            )
            self.store.add_experience(
                "fulfillment.shipped",
                shipment_payload,
                task_id=task.id,
                idempotency_key=(
                    f"fulfillment-shipped:{intent.operation_key}:"
                    f"{shipments[0].receipt_sha256}"
                ),
            )

    def _put_immutable_state(self, key: str, value: Mapping[str, Any]) -> None:
        existing = self.store.get_state(key)
        if existing is None:
            try:
                self.store.put_state(key, dict(value), None)
                return
            except StateConflictError:
                existing = self.store.get_state(key)
        if existing is None or existing.value != dict(value):
            raise EngineError(f"immutable fulfillment state conflict at {key}")

    def _task_is_quarantined(self, task_id: str) -> bool:
        return self.store.get_state(f"alice.task-quarantine:{task_id}") is not None

    def _quarantine_result(self, task: TaskRecord, error: Exception) -> None:
        """Isolate one malformed succeeded result without stopping the worker."""

        if task.output_sha256 is None:
            raise EngineError("cannot quarantine a task without an output hash")
        key = f"alice.task-quarantine:{task.id}"
        if self.store.get_state(key) is None:
            try:
                self.store.put_state(
                    key,
                    {
                        "task_id": task.id,
                        "kind": task.kind,
                        "candidate_id": task.candidate_id,
                        "output_sha256": task.output_sha256,
                        "error_code": type(error).__name__,
                        "error_message": str(error),
                    },
                    None,
                )
            except StateConflictError:
                pass
        self.store.add_experience(
            "task.result_quarantined",
            {
                "task_id": task.id,
                "kind": task.kind,
                "output_sha256": task.output_sha256,
                "error_code": type(error).__name__,
                "error_message": str(error),
            },
            task_id=task.id,
            candidate_id=task.candidate_id,
            idempotency_key=f"task-result-quarantined:{task.id}:{task.output_sha256}",
        )
        if task.candidate_id is not None:
            current = self.store.get_candidate(task.candidate_id)
            captured = task.payload.get("candidate_version")
            if (
                current.state not in TERMINAL_STATES | {"rework"}
                and current.version == captured
            ):
                try:
                    self.store.transition_candidate(
                        current.id,
                        "rework",
                        expected_state=current.state,
                        expected_version=current.version,
                        metadata_patch={
                            "last_gate_failure": {
                                "codes": ["malformed_durable_result"],
                                "task_id": task.id,
                                "action": task.kind,
                                "error": str(error),
                            }
                        },
                    )
                except StateConflictError:
                    pass
        self.store.mark_task_derived_applied(task.id, task.output_sha256)

    def _apply_mutation_result(
        self,
        task: TaskRecord,
        content: Mapping[str, Any],
    ) -> None:
        assert task.candidate_id is not None
        captured_version = task.payload.get("candidate_version")
        current = self.store.get_candidate(task.candidate_id)
        if current.state != "rework" or current.version != captured_version:
            self.store.add_experience(
                "candidate.stale_mutation_discarded",
                {
                    "task_id": task.id,
                    "captured_version": captured_version,
                    "current_version": current.version,
                    "current_state": current.state,
                },
                task_id=task.id,
                candidate_id=current.id,
                idempotency_key=f"stale-mutation:{task.id}:{task.output_sha256}",
            )
            return
        dependencies = task.payload.get("dependencies")
        choose = (
            dependencies.get("candidate.choose_mutation")
            if isinstance(dependencies, Mapping)
            else None
        )
        choose_result = choose.get("result") if isinstance(choose, Mapping) else None
        selection_content, executor, _ = _result_content_provenance(choose_result)
        if executor != "learning_policy":
            raise EngineError("mutation is not bound to a learning-policy selection")
        action = selection_content.get("action")
        if action != content.get("action") or action not in self.config["learning"]["actions"]:
            raise EngineError("applied mutation does not match the selected action")
        expectation = content.get("expectation")
        if not isinstance(expectation, str) or not expectation.strip():
            raise EngineError("mutation needs a falsifiable expectation")

        self.store.add_experience(
            "candidate.mutation_applied",
            {
                "candidate_id": current.id,
                "candidate_version": current.version,
                "action": action,
                "expectation": expectation,
                "selection": selection_content.get("selection"),
            },
            task_id=task.id,
            candidate_id=current.id,
            idempotency_key=f"mutation-applied:{task.id}:{task.output_sha256}",
        )
        if action == "kill_candidate":
            self.store.transition_candidate(
                current.id,
                "killed",
                expected_state="rework",
                expected_version=current.version,
                metadata_patch={
                    "last_mutation_action": action,
                    "last_mutation_expectation": expectation,
                },
            )
            return

        mutated = content.get("candidate")
        if not isinstance(mutated, Mapping):
            raise EngineError("candidate.apply_mutation must return the revised candidate")
        _validate_3d_game_candidate(mutated)
        metadata = {
            key: value
            for key, value in current.metadata.items()
            if key
            not in {
                "accepted_artifacts",
                "accepted_artifact_manifest_sha256",
                "accepted_manifests",
                "last_evidence_id",
                "last_evidence_source",
                "last_receipt_sha256",
                "release_decision",
                "publication_binding",
            }
        }
        metadata.update(
            {
                "last_mutation_action": action,
                "last_mutation_expectation": expectation,
                "mutated_from_version": current.version,
            }
        )
        updated = self.store.update_candidate(
            current.id,
            dict(mutated),
            title=str(mutated["title"]),
            metadata=metadata,
            expected_version=current.version,
        )
        self.store.transition_candidate(
            current.id,
            "proposed",
            expected_state="rework",
            expected_version=updated.version,
        )

    def _maybe_advance_candidate(self, candidate_id: str) -> None:
        candidate = self.store.get_candidate(candidate_id)
        target_state = next_progress_state(candidate.state)
        if target_state is None:
            return
        work = work_for_state(candidate.state, candidate.id)
        if not work:
            return
        run_id = f"candidate:{candidate.id}:v{candidate.version}"
        tasks = _tasks_by_current_kind(
            self.store.list_tasks(run_id=run_id, limit=1_000)
        )
        required_actions = {item.action for item in work}
        if set(tasks) < required_actions or any(
            tasks[action].state != "succeeded" for action in required_actions
        ):
            return
        task_version = candidate.version
        artifacts = []
        for action in sorted(required_actions):
            task = tasks[action]
            if task.payload.get("candidate_version") != task_version:
                raise EngineError("candidate stage contains a stale task")
            artifact = self.store.get_candidate_artifact_for_task(task.id)
            if artifact is None:
                # The final task can complete before an earlier task's derived
                # artifact has replayed. Recovery will revisit both.
                return
            content, executor, evidence_class = _result_content_provenance(task.result)
            artifacts.append(
                ArtifactSnapshot(
                    action=artifact.action,
                    task_id=artifact.task_id,
                    candidate_version=artifact.candidate_version,
                    output_sha256=artifact.output_sha256,
                    content_sha256=artifact.content_sha256,
                    executor=executor,
                    evidence_class=evidence_class,
                    content=content,
                )
            )

        gate_failure = _stage_gate_failure(candidate.state, artifacts, self.config)
        if gate_failure is not None:
            self.store.add_experience(
                "candidate.gate_failed",
                {
                    "candidate_id": candidate.id,
                    "candidate_version": candidate.version,
                    "state": candidate.state,
                    "reason": gate_failure,
                },
                candidate_id=candidate.id,
                idempotency_key=(
                    f"candidate-gate-failed:{candidate.id}:v{candidate.version}:"
                    f"{_canonical_sha256(gate_failure)}"
                ),
            )
            self.store.transition_candidate(
                candidate.id,
                "rework",
                expected_state=candidate.state,
                expected_version=candidate.version,
                metadata_patch={"last_gate_failure": gate_failure},
            )
            return

        manifest, manifest_sha256 = artifact_manifest(artifacts)
        source = {
            "proposed": "independent_model",
            "researched": "deterministic",
            "rules_valid": "simulation",
            "digitally_playtested": "deterministic",
            "human_ready": "blind_human",
            "human_validated": "manufacturing",
            "physical_ready": "manufacturing",
            "production_validated": "release_policy",
        }.get(candidate.state)
        if candidate.state in {"publish_ready", "page_ready"}:
            terminal_kind = (
                SEND_TO_SHOP
                if candidate.state == "publish_ready"
                else SEND_VERIFY_SHOP
            )
            terminal_artifact = next(
                (
                    artifact
                    for artifact in artifacts
                    if canonical_task_kind(artifact.action) == terminal_kind
                ),
                None,
            )
            if terminal_artifact is not None and terminal_artifact.evidence_class in {
                "shop_door",
                "publishing_pipeline",
            }:
                source = terminal_artifact.evidence_class
        if source is None:
            return
        receipt: dict[str, Any] = {
            "candidate_id": candidate.id,
            "candidate_version": candidate.version,
            "target_state": target_state,
            "artifacts": manifest,
            "artifact_manifest_sha256": manifest_sha256,
        }
        if candidate.state == "production_validated":
            release_task = tasks["release.evaluate"]
            release_content, _, _ = _result_content_provenance(release_task.result)
            receipt.update(dict(release_content))
            receipt["release_artifact_manifest_sha256"] = release_content.get(
                "artifact_manifest_sha256"
            )
            receipt["candidate_id"] = candidate.id
            receipt["candidate_version"] = candidate.version
            receipt["target_state"] = target_state
            receipt["artifacts"] = manifest
            receipt["artifact_manifest_sha256"] = manifest_sha256
        elif candidate.state in {"publish_ready", "page_ready"}:
            terminal_action = (
                SEND_TO_SHOP
                if candidate.state == "publish_ready"
                else SEND_VERIFY_SHOP
            )
            pipeline_content, _, _ = _result_content_provenance(
                tasks[terminal_action].result
            )
            receipt.update(dict(pipeline_content))
            receipt["candidate_id"] = candidate.id
            receipt["candidate_version"] = candidate.version
            receipt["target_state"] = target_state
            receipt["artifacts"] = manifest
            receipt["artifact_manifest_sha256"] = manifest_sha256
        evidence = TransitionEvidence(
            evidence_id=(
                f"stage:{candidate.id}:v{candidate.version}:"
                f"{manifest_sha256}"
            ),
            source=source,
            verified=True,
            receipt=receipt,
            held_out=source == "blind_human",
        )
        advance_with_evidence(
            self.store,
            candidate.id,
            target_state,
            evidence,
            expected_policy_hash=self.release_policy.policy_hash,
        )

    def _create_selected_candidate(self, task: TaskRecord, candidate: dict[str, Any]) -> None:
        active = [
            item
            for item in self.store.list_candidates(limit=1_000)
            if item.state not in TERMINAL_STATES
        ]
        if len(active) >= int(self.config["runtime"]["max_active_candidates"]):
            self.store.add_experience(
                "candidate.deferred",
                {"reason": "portfolio_full", "candidate": candidate},
                task_id=task.id,
                idempotency_key=f"candidate-deferred:{task.id}:{task.output_sha256}",
            )
            return
        _validate_3d_game_candidate(candidate)
        title = str(candidate["title"])
        content_hash = hashlib.sha256(
            json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.store.create_candidate(
            candidate,
            kind="3d_printable_board_game",
            title=title,
            task_id=task.id,
            idempotency_key=f"selected:{task.run_id}:{content_hash}",
            metadata={"source_run_id": task.run_id, "source_output_sha256": task.output_sha256},
        )

    def run_forever(self, *, poll_seconds: float | None = None) -> None:
        delay = (
            float(self.config["runtime"]["poll_seconds"])
            if poll_seconds is None
            else float(poll_seconds)
        )
        if delay <= 0:
            raise ValueError("poll_seconds must be positive")
        while True:
            task = self.work_once()
            if task is None:
                time.sleep(delay)


def _validate_required(content: Mapping[str, Any], contract: Mapping[str, Any]) -> None:
    missing = [name for name in contract.get("required", ()) if name not in content]
    if missing:
        raise EngineError("agent response missing required fields: " + ", ".join(missing))


def _durable_error_message(exc: Exception) -> str:
    """Keep provider-controlled text out of the durable task/event ledger."""

    if isinstance(exc, ProviderError):
        encoded = str(exc).encode("utf-8", errors="replace")
        return (
            f"ProviderError:detail_sha256={hashlib.sha256(encoded).hexdigest()};"
            f"detail_bytes={len(encoded)}"
        )
    return str(exc)


_FORBIDDEN_DURABLE_ADAPTER_KEYS = frozenset(
    {
        "authorization",
        "proxy_authorization",
        "password",
        "passwd",
        "secret",
        "client_secret",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "bearer_token",
        "private_key",
        "card_number",
        "cvv",
        "cvc",
        "email",
        "email_address",
        "phone",
        "phone_number",
        "address",
        "street_address",
        "shipping_address",
        "billing_address",
        "recipient_name",
        "customer_name",
        "full_name",
        "first_name",
        "last_name",
        "contact_name",
        "mobile",
        "telephone",
        "postal_address",
        "address_line_1",
        "address_line_2",
    }
)
_SENSITIVE_NESTED_IDENTITY_KEYS = frozenset(
    {"name", "first", "last", "city", "postal_code", "zip", "zipcode"}
)
_DURABLE_SECRET_VALUE = re.compile(
    r"(?i)(?:\bbearer\s+[A-Za-z0-9._~+/=-]{8,}|\bsk-[A-Za-z0-9_-]{8,})"
)
_DURABLE_EMAIL_VALUE = re.compile(
    r"(?i)(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])"
)

_ADAPTER_OPTIONAL_FIELDS: dict[str, frozenset[str]] = {
    "physical.create_rich_draft": frozenset(
        {
            "schema_version",
            "input_sha256",
            "production_slug",
            "artifact_manifest_sha256",
            "provenance_sha256",
            "project_files",
            "receipt_source",
            "pipeline_run_id",
            "operator_stdout_sha256",
        }
    ),
    SEND_TO_SHOP: frozenset(
        {
            "operation_key",
            "publication_id",
            "candidate_id",
            "packet_hash",
            "pipeline_run_id",
            "design_id",
            "history_id",
            "page_url",
            "price_cents",
            "sku",
            "currency",
        }
    ),
    SEND_VERIFY_SHOP: frozenset(
        {
            "operation_key",
            "publication_id",
            "candidate_id",
            "packet_hash",
            "pipeline_run_id",
            "design_id",
            "history_id",
            "page_url",
            "price_cents",
            "sku",
            "currency",
        }
    ),
}


def _reject_sensitive_adapter_payload(value: Any, *, path: str = "payload") -> None:
    """Keep raw credentials and customer PII out of the immutable ledger."""

    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise EngineError(f"{path} contains a non-string key")
            snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
            normalized = re.sub(r"[^a-z0-9]+", "_", snake.casefold()).strip("_")
            sensitive_context = ".orders[" in path or "consent" in path.casefold()
            if normalized in _FORBIDDEN_DURABLE_ADAPTER_KEYS or (
                sensitive_context and normalized in _SENSITIVE_NESTED_IDENTITY_KEYS
            ):
                raise EngineError(
                    f"adapter payload contains forbidden sensitive field {path}.{key}"
                )
            _reject_sensitive_adapter_payload(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_sensitive_adapter_payload(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and (
        _DURABLE_SECRET_VALUE.search(value) or _DURABLE_EMAIL_VALUE.search(value)
    ):
        raise EngineError(f"adapter payload contains sensitive text at {path}")


def _validate_adapter_payload_shape(
    action: str,
    content: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> None:
    """Persist only the documented top-level receipt fields for each adapter."""

    required_adapter = _required_adapter_name(action)
    if required_adapter is None:
        return
    allowed = set(contract.get("required", ()))
    allowed.update(_ADAPTER_OPTIONAL_FIELDS.get(canonical_task_kind(action), ()))
    if not allowed:
        raise EngineError(f"{action} has no closed durable adapter payload contract")
    unexpected = sorted(set(content) - allowed)
    if unexpected:
        raise EngineError(
            f"{action} adapter payload has undocumented fields: "
            + ", ".join(unexpected)
        )


def _validate_action_semantics(action: str, content: Mapping[str, Any]) -> None:
    """Reject common malformed gate values before a task can be committed."""

    try:
        validate_output_semantics(action, content)
    except ValueError as exc:
        raise EngineError(str(exc)) from exc

    nonnegative_fields: dict[str, tuple[str, ...]] = {
        "candidate.safety_ip": (
            "critical_safety_findings",
            "critical_ip_findings",
        ),
        "rules.adversary": ("critical_exploits",),
        "simulation.exploit": ("critical_exploits",),
        "human.collect_blind_results": (
            "blind_groups",
            "minimum_games_per_group",
            "designer_hints_required",
        ),
        "market.final_safety_ip": (
            "critical_safety_findings",
            "critical_ip_findings",
        ),
    }
    for name in nonnegative_fields.get(action, ()):
        value = content.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise EngineError(f"{action} {name} must be a non-negative integer")
    if action == "rules.lint":
        if not isinstance(content.get("rules_complete"), bool) or not isinstance(
            content.get("terminates"), bool
        ):
            raise EngineError("rules.lint completion fields must be booleans")
        if not isinstance(content.get("ambiguities"), list):
            raise EngineError("rules.lint ambiguities must be a list")
    if action == "simulation.optimizer":
        dominant = content.get("dominant_strategy")
        if dominant is not None and not isinstance(dominant, (bool, str)):
            raise EngineError(
                "simulation.optimizer dominant_strategy must be boolean, string, or null"
            )
    if action == "human.prepare_blind_kit":
        try:
            validate_blind_kit(content)
        except ReleaseAssemblyError as exc:
            raise EngineError(str(exc)) from exc
    if action == "human.collect_blind_results":
        try:
            validate_blind_human_evidence(content)
        except ReleaseAssemblyError as exc:
            raise EngineError(str(exc)) from exc
    if action in {"physical.cad", "physical.dfm"}:
        artifact_hashes = content.get("artifact_hashes")
        try:
            validate_printable_artifact_hashes(
                artifact_hashes if isinstance(artifact_hashes, Mapping) else {},
                source=f"{action}.artifact_hashes",
            )
        except PageBuilderError as exc:
            raise EngineError(str(exc)) from exc
        _validate_text2game_physical_receipt(action, content)
    if action in {"physical.dfm", "physical.production_run"}:
        value = content.get("print_yield")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not (
            0.0 <= float(value) <= 1.0
        ):
            raise EngineError(f"{action} print_yield must be between zero and one")
        if action == "physical.dfm" and content.get("fit") is not True:
            raise EngineError("physical.dfm fit must be the exact boolean true")
    if action in {"physical.prototype_print", "physical.production_run"}:
        try:
            validate_manufacturing_receipt(content, action)
        except ReleaseAssemblyError as exc:
            raise EngineError(str(exc)) from exc
    if action == "physical.production_run":
        manifest = content.get("production_manifest")
        try:
            validate_production_manifest(
                manifest if isinstance(manifest, Mapping) else {}
            )
        except ReleaseAssemblyError as exc:
            raise EngineError(str(exc)) from exc
    if action == "market.validate_offer":
        value = content.get("gross_margin")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not (
            0.0 <= float(value) <= 1.0
        ):
            raise EngineError("market.validate_offer gross_margin must be 0..1")


_TEXT2GAME_PAGE_LINEAGE_FIELDS = (
    "slug",
    "production_slug",
    "candidate_id",
    "candidate_version",
    "candidate_content_sha256",
    "rules_sha256",
    "rules_file_sha256",
    "vibe_idea_sha256",
    "project_sha256",
    "artifact_hashes",
    "text2game_source_artifact_hashes",
    "text2game_source_artifact_hashes_sha256",
    "text2game_export_receipt_sha256",
    "text2game_source_snapshot_sha256",
    "text2game_repo_url",
    "text2game_repo_commit",
)


def _validate_text2game_physical_receipt(
    action: str, content: Mapping[str, Any]
) -> None:
    lineage = content.get("page_builder_lineage")
    if not isinstance(lineage, Mapping) or set(lineage) != set(
        _TEXT2GAME_PAGE_LINEAGE_FIELDS
    ):
        raise EngineError(f"{action} page_builder_lineage fields are not exact")
    for key in _TEXT2GAME_PAGE_LINEAGE_FIELDS:
        if lineage.get(key) != content.get(key):
            raise EngineError(f"{action} page_builder_lineage {key} mismatch")
    hashes = content.get("validation_receipt_hashes")
    if not isinstance(hashes, Mapping) or not hashes:
        raise EngineError(f"{action} validation_receipt_hashes must be non-empty")
    for key, digest in hashes.items():
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise EngineError(f"{action} validation receipt hash is malformed")
    if not isinstance(content.get("receipt"), Mapping):
        raise EngineError(f"{action} receipt must be an object")
    operation_id = content.get("text2game_operation_id")
    if not isinstance(operation_id, str) or re.fullmatch(
        r"[0-9a-f]{32}", operation_id
    ) is None:
        raise EngineError(f"{action} text2game_operation_id is malformed")
    if action == "physical.dfm":
        if not isinstance(content.get("tolerances"), Mapping):
            raise EngineError("physical.dfm tolerances must be an object")
        if not isinstance(content.get("landed_cost"), Mapping):
            raise EngineError("physical.dfm landed_cost must be an object")


_RULE_FIELDS = (
    "setup",
    "turn",
    "legal_actions",
    "end",
    "scoring",
    "ties",
    "rules_markdown",
)


def _bind_agent_lineage(
    task: TaskRecord, content: Mapping[str, Any]
) -> dict[str, Any]:
    """Add hashes the runtime can compute itself instead of trusting a model."""

    result = dict(content)
    candidate_hash = task.payload.get("candidate_content_sha256")
    if task.kind == "candidate.rules":
        markdown = result.get("rules_markdown")
        if not isinstance(markdown, str) or not markdown.strip():
            raise EngineError("candidate.rules needs non-empty rules_markdown")
        rule_document = {name: result.get(name) for name in _RULE_FIELDS}
        result["candidate_content_sha256"] = candidate_hash
        result["rules_sha256"] = _canonical_sha256(rule_document)
    elif task.kind == "physical.design":
        result["candidate_id"] = task.candidate_id
        result["candidate_version"] = task.payload.get("candidate_version")
        result["candidate_content_sha256"] = candidate_hash
        result["rules_sha256"] = _accepted_lineage_value(
            task.payload, "candidate.rules", "rules_sha256"
        )
    return result


def _validate_task_lineage(task: TaskRecord, content: Mapping[str, Any]) -> None:
    if task.candidate_id is None:
        return
    actions_requiring_candidate = {
        "candidate.rules",
        "rules.lint",
        "rules.adversary",
        "simulation.optimizer",
        "simulation.social",
        "simulation.explorer",
        "simulation.exploit",
        "human.prepare_blind_kit",
        "human.collect_blind_results",
        "physical.design",
        "physical.cad",
        "physical.dfm",
        "physical.create_rich_draft",
        "physical.prototype_print",
        "physical.production_run",
        "market.validate_offer",
        "market.final_safety_ip",
    }
    if task.kind not in actions_requiring_candidate:
        return
    candidate_hash = task.payload.get("candidate_content_sha256")
    if content.get("candidate_content_sha256") != candidate_hash:
        raise EngineError(f"{task.kind} candidate content hash mismatch")
    if task.kind == "candidate.rules":
        expected_rules = _canonical_sha256(
            {name: content.get(name) for name in _RULE_FIELDS}
        )
    else:
        expected_rules = _accepted_lineage_value(
            task.payload, "candidate.rules", "rules_sha256"
        )
    if content.get("rules_sha256") != expected_rules:
        raise EngineError(f"{task.kind} rules hash mismatch")

    if task.kind == "physical.design":
        if content.get("candidate_id") != task.candidate_id:
            raise EngineError("physical.design candidate id mismatch")
        if content.get("candidate_version") != task.payload.get("candidate_version"):
            raise EngineError("physical.design candidate version mismatch")
        return

    if task.kind == "human.prepare_blind_kit":
        try:
            validate_blind_kit(
                content,
                expected_candidate_content_sha256=str(candidate_hash),
                expected_rules_sha256=str(expected_rules),
            )
        except ReleaseAssemblyError as exc:
            raise EngineError(str(exc)) from exc

    if task.kind == "human.collect_blind_results":
        expected_kit = _accepted_lineage_value(
            task.payload, "human.prepare_blind_kit", "blind_kit_sha256"
        )
        try:
            validate_blind_human_evidence(
                content,
                expected_candidate_content_sha256=str(candidate_hash),
                expected_rules_sha256=str(expected_rules),
                expected_blind_kit_sha256=str(expected_kit),
            )
        except ReleaseAssemblyError as exc:
            raise EngineError(str(exc)) from exc

    if task.kind == "physical.cad":
        design = _dependency_payload(task.payload, "physical.design")
        if not design:
            raise EngineError("physical.cad lacks its physical.design dependency")
        for key in (
            "candidate_id",
            "candidate_version",
            "candidate_content_sha256",
            "rules_sha256",
            "production_slug",
        ):
            if content.get(key) != design.get(key):
                raise EngineError(f"physical.cad does not match physical.design {key}")
        if content.get("physical_design_sha256") != _canonical_sha256(design):
            raise EngineError("physical.cad physical design hash mismatch")
        artifact_hashes = content.get("artifact_hashes")
        rules_file_hash = content.get("rules_file_sha256")
        if not isinstance(artifact_hashes, Mapping) or (
            artifact_hashes.get("RULES.md") != rules_file_hash
        ):
            raise EngineError("physical.cad must bind RULES.md in artifact_hashes")
        return

    if task.kind in {"physical.dfm", "physical.create_rich_draft"}:
        cad = _dependency_payload(task.payload, "physical.cad")
        for key in ("rules_file_sha256", "project_sha256", "artifact_hashes"):
            if content.get(key) != cad.get(key):
                raise EngineError(f"{task.kind} does not match physical.cad {key}")
        if task.kind == "physical.dfm":
            for key in (
                "candidate_id",
                "candidate_version",
                "candidate_content_sha256",
                "rules_sha256",
                "slug",
                "production_slug",
                "vibe_idea_sha256",
                "text2game_source_artifact_hashes",
                "text2game_source_artifact_hashes_sha256",
                "text2game_export_receipt_sha256",
                "text2game_source_snapshot_sha256",
                "text2game_repo_url",
                "text2game_repo_commit",
                "page_builder_lineage",
                "physical_design_sha256",
                "text2game_operation_id",
                "validation_receipt_hashes",
            ):
                if content.get(key) != cad.get(key):
                    raise EngineError(f"physical.dfm does not match physical.cad {key}")
        return

    if task.kind in {"physical.prototype_print", "physical.production_run"}:
        draft = _accepted_artifact_content(
            task.payload, "physical.create_rich_draft"
        )
        for key in ("rules_file_sha256", "project_sha256", "artifact_hashes"):
            if content.get(key) != draft.get(key):
                raise EngineError(f"{task.kind} does not match rich draft {key}")
        if task.kind == "physical.production_run":
            prototype = _dependency_payload(task.payload, "physical.prototype_print")
            try:
                validate_distinct_manufacturing_receipts(prototype, content)
            except ReleaseAssemblyError as exc:
                raise EngineError(str(exc)) from exc
            for key in (
                "candidate_content_sha256",
                "rules_sha256",
                "rules_file_sha256",
                "project_sha256",
                "artifact_hashes",
            ):
                if content.get(key) != prototype.get(key):
                    raise EngineError(
                        f"physical.production_run does not match prototype {key}"
                    )
        return

    if task.kind in {"market.validate_offer", "market.final_safety_ip"}:
        production = _accepted_artifact_content(
            task.payload, "physical.production_run"
        )
        for key in ("candidate_content_sha256", "rules_sha256"):
            if content.get(key) != production.get(key):
                raise EngineError(f"{task.kind} does not match production {key}")
        if task.kind == "market.validate_offer":
            for key in (
                "rules_file_sha256",
                "project_sha256",
                "artifact_hashes",
                "landed_cost_cents",
            ):
                if content.get(key) != production.get(key):
                    raise EngineError(f"market validation does not match production {key}")


def _accepted_artifact_content(
    payload: Mapping[str, Any], action: str
) -> Mapping[str, Any]:
    artifacts = payload.get("accepted_artifacts")
    if not isinstance(artifacts, list):
        raise EngineError("candidate task has no accepted artifact context")
    matches = [
        item
        for item in artifacts
        if isinstance(item, Mapping)
        and item.get("action") == action
        and isinstance(item.get("content"), Mapping)
    ]
    if not matches:
        raise EngineError(f"candidate task lacks accepted {action} artifact")
    latest = sorted(
        matches,
        key=lambda item: (
            int(item.get("candidate_version") or 0),
            str(item.get("task_id") or ""),
        ),
    )[-1]
    content = latest.get("content")
    assert isinstance(content, Mapping)
    return content


def _accepted_lineage_value(
    payload: Mapping[str, Any], action: str, key: str
) -> str:
    value = _accepted_artifact_content(payload, action).get(key)
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise EngineError(f"accepted {action} artifact lacks {key}")
    return value


def _dependency_payload(
    payload: Mapping[str, Any], action: str
) -> Mapping[str, Any]:
    dependencies = payload.get("dependencies")
    dependency = dependencies.get(action) if isinstance(dependencies, Mapping) else None
    result = dependency.get("result") if isinstance(dependency, Mapping) else None
    content, _, _ = _result_content_provenance(result)
    return content


def _validate_3d_game_candidate(candidate: Mapping[str, Any]) -> None:
    if not isinstance(candidate.get("title"), str) or not candidate["title"].strip():
        raise EngineError("selected candidate needs a title")
    components = candidate.get("components")
    if not isinstance(components, list) or not components:
        raise EngineError("selected candidate needs physical components")
    for component in components:
        if not isinstance(component, dict):
            raise EngineError("candidate components must be objects")
        manufacturing = component.get("manufacturing")
        if not isinstance(manufacturing, dict) or manufacturing.get("process") != "3d_print":
            raise EngineError("every Alice component must declare manufacturing.process=3d_print")


def _priority(item: WorkItem) -> int:
    return {
        "orders": 100,
        "send": 90,
        "publish": 90,
        "human": 70,
        "physical": 60,
        "playtest": 50,
        "candidate": 40,
        "history": 35,
        "library": 35,
        "invention": 30,
        "learning": 20,
        "meta": 5,
    }.get(item.loop, 0)


def _retry_delay(attempt_count: int) -> float:
    return min(3_600.0, 30.0 * (2 ** max(0, attempt_count - 1)))


def _compact_knowledge_content(value: Any, *, max_bytes: int = 8_000) -> Any:
    """Keep cross-loop context bounded while preserving a durable hash."""

    encoded = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    if len(encoded.encode("utf-8")) <= max_bytes:
        return value
    summary = value.get("summary") if isinstance(value, Mapping) else None
    return {
        "summary": summary if isinstance(summary, str) else "Large result omitted",
        "content_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "truncated": True,
    }


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _result_content_provenance(
    result: Any,
) -> tuple[Mapping[str, Any], str, str]:
    if not isinstance(result, Mapping):
        raise EngineError("task result is not a structured object")
    executor = result.get("executor")
    if executor == "adapter":
        receipt = result.get("receipt")
        if not isinstance(receipt, Mapping) or receipt.get("status") != "passed":
            raise EngineError("candidate artifact adapter receipt is not passed")
        content = receipt.get("payload")
        evidence_class = receipt.get("evidence_class")
    elif executor == "agent":
        response = result.get("response")
        content = response.get("content") if isinstance(response, Mapping) else None
        evidence_class = "same_model"
    elif executor == "release_policy":
        content = result.get("content")
        evidence_class = "release_policy"
    elif executor == "learning_policy":
        content = result.get("content")
        evidence_class = "deterministic"
    else:
        raise EngineError(f"unknown task result executor {executor!r}")
    if not isinstance(content, Mapping):
        raise EngineError("task result content is not an object")
    if not isinstance(evidence_class, str) or not evidence_class:
        raise EngineError("task result has no evidence class")
    return content, str(executor), evidence_class


def _stage_gate_failure(
    state: str,
    artifacts: list[ArtifactSnapshot],
    config: Mapping[str, Any],
) -> dict[str, Any] | None:
    content = {
        canonical_task_kind(artifact.action): artifact.content
        for artifact in artifacts
    }
    failures: list[str] = []
    if state == "proposed":
        safety = content["candidate.safety_ip"]
        if safety.get("critical_safety_findings") != 0:
            failures.append("critical_safety_finding_open")
        if safety.get("critical_ip_findings") != 0:
            failures.append("critical_ip_finding_open")
        prior = content["candidate.prior_art"]
        if not prior.get("citations") or not prior.get("material_differences"):
            failures.append("prior_art_not_substantiated")
    elif state == "researched":
        lint = content["rules.lint"]
        adversary = content["rules.adversary"]
        if lint.get("rules_complete") is not True:
            failures.append("rules_incomplete")
        if lint.get("terminates") is not True:
            failures.append("termination_not_proven")
        if lint.get("ambiguities"):
            failures.append("rules_ambiguity_open")
        if adversary.get("critical_exploits") != 0:
            failures.append("critical_exploit_open")
    elif state == "rules_valid":
        exploit = content["simulation.exploit"]
        optimizer = content["simulation.optimizer"]
        if exploit.get("critical_exploits") not in (0, [], None):
            failures.append("simulation_critical_exploit_open")
        if optimizer.get("dominant_strategy") not in {False, None, "none"}:
            failures.append("dominant_strategy_found")
    elif state == "human_ready":
        human = content["human.collect_blind_results"]
        quality = config["quality"]
        if human.get("blind_groups", 0) < int(quality["minimum_blind_groups"]):
            failures.append("insufficient_blind_groups")
        if human.get("minimum_games_per_group", 0) < int(
            quality["minimum_games_per_group"]
        ):
            failures.append("insufficient_games_per_group")
        if human.get("designer_hints_required") != 0:
            failures.append("designer_hints_required")
    elif state == "human_validated":
        dfm = content["physical.dfm"]
        rich_draft = content["physical.create_rich_draft"]
        if not dfm.get("artifact_hashes") or not dfm.get("receipt"):
            failures.append("dfm_receipt_missing")
        if dfm.get("fit") is False:
            failures.append("dfm_fit_failed")
        if rich_draft.get("status") != "draft":
            failures.append("rich_page_is_not_private_draft")
        if not rich_draft.get("history_id") or not rich_draft.get("project_url"):
            failures.append("rich_page_history_missing")
        if rich_draft.get("artifact_hashes") != dfm.get("artifact_hashes"):
            failures.append("rich_page_artifact_mismatch")
    elif state == "physical_ready":
        production = content["physical.production_run"]
        manifest = production.get("production_manifest")
        expected_hash = production.get("production_packet_hash")
        if not isinstance(manifest, Mapping) or not isinstance(expected_hash, str):
            failures.append("production_manifest_missing")
        elif _canonical_sha256(manifest) != expected_hash:
            failures.append("production_manifest_hash_mismatch")
        if production.get("reviewed_packet_hash") != expected_hash:
            failures.append("production_review_hash_mismatch")
        try:
            validate_manufacturing_receipt(
                production, "physical.production_run"
            )
        except ReleaseAssemblyError:
            failures.append("real_print_receipt_invalid")
    elif state == "production_validated":
        decision = content["release.evaluate"]
        if decision.get("allowed") is not True:
            failures.extend(
                str(item) for item in decision.get("failures", ["release_denied"])
            )
    elif state in {"publish_ready", "page_ready"}:
        terminal = (
            content.get(SEND_TO_SHOP)
            if state == "publish_ready"
            else content.get(SEND_VERIFY_SHOP)
        )
        if not isinstance(terminal, Mapping):
            failures.append("shop_door_stamp_missing")
    if not failures:
        return None
    return {"codes": sorted(set(failures)), "state": state}


def _required_effect_mode(action: str) -> str | None:
    """Return the minimum mode allowed to run a mutating operation."""

    action = canonical_task_kind(action)
    if action in {
        "release.evaluate",
        PACK_PRODUCT,
        "publish.effect",
        SEND_TO_SHOP,
        "orders.poll_paid",
        "orders.create_print_job",
        "orders.qa_ship",
        "orders.outcome",
    }:
        return "live"
    if action in {
        "physical.cad",
        "physical.dfm",
        "physical.create_rich_draft",
        "physical.prototype_print",
        "physical.production_run",
    }:
        return "draft"
    return None


def _canonical_adapter_map(adapters: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize old configured adapter keys without exposing them as current."""

    normalized = dict(adapters)
    for legacy, current in _LEGACY_ADAPTER_KEYS.items():
        if legacy not in normalized:
            continue
        if current in normalized and normalized[current] is not normalized[legacy]:
            raise EngineError(
                f"adapter keys {current!r} and its legacy alias {legacy!r} conflict"
            )
        normalized.setdefault(current, normalized[legacy])
        del normalized[legacy]
    return normalized


def _tasks_by_current_kind(tasks: Any) -> dict[str, TaskRecord]:
    """Index current and durable legacy tasks under the current work-graph name."""

    result: dict[str, TaskRecord] = {}
    for task in tasks:
        current = canonical_task_kind(task.kind)
        existing = result.get(current)
        if existing is not None and existing.id != task.id:
            raise EngineError(
                f"run contains both current and legacy forms of {current!r}"
            )
        result[current] = task
    return result


class _LeaseHeartbeat:
    """Renew one task lease while a blocking provider or adapter is running."""

    def __init__(
        self,
        store: DurableStore,
        task_id: str,
        worker_id: str,
        lease_token: str,
        lease_seconds: float,
    ) -> None:
        self.store = store
        self.task_id = task_id
        self.worker_id = worker_id
        self.lease_token = lease_token
        self.lease_seconds = lease_seconds
        self.interval_seconds = max(0.01, min(60.0, lease_seconds / 3.0))
        self._stop = threading.Event()
        self._error: Exception | None = None
        self._thread = threading.Thread(
            target=self._run,
            name=f"alice-lease-{task_id[:8]}",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5.0)
        if self._thread.is_alive() and self._error is None:
            self._error = EngineError("lease heartbeat did not stop")

    def raise_if_failed(self) -> None:
        if self._error is not None:
            raise self._error

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            try:
                self.store.renew_task_lease(
                    self.task_id,
                    self.worker_id,
                    self.lease_token,
                    lease_seconds=self.lease_seconds,
                    now=time.time(),
                )
            except Exception as exc:
                self._error = exc
                self._stop.set()
                return


def _required_adapter_name(action: str) -> str | None:
    action = canonical_task_kind(action)
    if action == "library.read":
        return "library"
    if action in {"history.scan_traditional", "history.scan_modern"}:
        return "history"
    if action in {
        "concept.prior_art",
        "candidate.prior_art",
        "candidate.safety_ip",
        "market.final_safety_ip",
    }:
        return "research"
    if action in {"rules.lint", "rules.adversary"}:
        return "rules_validator"
    if action.startswith("simulation."):
        return "digital_playtest"
    if action in {"human.prepare_blind_kit", "human.collect_blind_results"}:
        return "human_playtest"
    if action in {"physical.cad", "physical.dfm"}:
        return "cad"
    if action == "physical.create_rich_draft":
        return "page_builder"
    if action in {"physical.prototype_print", "physical.production_run"}:
        return "print_fulfillment"
    if action == "orders.poll_paid":
        return "delivery"
    if action.startswith("orders."):
        return "print_fulfillment"
    if action in {SEND_TO_SHOP, SEND_VERIFY_SHOP}:
        return "shop_door"
    if action == "market.validate_offer":
        return "market_validation"
    if action == "outcomes.ingest":
        return "outcomes"
    return None


def _required_evidence_class(action: str) -> str | None:
    legacy_action = action
    action = canonical_task_kind(action)
    if action in {
        "concept.prior_art",
        "candidate.prior_art",
        "candidate.safety_ip",
        "market.final_safety_ip",
    }:
        return "independent_model"
    if action in {"library.read", "history.scan_traditional", "history.scan_modern"}:
        return "deterministic"
    if action in {"rules.lint", "rules.adversary"}:
        return "deterministic"
    if action.startswith("simulation."):
        return "simulation"
    if action in {"human.prepare_blind_kit", "human.collect_blind_results"}:
        return "blind_human"
    if action in {
        "physical.cad",
        "physical.dfm",
        "physical.prototype_print",
        "physical.production_run",
        "orders.create_print_job",
        "orders.qa_ship",
        "orders.outcome",
    }:
        return "manufacturing"
    if legacy_action in {
        "publish.invoke_pipeline",
        "publish.verify_page",
    }:
        return "publishing_pipeline"
    if action == "physical.create_rich_draft":
        return "shop_door"
    if action in {SEND_TO_SHOP, SEND_VERIFY_SHOP}:
        return "shop_door"
    if action in {"market.validate_offer", "orders.poll_paid"}:
        return "market"
    if action == "outcomes.ingest":
        return "external"
    return None
