"""Trusted Manager-side composition for production Workshop services.

Inventor contributions never load this registry and never receive its service
objects.  An operator selects one installed entry point; that trusted factory
returns explicit bindings for the production capabilities it owns.  Bindings
publish only a bounded provider identity.  Credentials, clients, tokens, raw
world references, and carrier implementations remain opaque live objects.

Entry point group::

    autonomous_workshop.manager_services

An entry point name is the ``configuration_id`` and its target must be either a
``ManagerServices`` instance or a zero-argument factory returning one.
"""

from __future__ import annotations

import re
from importlib import machinery
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
)

from .agent_invent import (
    InventResearch,
    InventResearchProvider,
    InventResearchUnavailable,
)
from .errors import AmbiguousEffectError, ContractError
from .factory_agent import FactoryAgentCredentials
from .jobs import (
    DeliverContext,
    Delivered,
    InventContext,
    Need,
    PlaytestContext,
    WaitingFor,
)
from .lane_playtest_providers import (
    ClassicEvidenceProvider,
    PreparedLaneRelease,
)
from .make import Wish
from .models import require_exact_version, require_sha256
from .world_reference_vault import WorldReferenceService
from .world_service import (
    WorldInventInputs,
    WorldPlaytestEvidence,
    WorldPlaytestService,
    WorldProviderIdentity,
    prepare_world_invent_inputs,
    prepare_world_playtest_evidence,
)


MANAGER_SERVICES_ENTRY_POINT_GROUP = "autonomous_workshop.manager_services"

_CONFIGURATION_ID = re.compile(r"[a-z][a-z0-9-]{0,62}\Z")
_PROVIDER_ID = re.compile(r"[a-z][a-z0-9._-]{1,127}\Z")
_INVENTOR_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_MAX_ENTRY_POINTS = 128
_MAX_DISTRIBUTION_FILES = 100_000
_MAX_ISOLATION_PATHS = _MAX_ENTRY_POINTS * 4

_CAPABILITIES = (
    "research",
    "classic_rules",
    "world_reference",
    "world_playtest",
    "factory_credentials",
    "deliver",
)


def _configuration_id(value: Any) -> str:
    if not isinstance(value, str) or _CONFIGURATION_ID.fullmatch(value) is None:
        raise ContractError(
            "Manager service configuration_id must be a canonical lowercase id"
        )
    return value


def _provider_id(value: Any) -> str:
    if not isinstance(value, str) or _PROVIDER_ID.fullmatch(value) is None:
        raise ContractError(
            "Manager service provider_id must be a bounded canonical id"
        )
    return value


class WishResearchProvider(Protocol):
    """Manager-owned research selected with the exact Wish in view."""

    def research(self, wish: Wish, context: InventContext) -> InventResearch:
        ...


class ClassicRulesRegistry(Protocol):
    """Select an independently modeled classic-rules provider for one Wish."""

    def provider_for(
        self, wish: Wish, context: PlaytestContext
    ) -> ClassicEvidenceProvider:
        ...


class FactoryCredentialBroker(Protocol):
    """Return one inventor's opaque Factory credential only when requested."""

    def credentials_for(
        self, inventor_id: str
    ) -> Optional[FactoryAgentCredentials]:
        ...


class DeliverFulfiller(Protocol):
    """Preflight, fulfill once, or read back one exact prior attempt."""

    def preflight(self, context: DeliverContext) -> None:
        """Prove readiness without starting any external effect."""

        ...

    def fulfill(self, context: DeliverContext) -> Delivered:
        """Enter the effectful boundary and return exact delivery evidence."""

        ...

    def reconcile(self, context: DeliverContext) -> Optional[Delivered]:
        """Use authenticated GET-only readback; never start or retry effects."""

        ...


