"""Convenience and 0.x compatibility facade for Autonomous Workshop.

New code should import the public boundary owned by each component, such as
``workshop.wish``, ``workshop.make``, or ``workshop.workflow``. This root
surface keeps established 0.x callers working; it is not a second owner for
the contracts re-exported here.
"""

from workshop.artifacts.core import (
    ArtifactManifest,
    build_artifact_manifest,
    build_pack,
    build_publish_packet,
)
from workshop.product.attribution import attribute_product_description
from workshop.invent.agent import (
    CodexInventor,
    InventResearch,
    InventResearchProvider,
    InventResearchSource,
    InventResearchUnavailable,
)
from workshop.make.cad import (
    CadReleaseBundle,
    KernelBodyObservation,
    StlInspectionLimits,
    StlPathInspectionError,
    StlTopologyReceipt,
    fits_bed_envelope,
    inspect_stl_path,
    inspect_stl_topology,
)
from workshop.workflow.clockwork import (
    Clockwork,
    InspectionPolicy,
    PlaytestPolicy,
    Workflow,
    WorkflowSpec,
)
from workshop.make.service import (
    CadBuildResult,
    CreationBrief,
    CreationResult,
    Forge,
    MakeResult,
    ProductForge,
    Workbench,
)
from workshop.wish import Wish, generate_wish_id
from workshop.integrations.doors import (
    CadDoor,
    CadInspectionDoor,
    DeliveryDoor,
    InspectionDoor,
    ModelDoor,
    SendDoor,
    ShopDoorProtocol,
)
from workshop.integrations.base import Adapter
from workshop.playtest.inspection import Inspection
from workshop.playtest.service import Playtest
from workshop.playtest.release import (
    CapabilityReleaseProof,
    ReleaseProofSource,
    playtest_release_needs,
)
from workshop.playtest.providers import (
    ClassicEvidenceProvider,
    PinnedCheckersRulesProvider,
    PreparedLaneRelease,
    ProviderIdentity,
    PublicScienceSource,
    ScienceAccuracyCase,
    ScienceComprehensionTrace,
    ScienceEvidenceProvider,
    ScienceSimplificationCheck,
    ScienceVerification,
    WorkshopLanePlaytestProviders,
    WorldConsentRecord,
    WorldEvidenceProvider,
    WorldLikenessCase,
    WorldReferenceMaterial,
    WorldVerification,
)
from workshop.make.moving_machine import (
    MOVING_MACHINE_BINDING_KIND,
    MOVING_MACHINE_BINDING_VERSION,
    workshop_pinned_wear_model,
)
from workshop.playtest.moving_machine import (
    MovingMachineVerification,
    WorkshopMovingMachineVerifier,
)
from workshop.reviews.service import ReviewAuthentication, ReviewAuthenticator, review_sha256
from workshop.integrations.sealed_draft import (
    CanonicalSlugDoor,
    SealedDraft,
    load_sealed_draft,
    publish_sealed_draft,
)
from workshop.deliver.service import DefaultDeliver
from workshop.deliver.evidence import (
    DeliveryEvidenceReceipt,
    validate_delivery_evidence_chain,
)
from workshop.release.service import (
    DefaultRelease,
    ReleaseSiteWriter,
)
from workshop.playtest.gameplay import (
    ExecutableGame,
    GameTrace,
    LeagueConfig,
    LeagueReport,
    PlayerPolicy,
    RandomPlayer,
    run_game,
    run_league,
)
from workshop.deliver.contracts import DeliverContext, Delivered
from workshop.release.contracts import ReleaseContext, ProductRelease
from workshop.invent.contracts import InventContext, Invented
from workshop.make.contracts import Feedback, Made, MakeContext
from workshop.outcomes import Need, WaitingFor
from workshop.playtest.contracts import PlaytestContext, Playtested
from workshop.reviews.contracts import CustomerReview
from workshop.workflow.contracts import WorkshopRun
from workshop.match.service import (
    CatalogPage,
    FinalistContext,
    InventorAssignment,
    InventorCard,
    InventorCatalog,
    InventorFinalist,
    InventorRetriever,
    InventorRetrieverRequired,
    NoInventorFit,
    RoutingContext,
    RoutingDecision,
    Shortlist,
    TasteFit,
    TasteJudge,
    TasteJudgeRequired,
    WorkshopManager,
    create_assignment,
    create_shortlist,
    dispatch_assignment,
    discover_inventor_catalog,
    load_finalists,
    retrieve_shortlist,
    select_inventor,
    shortlist_all,
)
from workshop.product.blueprints import (
    PLAYTHING_LANES,
    POST_DELIVERY_REVIEWS,
    ReviewsPolicy,
    TOY_TASKS,
    WORKSHOP_JOBS,
    ToyBlueprint,
    ToyTask,
    playful_make_request,
)
from workshop.workflow.engine import (
    CUSTOMIZATION_LEVELS,
    ReleaseJob,
    InventJob,
    Workshop,
    WorkshopTools,
)
from workshop.errors import (
    AmbiguousEffectError,
    AmbiguousSendError,
    EffectError,
    ReceiptError,
    SendError,
    StampError,
    WorkshopError,
)
from workshop.workflow.lifecycle import GatePolicy, Pipeline, PipelineSpec
from workshop.contributors.manifest import (
    WORKSHOP_FEATURES,
    InventorManifest,
    discover_inventors,
    load_manifest,
)
from workshop.make.provenance import MAKER_MARK_MODES, MakerMark
from workshop.integrations.receipts import (
    PublicationOutcome,
    PublicationReceipt,
    Receipt,
    SendResult,
    Stamp,
)
from workshop.playtest.evidence import (
    GateResult,
    InspectionResult,
    PlaytestResult,
)
from workshop.artifacts.pack import (
    Artifact,
    ArtifactPlan,
    PackPlan,
    PackedArtifact,
    bundle_artifact,
    inspect_artifact,
    inspect_pack,
    pack_artifact,
    plan_artifact,
    plan_pack,
    seal_artifact,
)
from workshop.integrations.ports import (
    AgentPort,
    CadPort,
    CadVerifierPort,
    DeliveryPort,
    EvaluatorPort,
    LaunchPort,
)
from workshop.integrations.send import DEFAULT_SHOP_API, HttpResponse, Sender, ShopDoor
from workshop.integrations.shop import ShopReleaseWriter
from workshop.runtime.effects import Runtime
from workshop.runtime.reward import RewardLoopResult, RewardSignal, RewardStep, run_reward_loop
from workshop.integrations.launch import DEFAULT_PORTAL_API, Launchpad, Portal, inspect_publish_packet
from workshop.artifacts.schema_registry import discover_schemas, resolve_schemas_root
from workshop.contributors.scaffold import create_inventor
from workshop.make.skill_registry import (
    SkillFingerprint,
    discover_skills,
    fingerprint_skill_tree,
)
from workshop.runtime.store import InventorStore
from workshop.contributors.taste import (
    Taste,
    TasteHeader,
    TasteProfile,
    load_taste,
    load_taste_header,
    load_taste_profile,
)

