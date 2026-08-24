"""The shared Workshop for autonomous inventors.

The public model is deliberately small: Wish and Taste guide a Make/Playtest
loop. Artifact, Runtime, Adapter, and Receipt are literal implementation types,
not extra invention stages.
"""

from .artifacts import (
    ArtifactManifest,
    build_artifact_manifest,
    build_pack,
    build_publish_packet,
)
from .cad import (
    CadReleaseBundle,
    KernelBodyObservation,
    StlInspectionLimits,
    StlPathInspectionError,
    StlTopologyReceipt,
    fits_bed_envelope,
    inspect_stl_path,
    inspect_stl_topology,
)
from .clockwork import (
    Clockwork,
    InspectionPolicy,
    PlaytestPolicy,
    Workflow,
    WorkflowSpec,
)
from .make import (
    CadBuildResult,
    CreationBrief,
    CreationResult,
    Forge,
    MakeResult,
    ProductForge,
    Wish,
    Workbench,
)
from .doors import (
    CadDoor,
    CadInspectionDoor,
    DeliveryDoor,
    InspectionDoor,
    ModelDoor,
    SendDoor,
    ShopDoorProtocol,
)
from .integrations import Adapter
from .inspection import Inspection
from .playtest import Playtest
from .errors import (
    AmbiguousEffectError,
    AmbiguousSendError,
    EffectError,
    ReceiptError,
    SendError,
    StampError,
    WorkshopError,
)
from .lifecycle import GatePolicy, Pipeline, PipelineSpec
from .manifest import (
    WORKSHOP_FEATURES,
    InventorManifest,
    discover_inventors,
    load_manifest,
)
from .maker_mark import MAKER_MARK_MODES, MakerMark
from .models import (
    GateResult,
    InspectionResult,
    PlaytestResult,
    PublicationOutcome,
    PublicationReceipt,
    Receipt,
    SendResult,
    Stamp,
)
from .pack import (
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
from .ports import (
    AgentPort,
    CadPort,
    CadVerifierPort,
    DeliveryPort,
    EvaluatorPort,
    LaunchPort,
)
from .send import DEFAULT_SHOP_API, HttpResponse, Sender, ShopDoor
from .runtime import Runtime
from .launch import DEFAULT_PORTAL_API, Launchpad, Portal, inspect_publish_packet
from .schemas import discover_schemas, resolve_schemas_root
from .skills import SkillFingerprint, discover_skills, fingerprint_skill_tree
from .store import InventorStore
from .taste import Taste, TasteProfile, load_taste, load_taste_profile

__all__ = [
    # Workshop 0.4 canonical surface.
    "Adapter",
    "AmbiguousEffectError",
    "Artifact",
    "ArtifactManifest",
    "ArtifactPlan",
    "CadBuildResult",
    "CadReleaseBundle",
    "EffectError",
    "InventorManifest",
    "KernelBodyObservation",
    "MAKER_MARK_MODES",
    "MakeResult",
    "MakerMark",
    "Playtest",
    "PlaytestPolicy",
    "PlaytestResult",
    "Receipt",
    "ReceiptError",
    "Runtime",
    "SkillFingerprint",
    "StlInspectionLimits",
    "StlPathInspectionError",
    "StlTopologyReceipt",
    "Taste",
    "Wish",
    "Workbench",
    "Workflow",
    "WorkflowSpec",
    "WorkshopError",
    "bundle_artifact",
    "discover_inventors",
    "discover_schemas",
    "discover_skills",
    "fingerprint_skill_tree",
    "fits_bed_envelope",
    "inspect_artifact",
    "inspect_stl_path",
    "inspect_stl_topology",
    "load_manifest",
    "load_taste",
    "plan_artifact",
    "resolve_schemas_root",
    "seal_artifact",
    # Compatibility surface for Workshop 0.3 and older callers.
    "AgentPort",
    "AmbiguousSendError",
    "CadDoor",
    "CadInspectionDoor",
    "CadPort",
    "CadVerifierPort",
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

__version__ = "0.4.0"