class ManagerProviderIdentity:
    """Only the bounded, non-secret portion of one production provider."""

    __slots__ = ("_provider_id", "_version", "_config_sha256")

    def __init__(self, provider_id: str, version: str, config_sha256: str) -> None:
        self._provider_id = _provider_id(provider_id)
        self._version = require_exact_version(
            version, "Manager service provider version"
        )
        self._config_sha256 = require_sha256(
            config_sha256, "Manager service provider config sha256"
        )

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def version(self) -> str:
        return self._version

    @property
    def config_sha256(self) -> str:
        return self._config_sha256

    def to_dict(self) -> Dict[str, str]:
        return {
            "provider_id": self.provider_id,
            "version": self.version,
            "config_sha256": self.config_sha256,
        }

    def world_identity(self) -> WorldProviderIdentity:
        return WorldProviderIdentity(
            self.provider_id,
            self.version,
            self.config_sha256,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ManagerProviderIdentity) and (
            self.provider_id,
            self.version,
            self.config_sha256,
        ) == (
            other.provider_id,
            other.version,
            other.config_sha256,
        )

    def __hash__(self) -> int:
        return hash((self.provider_id, self.version, self.config_sha256))

    def __repr__(self) -> str:
        return (
            "ManagerProviderIdentity(provider_id=%r, version=%r, "
            "config_sha256=%r)"
            % (self.provider_id, self.version, self.config_sha256)
        )


ServiceT = TypeVar("ServiceT")


class ManagerServiceBinding(Generic[ServiceT]):
    """One public identity paired with one deliberately opaque live service."""

    __slots__ = ("_identity", "_service")

    def __init__(
        self, identity: ManagerProviderIdentity, service: ServiceT
    ) -> None:
        if not isinstance(identity, ManagerProviderIdentity):
            raise ContractError("Manager service binding requires a provider identity")
        if service is None:
            raise ContractError("Manager service binding requires a live service")
        self._identity = identity
        self._service = service

    @property
    def identity(self) -> ManagerProviderIdentity:
        return self._identity

    @property
    def service(self) -> ServiceT:
        return self._service

    def public_summary(self) -> Dict[str, str]:
        return self.identity.to_dict()

    def __repr__(self) -> str:
        return "ManagerServiceBinding(identity=%r, service=<opaque>)" % self.identity

    def __reduce_ex__(self, protocol: int) -> Any:
        del protocol
        raise TypeError("live Manager service bindings cannot be serialized")


class _WishResearchAdapter:
    __slots__ = ("_binding",)

    def __init__(
        self, binding: ManagerServiceBinding[WishResearchProvider]
    ) -> None:
        self._binding = binding

    def __call__(self, context: InventContext) -> InventResearch:
        if not isinstance(context, InventContext):
            raise ContractError("Manager research requires an InventContext")
        try:
            result = self._binding.service.research(context.wish, context)
            if not isinstance(result, InventResearch):
                raise ContractError("Manager research returned untyped evidence")
            result.assert_context(context)
            expected = self._binding.identity
            if (
                result.provider != expected.provider_id
                or result.provider_version != expected.version
                or result.provider_config_sha256 != expected.config_sha256
            ):
                raise ContractError(
                    "Manager research evidence identifies a different provider"
                )
            return result
        except InventResearchUnavailable:
            raise
        except Exception:
            raise InventResearchUnavailable(
                "Manager research provider failed"
            ) from None

    def __repr__(self) -> str:
        return "ManagerWishResearchProvider(identity=%r)" % self._binding.identity


class _ClassicRulesAdapter:
    __slots__ = ("_binding",)

    def __init__(
        self, binding: ManagerServiceBinding[ClassicRulesRegistry]
    ) -> None:
        self._binding = binding

    def prepare(self, context: PlaytestContext) -> PreparedLaneRelease:
        if not isinstance(context, PlaytestContext):
            raise ContractError("Manager classic rules require a PlaytestContext")
        try:
            provider = self._binding.service.provider_for(context.wish, context)
            prepare = getattr(provider, "prepare", None)
            if not callable(prepare):
                raise ContractError(
                    "classic rules registry returned a malformed provider"
                )
            result = prepare(context)
            if not isinstance(result, PreparedLaneRelease):
                raise ContractError("classic rules provider returned untyped evidence")
            if (
                result.capability != "classic-rules-test"
                or result.artifact_sha256 != context.made.artifact_sha256
                or result.provider.name != self._binding.identity.provider_id
                or result.provider.version != self._binding.identity.version
                or result.provider.config_sha256
                != self._binding.identity.config_sha256
            ):
                raise ContractError(
                    "classic rules provider returned evidence for another Make"
                )
            return result
        except Exception:
            # Provider-authored exception and Need text is untrusted. Persist
            # only this Workshop-authored recovery contract.
            raise WaitingFor(
                Need(
                    "playtest",
                    "classic-rules-test",
                    "The shared classic provider did not return complete reference-bound evidence for this exact edition.",
                    "Repair or reconnect the Manager-owned classic provider; include exact public rules, seeded conformance traces, and CAD-bound physical-role cases.",
                )
            ) from None

    def __repr__(self) -> str:
        return "ManagerClassicRulesProvider(identity=%r)" % self._binding.identity