__all__ = [
    # Toy Workshop 0.5 canonical surface.
    "ClassicEvidenceProvider",
    "MOVING_MACHINE_BINDING_KIND",
    "MOVING_MACHINE_BINDING_VERSION",
    "MovingMachineVerification",
    "PinnedCheckersRulesProvider",
    "PreparedLaneRelease",
    "ProviderIdentity",
    "PublicScienceSource",
    "ScienceAccuracyCase",
    "ScienceComprehensionTrace",
    "ScienceEvidenceProvider",
    "ScienceSimplificationCheck",
    "ScienceVerification",
    "WorkshopLanePlaytestProviders",
    "WorkshopMovingMachineVerifier",
    "WorldConsentRecord",
    "WorldEvidenceProvider",
    "WorldLikenessCase",
    "WorldReferenceMaterial",
    "WorldVerification",
    "workshop_pinned_wear_model",
    "Adapter",
    "AmbiguousEffectError",
    "Artifact",
    "ArtifactManifest",
    "ArtifactPlan",
    "attribute_product_description",
    "CadBuildResult",
    "CadReleaseBundle",
    "CapabilityReleaseProof",
    "CatalogPage",
    "CodexInventor",
    "CUSTOMIZATION_LEVELS",
    "CustomerReview",
    "DefaultDeliver",
    "DefaultRelease",
    "DeliverContext",
    "Delivered",
    "ReleaseContext",
    "ReleaseJob",
    "ReleaseSiteWriter",
    "InventContext",
    "Invented",
    "InventJob",
    "InventResearch",
    "InventResearchProvider",
    "InventResearchSource",
    "InventResearchUnavailable",
    "EffectError",
    "ExecutableGame",
    "Feedback",
    "FinalistContext",
    "GameTrace",
    "InventorManifest",
    "InventorAssignment",
    "InventorCard",
    "InventorCatalog",
    "InventorFinalist",
    "InventorRetriever",
    "InventorRetrieverRequired",
    "KernelBodyObservation",
    "LeagueConfig",
    "LeagueReport",
    "MAKER_MARK_MODES",
    "MakeResult",
    "Made",
    "MakeContext",
    "MakerMark",
    "Need",
    "NoInventorFit",
    "PLAYTHING_LANES",
    "POST_DELIVERY_REVIEWS",
    "PlayerPolicy",
    "Playtest",
    "PlaytestContext",
    "PlaytestPolicy",
    "PlaytestResult",
    "Playtested",
    "ProductRelease",
    "RandomPlayer",
    "ReleaseProofSource",
    "ReviewsPolicy",
    "RewardLoopResult",
    "RewardSignal",
    "RewardStep",
    "Receipt",
    "ReceiptError",
    "SealedDraft",
    "Runtime",
    "RoutingContext",
    "RoutingDecision",
    "Shortlist",
    "SkillFingerprint",
    "StlInspectionLimits",
    "StlPathInspectionError",
    "StlTopologyReceipt",
    "Taste",
    "TasteHeader",
    "TasteFit",
    "TasteJudge",
    "TasteJudgeRequired",
    "WorkshopManager",
    "TOY_TASKS",
    "ToyBlueprint",
    "ToyTask",
    "WaitingFor",
    "Wish",
    "WORKSHOP_JOBS",
    "Workbench",
    "Workshop",
    "WorkshopRun",
    "WorkshopTools",
    "Workflow",
    "WorkflowSpec",
    "WorkshopError",
    "bundle_artifact",
    "create_assignment",
    "create_inventor",
    "create_shortlist",
    "dispatch_assignment",
    "discover_inventor_catalog",
    "discover_inventors",
    "discover_schemas",
    "discover_skills",
    "fingerprint_skill_tree",
    "generate_wish_id",
    "fits_bed_envelope",
    "inspect_artifact",
    "inspect_stl_path",
    "inspect_stl_topology",
    "load_manifest",
    "load_sealed_draft",
    "load_finalists",
    "load_taste",
    "load_taste_header",
    "plan_artifact",
    "playful_make_request",
    "playtest_release_needs",
    "publish_sealed_draft",
    "resolve_schemas_root",
    "retrieve_shortlist",
    "run_game",
    "run_league",
    "run_reward_loop",
    "seal_artifact",
    "select_inventor",
    "shortlist_all",
    # Compatibility surface for Workshop 0.3 and older callers.
    "AgentPort",
    "AmbiguousSendError",
    "CadDoor",
    "CadInspectionDoor",
    "CadPort",
    "CadVerifierPort",
    "CanonicalSlugDoor",
    "Clockwork",
    "CreationBrief",
    "CreationResult",
    "DEFAULT_PORTAL_API",
    "DEFAULT_SHOP_API",
    "DeliveryDoor",
    "DeliveryPort",
    "EvaluatorPort",
    "Forge",
    "GatePolicy",
    "GateResult",
    "HttpResponse",
    "Inspection",
    "InspectionDoor",
    "InspectionPolicy",
    "InspectionResult",
    "InventorStore",
    "LaunchPort",
    "Launchpad",
    "ModelDoor",
    "PackPlan",
    "PackedArtifact",
    "Pipeline",
    "PipelineSpec",
    "Portal",
    "ProductForge",
    "PublicationOutcome",
    "PublicationReceipt",
    "SendDoor",
    "SendError",
    "SendResult",
    "Sender",
    "ShopDoor",
    "ShopReleaseWriter",
    "ShopDoorProtocol",
    "Stamp",
    "StampError",
    "TasteProfile",
    "WORKSHOP_FEATURES",
    "build_artifact_manifest",
    "build_pack",
    "build_publish_packet",
    "inspect_pack",
    "inspect_publish_packet",
    "load_taste_profile",
    "pack_artifact",
    "plan_pack",
]

__version__ = "0.6.0"
