"""The shared Workshop for autonomous inventors.

Customer-facing inventors keep the promise simple: Wish -> Wait -> Receive.
Developers compose the backstage work from Make, Inspect, Pack, and Send while
Taste guides invention and Clockwork keeps durable work moving.
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
from .clockwork import Clockwork, InspectionPolicy, Workflow, WorkflowSpec
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
from .inspection import Inspection
from .errors import AmbiguousSendError, SendError, StampError, WorkshopError
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
    PublicationOutcome,
    PublicationReceipt,
    SendResult,
    Stamp,
)
from .pack import PackPlan, PackedArtifact, inspect_pack, pack_artifact, plan_pack, seal_artifact
from .ports import (
    AgentPort,
    CadPort,
    CadVerifierPort,
    DeliveryPort,
    EvaluatorPort,
    LaunchPort,
)
from .send import DEFAULT_SHOP_API, HttpResponse, Sender, ShopDoor
from .launch import DEFAULT_PORTAL_API, Launchpad, Portal, inspect_publish_packet
from .schemas import discover_schemas, resolve_schemas_root
from .skills import SkillFingerprint, discover_skills, fingerprint_skill_tree
from .store import InventorStore
from .taste import Taste, TasteProfile, load_taste, load_taste_profile

__all__ = [
    # Workshop 0.3 canonical surface.
    "ArtifactManifest",
    "AmbiguousSendError",
    "CadBuildResult",
    "CadDoor",
    "CadInspectionDoor",
    "CadReleaseBundle",
    "Clockwork",
    "DEFAULT_SHOP_API",
    "DeliveryDoor",
    "HttpResponse",
    "Inspection",
    "InspectionDoor",
    "InspectionPolicy",
    "InspectionResult",
    "InventorManifest",
    "KernelBodyObservation",
    "MakeResult",
    "MAKER_MARK_MODES",
    "MakerMark",
    "ModelDoor",
    "PackedArtifact",
    "PackPlan",
    "SendResult",
    "SendDoor",
    "SendError",
    "Sender",
    "ShopDoor",
    "ShopDoorProtocol",
    "SkillFingerprint",
    "Stamp",
    "StampError",
    "StlInspectionLimits",
    "StlPathInspectionError",
    "StlTopologyReceipt",
    "Taste",
    "WORKSHOP_FEATURES",
    "Wish",
    "Workbench",
    "Workflow",
    "WorkflowSpec",
    "WorkshopError",
    "discover_inventors",
    "discover_skills",
    "discover_schemas",
    "fingerprint_skill_tree",
    "fits_bed_envelope",
    "inspect_pack",
    "inspect_stl_path",
    "inspect_stl_topology",
    "load_manifest",
    "load_taste",
    "pack_artifact",
    "plan_pack",
    "build_pack",
    "resolve_schemas_root",
    "seal_artifact",
    # Compatibility surface for Workshop 0.2/Foundation/Core callers.
    "AgentPort",
    "CadPort",
    "CadVerifierPort",
    "CreationBrief",
    "CreationResult",
    "DEFAULT_PORTAL_API",
    "DeliveryPort",
    "EvaluatorPort",
    "Forge",
    "GatePolicy",
    "GateResult",
    "InventorStore",
    "LaunchPort",
    "Launchpad",
    "Pipeline",
    "PipelineSpec",
    "Portal",
    "ProductForge",
    "PublicationOutcome",
    "PublicationReceipt",
    "TasteProfile",
    "build_artifact_manifest",
    "build_publish_packet",
    "inspect_publish_packet",
    "load_taste_profile",
]

__version__ = "0.3.0"