class _DeliverAdapter:
    __slots__ = ("_binding",)

    def __init__(self, binding: ManagerServiceBinding[DeliverFulfiller]) -> None:
        self._binding = binding

    def __call__(self, context: DeliverContext) -> Delivered:
        if not isinstance(context, DeliverContext):
            raise ContractError("Manager Deliver requires a DeliverContext")
        context.assert_current()
        try:
            preflight = self._binding.service.preflight(context)
            if preflight is not None:
                raise ContractError("Manager Deliver preflight returned a value")
            context.assert_current()
        except WaitingFor:
            raise WaitingFor(
                Need(
                    "deliver",
                    "production-and-shipping",
                    "The Manager fulfillment provider is not ready for this exact product.",
                    "Repair or reconnect the selected fulfillment provider, then resume this exact Wish.",
                )
            ) from None
        except Exception:
            raise WaitingFor(
                Need(
                    "deliver",
                    "production-and-shipping",
                    "The Manager fulfillment provider did not pass its no-effect readiness preflight.",
                    "Repair or reconnect the selected fulfillment provider, then resume this exact Wish.",
                )
            ) from None
        try:
            result = self._binding.service.fulfill(context)
            if not isinstance(result, Delivered):
                raise ContractError("Manager Deliver returned untyped evidence")
            result.assert_context(context)
            return result
        except Exception:
            # Once fulfill is entered, even provider-authored WaitingFor is an
            # unknown external outcome. Never make it a retryable wait.
            raise AmbiguousEffectError(
                "The Manager fulfillment effect has an unknown outcome; reconcile it without retrying."
            ) from None

    def reconcile(self, context: DeliverContext) -> Optional[Delivered]:
        """Perform only the provider's authenticated readback operation."""

        if not isinstance(context, DeliverContext):
            raise ContractError(
                "Manager Deliver reconciliation requires a DeliverContext"
            )
        context.assert_current()
        try:
            result = self._binding.service.reconcile(context)
            context.assert_current()
            if result is None:
                return None
            if not isinstance(result, Delivered):
                raise ContractError(
                    "Manager Deliver reconciliation returned untyped evidence"
                )
            result.assert_context(context)
            return result
        except Exception:
            # Provider text and credentials are untrusted. Reconciliation is
            # safe to repeat because its official contract is GET-only, but it
            # can never turn an unknown attempt back into a fulfill retry.
            raise AmbiguousEffectError(
                "The Manager fulfillment readback did not prove this exact attempt; retry reconciliation without fulfilling."
            ) from None

    def __repr__(self) -> str:
        return "ManagerDeliverFulfiller(identity=%r)" % self._binding.identity


