"""Public, stage-scoped identity for the effective Workshop engine.

The Workshop is assembled from five common components.  This module describes
the *effective* component selected for each stage without serializing a live
provider, a credential, a filesystem path, or arbitrary object state.

Each stage has its own digest.  The ordered whole-engine digest is deliberately
named ``informational_engine_sha256``: it is useful in Doctor and status output,
but it is not a resume fence.  Resume compatibility protects only stages whose
results have been accepted, plus stages whose external effect may already have
started.  Consequently a missing provider can be installed for an incomplete,
explicitly no-effect waiting stage without invalidating completed work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import types
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .errors import ContractError
from .models import require_exact_version, require_sha256


WORKSHOP_STAGES = ("invent", "make", "playtest", "instructions", "deliver")
DEPENDENCY_KINDS = ("models", "prompts", "rewards", "toolchains", "services")
COMPONENT_STATES = ("missing", "configured", "custom")
MANIFEST_COMPLETENESS = ("complete", "opaque")
DEFAULT_STAGE_PROVIDER_IDS = {
    "invent": "workshop.codex-inventor-v1",
    "make": "workshop.codex-maker-v1",
    "playtest": "workshop.lane-aware-playtester-v1",
    "instructions": "workshop.rewarded-instructions-v1",
    "deliver": "workshop.default-deliver-v1",
}

_PUBLIC_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,511}$")
_MAX_SKILL_LOCK_BYTES = 1024 * 1024


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("engine provenance must be finite JSON") from exc


def _json_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _public_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or _PUBLIC_ID.fullmatch(value) is None:
        raise ContractError("%s must be a bounded public identifier" % label)
    return value


def _stage(value: Any) -> str:
    if value not in WORKSHOP_STAGES:
        raise ContractError("engine provenance stage is invalid")
    return value


def _kind(value: Any) -> str:
    if value not in DEPENDENCY_KINDS:
        raise ContractError("engine provenance dependency kind is invalid")
    return value


def _implementation_id(component: Any) -> str:
    """Return a bounded type/function label without inspecting provider state."""

    if component is None:
        raise ContractError("a missing component has no implementation identity")
    if isinstance(component, types.MethodType):
        function = object.__getattribute__(component, "__func__")
        module = object.__getattribute__(function, "__module__")
        qualname = object.__getattribute__(function, "__qualname__")
    elif isinstance(
        component,
        (types.FunctionType, types.BuiltinFunctionType),
    ):
        module = object.__getattribute__(component, "__module__")
        qualname = object.__getattribute__(component, "__qualname__")
    else:
        target = type(component)
        module = type.__getattribute__(target, "__module__")
        qualname = type.__getattribute__(target, "__qualname__")
    raw = "%s.%s" % (module, qualname)
    if isinstance(module, str) and isinstance(qualname, str) and _PUBLIC_ID.fullmatch(raw):
        return raw
    # Local functions contain angle brackets and may disclose an unbounded
    # name.  Preserve a stable diagnostic distinction without publishing it.
    return "python-callable.%s" % hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _scoped_implementation_id(scope: str, implementation_id: str) -> str:
    """Prefix an implementation identity without exceeding public-id bounds."""

    raw = "%s.%s" % (scope, implementation_id)
    if _PUBLIC_ID.fullmatch(raw):
        return raw
    return "%s.sha256-%s" % (
        scope,
        hashlib.sha256(implementation_id.encode("utf-8")).hexdigest(),
    )


@dataclass(frozen=True)
class PublicDependency:
    """One public dependency identity; never a live dependency object."""

    kind: str
    name: str
    state: str
    version: Optional[str] = None
    config_sha256: Optional[str] = None

    def __post_init__(self) -> None:
        _kind(self.kind)
        _public_id(self.name, "engine dependency name")
        if self.state not in COMPONENT_STATES:
            raise ContractError("engine dependency state is invalid")
        if self.state == "missing":
            if self.version is not None or self.config_sha256 is not None:
                raise ContractError("a missing dependency cannot claim an identity")
        else:
            require_exact_version(self.version, "engine dependency version")
            require_sha256(
                self.config_sha256, "engine dependency config sha256"
            )

    @classmethod
    def configured(
        cls, kind: str, name: str, version: str, config_sha256: str
    ) -> "PublicDependency":
        return cls(kind, name, "configured", version, config_sha256)

    @classmethod
    def custom(
        cls, kind: str, name: str, version: str, config_sha256: str
    ) -> "PublicDependency":
        return cls(kind, name, "custom", version, config_sha256)

    @classmethod
    def missing(cls, kind: str, name: str) -> "PublicDependency":
        return cls(kind, name, "missing")

    @classmethod
    def from_public_identity(
        cls,
        kind: str,
        identity: Mapping[str, Any],
        *,
        state: str = "configured",
        name: Optional[str] = None,
    ) -> "PublicDependency":
        if not isinstance(identity, Mapping) or set(identity) != {
            "provider_id",
            "version",
            "config_sha256",
        }:
            raise ContractError("engine service identity must have an exact public shape")
        selected_name = identity["provider_id"] if name is None else name
        return cls(
            kind,
            selected_name,
            state,
            identity["version"],
            identity["config_sha256"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "version": self.version,
            "config_sha256": self.config_sha256,
        }

    @classmethod
    def from_dict(cls, kind: str, value: Any) -> "PublicDependency":
        if not isinstance(value, Mapping) or set(value) != {
            "name",
            "state",
            "version",
            "config_sha256",
        }:
            raise ContractError("engine dependency manifest is malformed")
        return cls(
            kind,
            value["name"],
            value["state"],
            value["version"],
            value["config_sha256"],
        )


def _ordered_dependencies(
    dependencies: Iterable[PublicDependency],
) -> Tuple[PublicDependency, ...]:
    selected = tuple(dependencies)
    if not all(isinstance(item, PublicDependency) for item in selected):
        raise ContractError("engine dependencies must be public dependency manifests")
    order = {kind: index for index, kind in enumerate(DEPENDENCY_KINDS)}
    sorted_dependencies = tuple(
        sorted(selected, key=lambda item: (order[item.kind], item.name))
    )
    identities = [(item.kind, item.name) for item in sorted_dependencies]
    if len(identities) != len(set(identities)):
        raise ContractError("engine dependency identities must be unique per kind")
    return sorted_dependencies


@dataclass(frozen=True)
class StageComponentManifest:
    """Secret-free identity of one effective Workshop stage component."""

    stage: str
    state: str
    manifest_completeness: str
    provider_id: Optional[str]
    implementation_id: Optional[str]
    configuration_sha256: Optional[str]
    dependencies: Tuple[PublicDependency, ...] = ()
    schema_version: int = 1
    stage_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("stage component schema_version must be 1")
        _stage(self.stage)
        if self.state not in COMPONENT_STATES:
            raise ContractError("stage component state is invalid")
        if self.manifest_completeness not in MANIFEST_COMPLETENESS:
            raise ContractError("stage component completeness is invalid")
        dependencies = _ordered_dependencies(self.dependencies)
        object.__setattr__(self, "dependencies", dependencies)
        if self.state == "missing":
            if (
                self.provider_id is not None
                or self.implementation_id is not None
                or self.configuration_sha256 is not None
                or dependencies
                or self.manifest_completeness != "complete"
            ):
                raise ContractError("a missing stage cannot claim component identity")
        else:
            _public_id(self.provider_id, "stage provider id")
            _public_id(self.implementation_id, "stage implementation id")
            require_sha256(
                self.configuration_sha256, "stage configuration sha256"
            )
        object.__setattr__(self, "stage_sha256", _json_sha256(self._identity_dict()))

    @classmethod
    def missing(cls, stage: str) -> "StageComponentManifest":
        return cls(stage, "missing", "complete", None, None, None)

    def _identity_dict(self) -> Dict[str, Any]:
        grouped = {
            kind: [
                dependency.to_dict()
                for dependency in self.dependencies
                if dependency.kind == kind
            ]
            for kind in DEPENDENCY_KINDS
        }
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "state": self.state,
            "manifest_completeness": self.manifest_completeness,
            "provider_id": self.provider_id,
            "implementation_id": self.implementation_id,
            "configuration_sha256": self.configuration_sha256,
            "dependencies": grouped,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {**self._identity_dict(), "stage_sha256": self.stage_sha256}

    @classmethod
    def from_dict(cls, value: Any) -> "StageComponentManifest":
        if not isinstance(value, Mapping) or set(value) != {
            "schema_version",
            "stage",
            "state",
            "manifest_completeness",
            "provider_id",
            "implementation_id",
            "configuration_sha256",
            "dependencies",
            "stage_sha256",
        }:
            raise ContractError("stage component manifest is malformed")
        raw_dependencies = value["dependencies"]
        if not isinstance(raw_dependencies, Mapping) or set(raw_dependencies) != set(
            DEPENDENCY_KINDS
        ):
            raise ContractError("stage component dependency groups are malformed")
        dependencies = []
        for kind in DEPENDENCY_KINDS:
            records = raw_dependencies[kind]
            if not isinstance(records, list):
                raise ContractError("stage component dependency group must be a list")
            dependencies.extend(
                PublicDependency.from_dict(kind, record) for record in records
            )
        manifest = cls(
            value["stage"],
            value["state"],
            value["manifest_completeness"],
            value["provider_id"],
            value["implementation_id"],
            value["configuration_sha256"],
            tuple(dependencies),
            value["schema_version"],
        )
        require_sha256(value["stage_sha256"], "persisted stage sha256")
        if manifest.stage_sha256 != value["stage_sha256"]:
            raise ContractError("stage component manifest digest is inconsistent")
        return manifest


@dataclass(frozen=True)
class EngineProvenanceManifest:
    """Exactly five stage manifests and one non-authoritative overview digest."""

    components: Tuple[StageComponentManifest, ...]
    schema_version: int = 1
    informational_engine_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("engine provenance schema_version must be 1")
        components = tuple(self.components)
        if (
            not all(isinstance(item, StageComponentManifest) for item in components)
            or tuple(item.stage for item in components) != WORKSHOP_STAGES
        ):
            raise ContractError("engine provenance must describe all five stages in order")
        object.__setattr__(self, "components", components)
        digest = _json_sha256(
            {
                "schema_version": self.schema_version,
                "ordered_stage_sha256": [
                    {"stage": item.stage, "stage_sha256": item.stage_sha256}
                    for item in components
                ],
            }
        )
        object.__setattr__(self, "informational_engine_sha256", digest)

    def component(self, stage: str) -> StageComponentManifest:
        selected = _stage(stage)
        return self.components[WORKSHOP_STAGES.index(selected)]

    @property
    def stage_sha256(self) -> Dict[str, str]:
        return {item.stage: item.stage_sha256 for item in self.components}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "components": [item.to_dict() for item in self.components],
            "informational_engine_sha256": self.informational_engine_sha256,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "EngineProvenanceManifest":
        if not isinstance(value, Mapping) or set(value) != {
            "schema_version",
            "components",
            "informational_engine_sha256",
        }:
            raise ContractError("engine provenance manifest is malformed")
        records = value["components"]
        if not isinstance(records, list):
            raise ContractError("engine provenance components must be a list")
        manifest = cls(
            tuple(StageComponentManifest.from_dict(item) for item in records),
            value["schema_version"],
        )
        require_sha256(
            value["informational_engine_sha256"],
            "persisted informational engine sha256",
        )
        if manifest.informational_engine_sha256 != value["informational_engine_sha256"]:
            raise ContractError("informational engine digest is inconsistent")
        return manifest


@dataclass(frozen=True)
class ResumeEngineCompatibility:
    """Result of comparing stage-scoped provenance for one resume."""

    protected_stages: Tuple[str, ...]
    changed_stages: Tuple[str, ...]
    informational_engine_changed: bool


def compare_engine_for_resume(
    recorded: EngineProvenanceManifest,
    current: EngineProvenanceManifest,
    *,
    completed_stages: Iterable[str],
    effect_started_stages: Iterable[str] = (),
) -> ResumeEngineCompatibility:
    """Fence accepted/effectful stages while permitting safe provider additions.

    A stage omitted from both ``completed_stages`` and ``effect_started_stages``
    is incomplete and has no possibly-committed external effect.  Its provider
    may therefore be added or rotated.  Callers must put an ambiguous/working
    stage in ``effect_started_stages``; Deliver in particular becomes protected
    as soon as its durable working event is written.
    """

    if not isinstance(recorded, EngineProvenanceManifest) or not isinstance(
        current, EngineProvenanceManifest
    ):
        raise ContractError("resume provenance requires two engine manifests")
    completed = tuple(completed_stages)
    effect_started = tuple(effect_started_stages)
    if len(completed) != len(set(completed)) or len(effect_started) != len(
        set(effect_started)
    ):
        raise ContractError("resume provenance stage sets must be unique")
    for stage in (*completed, *effect_started):
        _stage(stage)
    protected_set = set(completed) | set(effect_started)
    protected = tuple(stage for stage in WORKSHOP_STAGES if stage in protected_set)
    changed = tuple(
        stage
        for stage in WORKSHOP_STAGES
        if recorded.component(stage).stage_sha256
        != current.component(stage).stage_sha256
    )
    incompatible = tuple(stage for stage in changed if stage in protected_set)
    if incompatible:
        raise ContractError(
            "effective Workshop component changed for protected stage(s): %s"
            % ", ".join(incompatible)
        )
    return ResumeEngineCompatibility(
        protected,
        changed,
        recorded.informational_engine_sha256
        != current.informational_engine_sha256,
    )


def _identity_dependency(
    kind: str, name: str, version: str, configuration: Any
) -> PublicDependency:
    return PublicDependency.configured(
        kind, name, version, _json_sha256(configuration)
    )


def _model_dependency(role: str, runner: Any) -> PublicDependency:
    model = object.__getattribute__(runner, "model")
    reasoning_effort = object.__getattribute__(runner, "reasoning_effort")
    cli_version = object.__getattribute__(runner, "cli_version")
    name = "codex-%s-%s" % (role, model)
    return _identity_dependency(
        "models",
        name,
        cli_version,
        {
            "model": model,
            "reasoning_effort": reasoning_effort,
            "cli_version": cli_version,
        },
    )


def _skill_lock_dependencies(builder: Any) -> Tuple[PublicDependency, ...]:
    """Read only declared public skill-tree hashes; never provider paths."""

    from .agent_make import LockedCadSkillBuilder

    if type(builder) is not LockedCadSkillBuilder:
        return ()
    root = Path(object.__getattribute__(builder, "skills_root"))
    path = root / "LOCK.json"
    descriptor = None
    try:
        expected = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(expected.st_mode)
            or expected.st_size > _MAX_SKILL_LOCK_BYTES
        ):
            raise OSError("unsafe skill lock")
        descriptor = os.open(
            path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        )
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino)
            != (expected.st_dev, expected.st_ino)
            or opened.st_size != expected.st_size
        ):
            raise OSError("skill lock changed")
        chunks = []
        observed = 0
        while True:
            chunk = os.read(descriptor, 64 * 1024)
            if not chunk:
                break
            observed += len(chunk)
            if observed > _MAX_SKILL_LOCK_BYTES:
                raise OSError("skill lock is too large")
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
        ):
            raise OSError("skill lock changed")
        raw = b"".join(chunks)

        def exact_object(pairs: list[tuple[str, Any]]) -> Dict[str, Any]:
            selected: Dict[str, Any] = {}
            for key, value in pairs:
                if key in selected:
                    raise ValueError("duplicate skill lock key")
                selected[key] = value
            return selected

        document = json.loads(
            raw.decode("utf-8"), object_pairs_hook=exact_object
        )
        skills = document["skills"]
    except (KeyError, OSError, UnicodeError, json.JSONDecodeError, TypeError) as exc:
        raise ContractError("Workshop CAD skill lock is missing or malformed") from exc
    except ValueError as exc:
        raise ContractError("Workshop CAD skill lock is missing or malformed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    dependencies = []
    for name in ("cad", "product-to-cad"):
        value = skills.get(name) if isinstance(skills, Mapping) else None
        if not isinstance(value, Mapping):
            raise ContractError("Workshop CAD skill lock is incomplete")
        digest = require_sha256(value.get("sha256"), "Workshop skill sha256")
        dependencies.append(
            PublicDependency.configured(
                "toolchains", "workshop-skill-%s" % name, "1.0.0", digest
            )
        )
    return tuple(dependencies)


@dataclass(frozen=True)
class _KnownDescription:
    provider_id: str
    implementation_id: str
    configuration_sha256: str
    dependencies: Tuple[PublicDependency, ...]
    complete: bool = True


def _reward_loop_policy(component: Any) -> Dict[str, int]:
    """Return the public controls that govern a known reward loop."""

    return {
        "goal": object.__getattribute__(component, "goal"),
        "max_steps_per_batch": object.__getattribute__(component, "max_steps"),
        "max_total_steps": object.__getattribute__(component, "max_total_steps"),
        "max_elapsed_seconds": object.__getattribute__(
            component, "max_elapsed_seconds"
        ),
    }


def _describe_known_component(
    stage: str,
    component: Any,
    explicit_services: Tuple[PublicDependency, ...],
) -> Optional[_KnownDescription]:
    """Describe only allowlisted Workshop implementations and public fields."""

    from .agent_instructions import RewardedInstructions
    from .agent_invent import CodexInventor, PublicHTTPResearchProvider
    from .agent_make import CodexMaker, MAKE_GENERATOR_ID, MAKE_GENERATOR_VERSION
    from .agent_playtest import (
        LaneAwarePlaytester,
        PRUSASLICER_VERSION,
        _WORKSHOP_PRUSA_PROFILES,
        default_sealed_game_simulator,
    )
    from .deliver import DefaultDeliver
    from .invented_game import (
        GAME_SIMULATOR_ID,
        GAME_SIMULATOR_SOURCE,
        GAME_SIMULATOR_VERSION,
    )
    from .lane_playtest_providers import (
        PinnedCheckersRulesProvider,
        SealedInventScienceEvidenceProvider,
        WorkshopLanePlaytestProviders,
    )
    from .moving_machine import (
        MOVING_MACHINE_CHECKER_VERSION,
        WorkshopMovingMachineVerifier,
    )

    implementation = _implementation_id(component)
    if stage == "invent" and type(component) is CodexInventor:
        creator = object.__getattribute__(component, "creator")
        evaluator = object.__getattribute__(component, "evaluator")
        creator_config = object.__getattribute__(component, "creator_config_sha256")
        reward_config = object.__getattribute__(component, "reward_config_sha256")
        dependencies = [
            _model_dependency("invent-creator", creator),
            _model_dependency("invent-reward", evaluator),
            PublicDependency.configured(
                "prompts",
                "workshop-invent-creator",
                object.__getattribute__(component, "creator_version"),
                creator_config,
            ),
            PublicDependency.configured(
                "rewards",
                "workshop-invent-reward",
                object.__getattribute__(component, "evaluator_version"),
                reward_config,
            ),
            PublicDependency.configured(
                "toolchains",
                GAME_SIMULATOR_ID,
                GAME_SIMULATOR_VERSION,
                hashlib.sha256(GAME_SIMULATOR_SOURCE.encode("utf-8")).hexdigest(),
            ),
        ]
        complete = True
        dependencies.extend(explicit_services)
        has_declared_research = any(
            item.name.startswith("research.") for item in explicit_services
        )
        if not has_declared_research:
            research = object.__getattribute__(component, "research_provider")
            if type(research) is PublicHTTPResearchProvider:
                dependencies.append(
                    PublicDependency.configured(
                        "services",
                        object.__getattribute__(research, "provider"),
                        object.__getattribute__(research, "provider_version"),
                        object.__getattribute__(research, "provider_config_sha256"),
                    )
                )
            elif research is None:
                dependencies.append(
                    PublicDependency.missing(
                        "services", "source-backed-design-research"
                    )
                )
            else:
                opaque_id = _implementation_id(research)
                dependencies.append(
                    _identity_dependency(
                        "services", opaque_id, "1.0.0", {"implementation": opaque_id}
                    )
                )
                complete = False
        return _KnownDescription(
            DEFAULT_STAGE_PROVIDER_IDS["invent"],
            implementation,
            _json_sha256(
                {
                    "creator_config_sha256": creator_config,
                    "reward_config_sha256": reward_config,
                    "reward_loop_policy": _reward_loop_policy(component),
                }
            ),
            _ordered_dependencies(dependencies),
            complete,
        )

    if stage == "make" and type(component) is CodexMaker:
        creator = object.__getattribute__(component, "creator")
        evaluator = object.__getattribute__(component, "evaluator")
        creator_config = object.__getattribute__(component, "creator_config_sha256")
        reward_config = object.__getattribute__(component, "reward_config_sha256")
        cad_builder = object.__getattribute__(component, "cad_builder")
        skill_dependencies = _skill_lock_dependencies(cad_builder)
        dependencies = [
            _model_dependency("make-creator", creator),
            _model_dependency("make-reward", evaluator),
            PublicDependency.configured(
                "prompts",
                "workshop-make-creator",
                object.__getattribute__(component, "creator_version"),
                creator_config,
            ),
            PublicDependency.configured(
                "rewards",
                "workshop-make-reward",
                object.__getattribute__(component, "evaluator_version"),
                reward_config,
            ),
            _identity_dependency(
                "toolchains",
                MAKE_GENERATOR_ID,
                MAKE_GENERATOR_VERSION,
                {"id": MAKE_GENERATOR_ID, "version": MAKE_GENERATOR_VERSION},
            ),
            *skill_dependencies,
            *explicit_services,
        ]
        complete = bool(skill_dependencies)
        if not skill_dependencies:
            opaque_id = _implementation_id(cad_builder)
            dependencies.append(
                PublicDependency.custom(
                    "toolchains",
                    opaque_id,
                    "1.0.0",
                    _json_sha256({"implementation": opaque_id}),
                )
            )
        return _KnownDescription(
            DEFAULT_STAGE_PROVIDER_IDS["make"],
            implementation,
            _json_sha256(
                {
                    "creator_config_sha256": creator_config,
                    "reward_config_sha256": reward_config,
                    "reward_loop_policy": _reward_loop_policy(component),
                }
            ),
            _ordered_dependencies(dependencies),
            complete,
        )

    if stage == "playtest" and type(component) is LaneAwarePlaytester:
        evaluator = object.__getattribute__(component, "evaluator")
        config = object.__getattribute__(component, "config_sha256")
        game_count = object.__getattribute__(component, "game_count")
        profile_hashes = {
            name: hashlib.sha256(value).hexdigest()
            for name, value in sorted(_WORKSHOP_PRUSA_PROFILES.items())
        }
        dependencies = [
            _model_dependency("playtest-evaluator", evaluator),
            PublicDependency.configured(
                "prompts",
                "workshop-playtest-evaluator",
                object.__getattribute__(component, "evaluator_version"),
                config,
            ),
            PublicDependency.configured(
                "rewards",
                "workshop-playtest-release",
                object.__getattribute__(component, "evaluator_version"),
                config,
            ),
            _identity_dependency(
                "toolchains",
                "workshop-prusaslicer",
                PRUSASLICER_VERSION,
                {"version": PRUSASLICER_VERSION, "profiles": profile_hashes},
            ),
            *explicit_services,
        ]
        complete = True

        game_simulator = object.__getattribute__(component, "game_simulator")
        if game_simulator is default_sealed_game_simulator:
            dependencies.append(
                PublicDependency.configured(
                    "toolchains",
                    GAME_SIMULATOR_ID,
                    GAME_SIMULATOR_VERSION,
                    hashlib.sha256(
                        GAME_SIMULATOR_SOURCE.encode("utf-8")
                    ).hexdigest(),
                )
            )
        elif game_simulator is None:
            dependencies.append(
                PublicDependency.missing("toolchains", GAME_SIMULATOR_ID)
            )
        else:
            simulator_id = _implementation_id(game_simulator)
            dependencies.append(
                PublicDependency.custom(
                    "toolchains",
                    _scoped_implementation_id("game-simulator", simulator_id),
                    "1.0.0",
                    _json_sha256({"implementation": simulator_id}),
                )
            )
            complete = False

        moving_verifier = object.__getattribute__(
            component, "moving_machine_verifier"
        )
        if type(moving_verifier) is WorkshopMovingMachineVerifier:
            dependencies.append(
                _identity_dependency(
                    "toolchains",
                    "workshop-moving-machine-verifier",
                    MOVING_MACHINE_CHECKER_VERSION,
                    {
                        "checker_version": MOVING_MACHINE_CHECKER_VERSION,
                        "method": "deterministic-rigid-primitive-motion",
                    },
                )
            )
        else:
            verifier_id = _implementation_id(moving_verifier)
            dependencies.append(
                PublicDependency.custom(
                    "toolchains",
                    _scoped_implementation_id(
                        "moving-machine-verifier", verifier_id
                    ),
                    "1.0.0",
                    _json_sha256({"implementation": verifier_id}),
                )
            )
            complete = False

        checks = object.__getattribute__(component, "capability_checks")
        explicit_checks = object.__getattribute__(
            component, "_explicit_capability_checks"
        )
        for capability, checker in sorted(checks.items()):
            checker_id = _implementation_id(checker)
            dependency = (
                PublicDependency.custom
                if explicit_checks
                else PublicDependency.configured
            )
            dependencies.append(
                dependency(
                    "toolchains",
                    _scoped_implementation_id(
                        "playtest-check.%s" % capability, checker_id
                    ),
                    "1.0.0",
                    _json_sha256(
                        {"capability": capability, "implementation": checker_id}
                    ),
                )
            )
        if explicit_checks:
            complete = False

        declared_classic = any(
            item.name.startswith("classic_rules.") for item in explicit_services
        )
        declared_world = any(
            item.name.startswith("world_playtest.") for item in explicit_services
        )
        lane_providers = object.__getattribute__(component, "lane_providers")
        if type(lane_providers) is WorkshopLanePlaytestProviders:
            classic = object.__getattribute__(lane_providers, "classic_provider")
            science = object.__getattribute__(lane_providers, "science_provider")
            world = object.__getattribute__(lane_providers, "world_provider")
            if type(classic) is PinnedCheckersRulesProvider:
                identity = object.__getattribute__(classic, "identity")
                dependencies.append(
                    PublicDependency.configured(
                        "toolchains",
                        object.__getattribute__(identity, "name"),
                        object.__getattribute__(identity, "version"),
                        object.__getattribute__(identity, "config_sha256"),
                    )
                )
            elif not declared_classic:
                classic_id = _implementation_id(classic)
                dependencies.append(
                    PublicDependency.custom(
                        "services",
                        _scoped_implementation_id("classic-rules", classic_id),
                        "1.0.0",
                        _json_sha256({"implementation": classic_id}),
                    )
                )
                complete = False
            if type(science) is SealedInventScienceEvidenceProvider:
                identity = object.__getattribute__(science, "identity")
                dependencies.append(
                    PublicDependency.configured(
                        "toolchains",
                        object.__getattribute__(identity, "name"),
                        object.__getattribute__(identity, "version"),
                        object.__getattribute__(identity, "config_sha256"),
                    )
                )
            else:
                science_id = _implementation_id(science)
                dependencies.append(
                    PublicDependency.custom(
                        "services",
                        _scoped_implementation_id("science-evidence", science_id),
                        "1.0.0",
                        _json_sha256({"implementation": science_id}),
                    )
                )
                complete = False
            if world is None:
                if not declared_world:
                    dependencies.append(
                        PublicDependency.missing(
                            "services", "world-playtest-evidence"
                        )
                    )
            elif not declared_world:
                world_id = _implementation_id(world)
                dependencies.append(
                    PublicDependency.custom(
                        "services",
                        _scoped_implementation_id("world-playtest", world_id),
                        "1.0.0",
                        _json_sha256({"implementation": world_id}),
                    )
                )
                complete = False
        else:
            registry_id = _implementation_id(lane_providers)
            dependencies.append(
                PublicDependency.custom(
                    "services",
                    _scoped_implementation_id(
                        "lane-playtest-registry", registry_id
                    ),
                    "1.0.0",
                    _json_sha256({"implementation": registry_id}),
                )
            )
            complete = False
        return _KnownDescription(
            DEFAULT_STAGE_PROVIDER_IDS["playtest"],
            implementation,
            _json_sha256(
                {"playtest_config_sha256": config, "game_count": game_count}
            ),
            _ordered_dependencies(dependencies),
            complete,
        )

    if stage == "instructions" and type(component) is RewardedInstructions:
        creator = object.__getattribute__(component, "creator")
        evaluator = object.__getattribute__(component, "evaluator")
        creator_config = object.__getattribute__(component, "creator_config_sha256")
        reward_config = object.__getattribute__(component, "reward_config_sha256")
        dependencies = [
            _model_dependency("instructions-creator", creator),
            _model_dependency("instructions-reward", evaluator),
            PublicDependency.configured(
                "prompts",
                "workshop-instructions-creator",
                object.__getattribute__(component, "creator_version"),
                creator_config,
            ),
            PublicDependency.configured(
                "rewards",
                "workshop-instructions-reward",
                object.__getattribute__(component, "evaluator_version"),
                reward_config,
            ),
            *explicit_services,
        ]
        if object.__getattribute__(component, "site_writer") is None:
            dependencies.append(
                PublicDependency.missing("services", "factory-private-draft")
            )
        elif not explicit_services:
            writer_id = _implementation_id(
                object.__getattribute__(component, "site_writer")
            )
            dependencies.append(
                _identity_dependency(
                    "services", writer_id, "1.0.0", {"implementation": writer_id}
                )
            )
        return _KnownDescription(
            DEFAULT_STAGE_PROVIDER_IDS["instructions"],
            implementation,
            _json_sha256(
                {
                    "creator_config_sha256": creator_config,
                    "reward_config_sha256": reward_config,
                    "reward_loop_policy": _reward_loop_policy(component),
                }
            ),
            _ordered_dependencies(dependencies),
            object.__getattribute__(component, "site_writer") is None
            or bool(explicit_services),
        )

    if stage == "deliver" and type(component) is DefaultDeliver:
        dependencies = list(explicit_services)
        fulfiller = object.__getattribute__(component, "fulfiller")
        complete = True
        if fulfiller is None:
            dependencies.append(
                PublicDependency.missing("services", "production-and-shipping")
            )
        elif not explicit_services:
            fulfiller_id = _implementation_id(fulfiller)
            dependencies.append(
                _identity_dependency(
                    "services",
                    fulfiller_id,
                    "1.0.0",
                    {"implementation": fulfiller_id},
                )
            )
            complete = False
        return _KnownDescription(
            DEFAULT_STAGE_PROVIDER_IDS["deliver"],
            implementation,
            _json_sha256(
                {
                    "contract": "production-qa-packing-carrier-v1",
                }
            ),
            _ordered_dependencies(dependencies),
            complete,
        )
    return None


def _mapping_of_sequences(
    value: Optional[Mapping[str, Sequence[PublicDependency]]], label: str
) -> Dict[str, Tuple[PublicDependency, ...]]:
    if value is None:
        return {}
    if not isinstance(value, Mapping) or any(key not in WORKSHOP_STAGES for key in value):
        raise ContractError("%s must be keyed only by Workshop stage" % label)
    selected = {}
    for stage, dependencies in value.items():
        if isinstance(dependencies, (str, bytes)) or not isinstance(
            dependencies, Sequence
        ):
            raise ContractError("%s values must be dependency sequences" % label)
        selected[stage] = _ordered_dependencies(dependencies)
    return selected


def describe_effective_engine(
    components: Mapping[str, Any],
    *,
    provider_ids: Optional[Mapping[str, str]] = None,
    custom_stages: Iterable[str] = (),
    configuration_sha256: Optional[Mapping[str, str]] = None,
    service_dependencies: Optional[
        Mapping[str, Sequence[PublicDependency]]
    ] = None,
    toolchain_dependencies: Optional[
        Mapping[str, Sequence[PublicDependency]]
    ] = None,
) -> EngineProvenanceManifest:
    """Materialize all five effective stages from explicit composition inputs.

    Unknown trusted callables remain usable but are marked ``opaque``.  A
    production composition can make an unknown/custom stage content-addressed
    by supplying its public configuration hash.  The function never calls a
    component, serializes its attributes, or evaluates ``repr(component)``.
    """

    if not isinstance(components, Mapping) or set(components) != set(WORKSHOP_STAGES):
        raise ContractError(
            "effective engine components must contain all five stages in order"
        )
    providers = {} if provider_ids is None else dict(provider_ids)
    if any(stage not in WORKSHOP_STAGES for stage in providers):
        raise ContractError("engine provider ids contain an unknown stage")
    custom = tuple(custom_stages)
    if len(custom) != len(set(custom)):
        raise ContractError("custom engine stages must be unique")
    for stage in custom:
        _stage(stage)
    configs = {} if configuration_sha256 is None else dict(configuration_sha256)
    if any(stage not in WORKSHOP_STAGES for stage in configs):
        raise ContractError("engine configuration hashes contain an unknown stage")
    for digest in configs.values():
        require_sha256(digest, "engine component configuration sha256")
    services = _mapping_of_sequences(service_dependencies, "service dependencies")
    toolchains = _mapping_of_sequences(
        toolchain_dependencies, "toolchain dependencies"
    )
    if any(
        dependency.kind != "services"
        for dependencies in services.values()
        for dependency in dependencies
    ):
        raise ContractError("service dependencies must use the services kind")
    if any(
        dependency.kind != "toolchains"
        for dependencies in toolchains.values()
        for dependency in dependencies
    ):
        raise ContractError("toolchain dependencies must use the toolchains kind")

    manifests = []
    for stage in WORKSHOP_STAGES:
        component = components[stage]
        if component is None:
            if stage in providers or stage in configs or stage in custom:
                raise ContractError("a missing stage cannot claim provider configuration")
            manifests.append(StageComponentManifest.missing(stage))
            continue
        explicit_services = services.get(stage, ())
        known = (
            None
            if stage in custom
            else _describe_known_component(stage, component, explicit_services)
        )
        implementation = (
            known.implementation_id if known is not None else _implementation_id(component)
        )
        provider_id = providers.get(
            stage, known.provider_id if known is not None else implementation
        )
        _public_id(provider_id, "stage provider id")
        dependencies = list(known.dependencies if known is not None else ())
        if known is None:
            dependencies.extend(explicit_services)
        dependencies.extend(toolchains.get(stage, ()))
        supplied_config = configs.get(stage)
        if supplied_config is not None:
            selected_config = supplied_config
        elif known is not None:
            selected_config = known.configuration_sha256
        else:
            selected_config = _json_sha256(
                {"provider_id": provider_id, "implementation_id": implementation}
            )
        state = "custom" if stage in custom else "configured"
        complete = (
            supplied_config is not None
            if known is None
            else known.complete
        )
        manifests.append(
            StageComponentManifest(
                stage,
                state,
                "complete" if complete else "opaque",
                provider_id,
                implementation,
                selected_config,
                _ordered_dependencies(dependencies),
            )
        )
    return EngineProvenanceManifest(tuple(manifests))


__all__ = [
    "COMPONENT_STATES",
    "DEFAULT_STAGE_PROVIDER_IDS",
    "DEPENDENCY_KINDS",
    "EngineProvenanceManifest",
    "MANIFEST_COMPLETENESS",
    "PublicDependency",
    "ResumeEngineCompatibility",
    "StageComponentManifest",
    "WORKSHOP_STAGES",
    "compare_engine_for_resume",
    "describe_effective_engine",
]