class ManagerServices:
    """One installed, trusted Manager-side production composition root."""

    __slots__ = ("_configuration_id", "_bindings")

    def __init__(
        self,
        configuration_id: str,
        *,
        research: Optional[ManagerServiceBinding[WishResearchProvider]] = None,
        classic_rules: Optional[
            ManagerServiceBinding[ClassicRulesRegistry]
        ] = None,
        world_reference: Optional[
            ManagerServiceBinding[WorldReferenceService]
        ] = None,
        world_playtest: Optional[
            ManagerServiceBinding[WorldPlaytestService]
        ] = None,
        factory_credentials: Optional[
            ManagerServiceBinding[FactoryCredentialBroker]
        ] = None,
        deliver: Optional[ManagerServiceBinding[DeliverFulfiller]] = None,
    ) -> None:
        self._configuration_id = _configuration_id(configuration_id)
        selected = {
            "research": research,
            "classic_rules": classic_rules,
            "world_reference": world_reference,
            "world_playtest": world_playtest,
            "factory_credentials": factory_credentials,
            "deliver": deliver,
        }
        bindings: Dict[str, ManagerServiceBinding[Any]] = {}
        for capability, binding in selected.items():
            if binding is None:
                continue
            if not isinstance(binding, ManagerServiceBinding):
                raise ContractError(
                    "Manager %s capability requires a typed binding" % capability
                )
            self._validate_service(capability, binding.service)
            bindings[capability] = binding
        if not bindings:
            raise ContractError(
                "Manager service configuration must bind at least one capability"
            )
        self._bindings = bindings

    @staticmethod
    def _validate_service(capability: str, service: Any) -> None:
        required_methods = {
            "research": ("research",),
            "classic_rules": ("provider_for",),
            "world_reference": (
                "descriptors",
                "verify_admission",
                "authorized_provider_inputs",
                "verify_authorization",
            ),
            "world_playtest": ("evaluate", "verify"),
            "factory_credentials": ("credentials_for",),
        }
        required_methods["deliver"] = ("preflight", "fulfill", "reconcile")
        if capability not in required_methods or not all(
            callable(getattr(service, method, None))
            for method in required_methods[capability]
        ):
            raise ContractError("Manager %s service is malformed" % capability)

    @property
    def configuration_id(self) -> str:
        return self._configuration_id

    @property
    def capabilities(self) -> Tuple[str, ...]:
        return tuple(
            capability
            for capability in _CAPABILITIES
            if capability in self._bindings
        )

    def binding(
        self, capability: str
    ) -> Optional[ManagerServiceBinding[Any]]:
        if capability not in _CAPABILITIES:
            raise ContractError("unknown Manager service capability")
        return self._bindings.get(capability)

    @property
    def invent_research_provider(self) -> Optional[InventResearchProvider]:
        binding = self._bindings.get("research")
        return None if binding is None else _WishResearchAdapter(binding)

    @property
    def classic_evidence_provider(self) -> Optional[ClassicEvidenceProvider]:
        binding = self._bindings.get("classic_rules")
        return None if binding is None else _ClassicRulesAdapter(binding)

    @property
    def world_reference_service(self) -> Optional[WorldReferenceService]:
        binding = self._bindings.get("world_reference")
        return None if binding is None else binding.service

    @property
    def world_playtest_service(self) -> Optional[WorldPlaytestService]:
        binding = self._bindings.get("world_playtest")
        return None if binding is None else binding.service

    @property
    def deliver_fulfiller(
        self,
    ) -> Optional[_DeliverAdapter]:
        binding = self._bindings.get("deliver")
        return None if binding is None else _DeliverAdapter(binding)

    def prepare_world_inputs(self, wish: Wish) -> WorldInventInputs:
        binding = self._bindings.get("world_reference")
        if binding is None:
            raise ContractError("Manager world reference service is not configured")
        try:
            return prepare_world_invent_inputs(
                wish,
                binding.service,
                binding.identity.world_identity(),
            )
        except Exception:
            raise ContractError("Manager world reference service failed") from None

    def prepare_world_evidence(
        self,
        wish: Wish,
        artifact_sha256: str,
        personalization_map: Mapping[str, Any],
        invent_inputs: WorldInventInputs,
    ) -> WorldPlaytestEvidence:
        binding = self._bindings.get("world_playtest")
        if binding is None:
            raise ContractError("Manager world Playtest service is not configured")
        try:
            evidence = prepare_world_playtest_evidence(
                wish,
                artifact_sha256,
                personalization_map,
                invent_inputs,
                binding.service,
            )
        except Exception:
            raise ContractError("Manager world Playtest service failed") from None
        if evidence.provider != binding.identity.world_identity():
            raise ContractError(
                "world Playtest evidence identifies a different provider"
            )
        return evidence

    def factory_credentials_for(
        self, inventor_id: str
    ) -> Optional[FactoryAgentCredentials]:
        if (
            not isinstance(inventor_id, str)
            or _INVENTOR_ID.fullmatch(inventor_id) is None
        ):
            raise ContractError("Factory inventor_id must be a canonical slug")
        binding = self._bindings.get("factory_credentials")
        if binding is None:
            raise ContractError("Manager Factory credential broker is not configured")
        try:
            credentials = binding.service.credentials_for(inventor_id)
        except Exception:
            raise ContractError("Factory credential broker failed") from None
        if credentials is None:
            return None
        if not isinstance(credentials, FactoryAgentCredentials):
            raise ContractError("Factory credential broker returned an untyped secret")
        if credentials.username.casefold() != inventor_id.casefold():
            raise ContractError(
                "Factory credential broker returned a different inventor account"
            )
        return credentials

    def trusted_workshop_engine(self):
        """Compose all five effective shared workers owned by this Manager."""

        from .agent_invent import CodexInventor
        from .agent_instructions import RewardedInstructions
        from .agent_make import CodexMaker
        from .agent_playtest import LaneAwarePlaytester
        from .deliver import DefaultDeliver
        from .engine_provenance import (
            DEFAULT_STAGE_PROVIDER_IDS,
            PublicDependency,
            describe_effective_engine,
        )
        from .manager import register_workshop_engine
        from .workshop import WorkshopTools

        provider_ids = dict(DEFAULT_STAGE_PROVIDER_IDS)
        research = self.invent_research_provider
        invent = (
            CodexInventor()
            if research is None
            else CodexInventor(research_provider=research)
        )
        if research is not None:
            provider_ids["invent"] = self.stage_provider_id("research", "invent")
        make = CodexMaker()
        classic = self.classic_evidence_provider
        playtest = (
            LaneAwarePlaytester()
            if classic is None
            else LaneAwarePlaytester(classic_provider=classic)
        )
        if classic is not None:
            provider_ids["playtest"] = self.stage_provider_id(
                "classic_rules", "playtest"
            )
        instructions = RewardedInstructions(None)
        fulfiller = self.deliver_fulfiller
        deliver = DefaultDeliver(fulfiller)
        if fulfiller is not None:
            provider_ids["deliver"] = self.stage_provider_id("deliver", "deliver")

        tools = WorkshopTools(
            invent=invent,
            make=make,
            playtest=playtest,
            instructions=instructions,
            deliver=deliver,
        )
        stage_capabilities = {
            "invent": ("research", "world_reference"),
            "make": (),
            "playtest": ("classic_rules", "world_playtest"),
            "instructions": ("factory_credentials",),
            "deliver": ("deliver",),
        }
        service_dependencies = {}
        for stage, capabilities in stage_capabilities.items():
            dependencies = []
            for capability in capabilities:
                binding = self._bindings.get(capability)
                if binding is None:
                    continue
                identity = binding.identity.to_dict()
                dependencies.append(
                    PublicDependency.from_public_identity(
                        "services",
                        identity,
                        name="%s.%s"
                        % (capability, identity["provider_id"]),
                    )
                )
            if dependencies:
                service_dependencies[stage] = tuple(dependencies)
        provenance = describe_effective_engine(
            {
                "invent": invent,
                "make": make,
                "playtest": playtest,
                "instructions": instructions,
                "deliver": deliver,
            },
            provider_ids=provider_ids,
            service_dependencies=service_dependencies,
        )
        return register_workshop_engine(
            tools,
            provider_ids=provider_ids,
            provenance=provenance,
        )

    def stage_provider_id(self, capability: str, stage: str) -> str:
        if capability not in self._bindings or stage not in (
            "invent",
            "make",
            "playtest",
            "instructions",
            "deliver",
        ):
            raise ContractError("Manager service stage provider identity is invalid")
        binding = self._bindings[capability]
        identity = binding.identity
        return "manager-services.%s.%s.%s.%s.%s" % (
            self.configuration_id,
            stage,
            identity.provider_id,
            identity.version,
            identity.config_sha256,
        )

    def public_summary(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "configuration_id": self.configuration_id,
            "capabilities": {
                capability: self._bindings[capability].public_summary()
                for capability in self.capabilities
            },
        }

    def __repr__(self) -> str:
        return "ManagerServices(configuration_id=%r, capabilities=%r)" % (
            self.configuration_id,
            self.capabilities,
        )

    def __reduce_ex__(self, protocol: int) -> Any:
        del protocol
        raise TypeError("live Manager services cannot be serialized")


class ManagerServiceEntryPoint(Protocol):
    name: str
    group: str

    def load(self) -> Any:
        ...


EntryPointResolver = Callable[[str], Iterable[ManagerServiceEntryPoint]]


def installed_manager_service_entry_points(
    group: str,
) -> Iterable[ManagerServiceEntryPoint]:
    """Resolve installed entry points without importing any provider."""

    if group != MANAGER_SERVICES_ENTRY_POINT_GROUP:
        raise ContractError("Manager service entry-point group is not trusted")
    return metadata.entry_points(group=group)


def _entry_points(
    resolver: EntryPointResolver,
) -> Tuple[ManagerServiceEntryPoint, ...]:
    try:
        discovered = resolver(MANAGER_SERVICES_ENTRY_POINT_GROUP)
        if isinstance(discovered, (str, bytes, Mapping)):
            raise TypeError
        entries = []
        for index, entry in enumerate(discovered):
            if index >= _MAX_ENTRY_POINTS:
                raise ContractError(
                    "too many installed Manager service entry points"
                )
            name = getattr(entry, "name", None)
            _configuration_id(name)
            group = getattr(entry, "group", MANAGER_SERVICES_ENTRY_POINT_GROUP)
            if group != MANAGER_SERVICES_ENTRY_POINT_GROUP or not callable(
                getattr(entry, "load", None)
            ):
                raise ContractError("Manager service entry point is malformed")
            entries.append(entry)
    except ContractError:
        raise
    except Exception:
        raise ContractError("Manager service entry-point discovery failed") from None
    names = tuple(entry.name for entry in entries)
    if len(names) != len(set(names)):
        raise ContractError("duplicate Manager service entry-point name")
    return tuple(entries)


def discover_manager_service_configurations(
    *,
    resolver: EntryPointResolver = installed_manager_service_entry_points,
) -> Tuple[str, ...]:
    """List validated installed configuration ids without loading providers."""

    return tuple(sorted(entry.name for entry in _entry_points(resolver)))


def _distribution_file_manifest(
    entry: ManagerServiceEntryPoint,
) -> tuple[Any, tuple[PurePosixPath, ...]]:
    """Return one entry point's inert installed-file manifest.

    Reading ``Distribution.files`` and ``locate_file`` never imports the entry
    point target.  Custom contribution isolation relies on that distinction:
    provider factories must remain entirely in the Manager process.
    """

    distribution = getattr(entry, "dist", None)
    locate = getattr(distribution, "locate_file", None)
    files = getattr(distribution, "files", None)
    if distribution is None or not callable(locate) or files is None or isinstance(
        files, (str, bytes, Mapping)
    ):
        raise ContractError(
            "installed Manager service distribution metadata is unavailable"
        )
    normalized = []
    try:
        for index, item in enumerate(files):
            if index >= _MAX_DISTRIBUTION_FILES:
                raise ContractError(
                    "installed Manager service distribution manifest is too large"
                )
            relative = PurePosixPath(str(item))
            if (
                relative.is_absolute()
                or not relative.parts
                or any(part in ("", ".") for part in relative.parts)
            ):
                # Absolute RECORD paths are not valid installed-distribution
                # ownership records. Relative ``..`` launcher paths are kept
                # and denied as exact resolved files below.
                continue
            normalized.append(relative)
    except ContractError:
        raise
    except Exception:
        raise ContractError(
            "installed Manager service distribution manifest is unreadable"
        ) from None
    return distribution, tuple(normalized)


def _located_distribution_path(
    distribution: Any,
    relative: PurePosixPath,
) -> Path:
    try:
        located = Path(distribution.locate_file(relative))
        if not located.is_absolute():
            raise OSError
        return located.resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ContractError(
            "installed Manager service isolation path cannot be resolved"
        ) from None


def _entry_point_module(entry: ManagerServiceEntryPoint) -> PurePosixPath:
    try:
        module = getattr(entry, "module")
    except Exception:
        raise ContractError(
            "installed Manager service entry point has no import target"
        ) from None
    if not isinstance(module, str) or not module or len(module) > 512:
        raise ContractError(
            "installed Manager service entry point has no import target"
        )
    components = module.split(".")
    if len(components) > 32 or any(
        re.fullmatch(r"[A-Za-z_]\w*", component) is None
        for component in components
    ):
        raise ContractError(
            "installed Manager service entry point import target is malformed"
        )
    return PurePosixPath(*components)


def _entry_point_isolation_paths(
    entry: ManagerServiceEntryPoint,
) -> tuple[Path, ...]:
    distribution, files = _distribution_file_manifest(entry)
    module_path = _entry_point_module(entry)
    suffixes = tuple(machinery.all_suffixes())

    metadata_roots = {
        PurePosixPath(*relative.parts[: index + 1])
        for relative in files
        for index, part in enumerate(relative.parts)
        if part.endswith((".dist-info", ".egg-info"))
        and relative.name == "entry_points.txt"
    }
    if not metadata_roots:
        raise ContractError(
            "installed Manager service entry-point metadata is unavailable"
        )

    package_inits = tuple(
        relative
        for relative in files
        if relative.parent == module_path
        and relative.name.startswith("__init__.")
        and any(relative.name.endswith(suffix) for suffix in suffixes)
    )
    if package_inits:
        code_paths = (module_path,)
    else:
        module_parent = module_path.parent
        module_name = module_path.name
        code_paths = tuple(
            relative
            for relative in files
            if relative.parent == module_parent
            and relative.name.startswith(module_name + ".")
            and relative.name != module_name + ".pyi"
            and any(relative.name.endswith(suffix) for suffix in suffixes)
        )
    if not code_paths:
        raise ContractError(
            "installed Manager service entry-point code is not resolvable"
        )

    # Provider entry points must live in a dedicated installed distribution.
    # Deny every owned top-level package/module/data root, not only the target:
    # a hook must not import a sibling credentials/client module, read bundled
    # configuration, or execute a provider-owned .pth file.
    try:
        installation_root = Path(distribution.locate_file(PurePosixPath(".")))
        if not installation_root.is_absolute() or installation_root.is_symlink():
            raise OSError
        installation_root = installation_root.resolve(strict=True)
        if not installation_root.is_dir():
            raise OSError
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ContractError(
            "installed Manager service distribution root cannot be resolved"
        ) from None

    resolved = set()
    for relative in files:
        try:
            installed = Path(distribution.locate_file(relative))
            if not installed.is_absolute():
                raise OSError
            installed = installed.resolve(strict=True)
        except (OSError, RuntimeError, TypeError, ValueError):
            # A stale RECORD entry is not readable and therefore grants no
            # child authority. Exact target and metadata paths are separately
            # required below, so neither can disappear silently.
            continue
        first = relative.parts[0]
        if first == "..":
            resolved.add(installed)
            continue
        top = Path(distribution.locate_file(PurePosixPath(first)))
        if not top.is_absolute() or top.is_symlink():
            raise ContractError(
                "installed Manager service top-level root is unsafe"
            )
        try:
            resolved.add(top.resolve(strict=True))
        except OSError:
            raise ContractError(
                "installed Manager service top-level root cannot be resolved"
            ) from None

    required = {
        _located_distribution_path(distribution, relative)
        for relative in (*tuple(metadata_roots), *code_paths)
    }
    if any(
        not any(
            required_path == owned or owned in required_path.parents
            for owned in resolved
        )
        for required_path in required
    ):
        raise ContractError(
            "installed Manager service distribution ownership is incomplete"
        )

    cache_root = installation_root / "__pycache__"
    if cache_root.is_dir() and not cache_root.is_symlink():
        top_level_modules = {
            relative.stem
            for relative in files
            if len(relative.parts) == 1 and relative.suffix == ".py"
        }
        try:
            for cached in cache_root.iterdir():
                if (
                    cached.is_file()
                    and not cached.is_symlink()
                    and any(
                        cached.name.startswith(module + ".")
                        and cached.name.endswith(".pyc")
                        for module in top_level_modules
                    )
                ):
                    resolved.add(cached.resolve(strict=True))
        except OSError:
            raise ContractError(
                "installed Manager service bytecode paths cannot be resolved"
            ) from None

    child_runtime = Path(__file__).resolve(strict=True).parent
    if any(
        path == child_runtime or path in child_runtime.parents
        for path in resolved
    ):
        raise ContractError(
            "Manager service providers for custom contributions require a dedicated distribution"
        )
    if not resolved:
        raise ContractError(
            "installed Manager service distribution ownership is unavailable"
        )
    return tuple(sorted(resolved, key=str))


def manager_service_forbidden_read_paths(
    *,
    resolver: EntryPointResolver = installed_manager_service_entry_points,
) -> Tuple[Path, ...]:
    """Resolve installed provider code/metadata that a hook must never read.

    Every entry point in the Manager-services group is covered, not merely the
    selected configuration.  This prevents a custom hook from using
    ``importlib.metadata`` to discover a different installed provider.  The
    entry points are inspected but never loaded.  Missing or ambiguous wheel
    metadata fails closed instead of silently leaving provider code readable.
    """

    forbidden = {
        path
        for entry in _entry_points(resolver)
        for path in _entry_point_isolation_paths(entry)
    }
    if len(forbidden) > _MAX_ISOLATION_PATHS:
        raise ContractError("too many Manager service isolation paths")
    return tuple(sorted(forbidden, key=str))


def load_manager_services(
    configuration_id: str,
    *,
    resolver: EntryPointResolver = installed_manager_service_entry_points,
) -> ManagerServices:
    """Load exactly one trusted installed Manager composition, fail closed."""

    selected_id = _configuration_id(configuration_id)
    matches = tuple(
        entry for entry in _entry_points(resolver) if entry.name == selected_id
    )
    if not matches:
        raise ContractError("Manager service configuration is not installed")
    # ``_entry_points`` rejects duplicates globally; keep this local assertion
    # as a defense if its implementation ever changes.
    if len(matches) != 1:
        raise ContractError("Manager service configuration is ambiguous")
    try:
        loaded = matches[0].load()
        services = loaded if isinstance(loaded, ManagerServices) else loaded()
    except Exception:
        raise ContractError("Manager service configuration failed to load") from None
    if not isinstance(services, ManagerServices):
        raise ContractError(
            "Manager service entry point must return ManagerServices"
        )
    if services.configuration_id != selected_id:
        raise ContractError(
            "Manager service entry point returned another configuration"
        )
    return services


def configured_manager_services(
    environ: Mapping[str, str],
    *,
    resolver: EntryPointResolver = installed_manager_service_entry_points,
) -> Optional[ManagerServices]:
    """Load the one explicitly selected production composition, if any."""

    if not isinstance(environ, Mapping):
        raise ContractError("Manager service environment must be a mapping")
    selected = environ.get("WORKSHOP_MANAGER_SERVICES")
    if selected is None:
        return None
    if not isinstance(selected, str) or not selected:
        raise ContractError(
            "WORKSHOP_MANAGER_SERVICES must name one installed configuration"
        )
    return load_manager_services(selected, resolver=resolver)


__all__ = [
    "ClassicRulesRegistry",
    "DeliverFulfiller",
    "EntryPointResolver",
    "FactoryCredentialBroker",
    "MANAGER_SERVICES_ENTRY_POINT_GROUP",
    "ManagerProviderIdentity",
    "ManagerServiceBinding",
    "ManagerServiceEntryPoint",
    "ManagerServices",
    "WishResearchProvider",
    "discover_manager_service_configurations",
    "configured_manager_services",
    "installed_manager_service_entry_points",
    "load_manager_services",
    "manager_service_forbidden_read_paths",
]
