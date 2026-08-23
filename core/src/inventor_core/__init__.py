"""Durable primitives shared by autonomous inventor implementations.

The package intentionally depends only on Python's standard library.  An
inventor may use any model, CAD stack, or scheduler it wants; core owns the
small set of facts that must remain true across all of them.
"""

from .artifacts import ArtifactManifest, build_artifact_manifest, build_publish_packet
from .cad import CadReleaseBundle
from .lifecycle import GatePolicy, Pipeline, PipelineSpec
from .manifest import InventorManifest, discover_inventors, load_manifest
from .models import GateResult, PublicationOutcome, PublicationReceipt
from .ports import (
    AgentPort,
    CadPort,
    CadVerifierPort,
    EvaluatorPort,
    FulfillmentPort,
    PublisherPort,
)
from .panda import (
    HttpResponse,
    PandaClient,
    PandaPublicationCoordinator,
    inspect_publish_packet,
)
from .store import InventorStore

__all__ = [
    "ArtifactManifest",
    "AgentPort",
    "CadPort",
    "CadReleaseBundle",
    "CadVerifierPort",
    "EvaluatorPort",
    "FulfillmentPort",
    "GateResult",
    "GatePolicy",
    "InventorManifest",
    "InventorStore",
    "HttpResponse",
    "PandaClient",
    "PandaPublicationCoordinator",
    "Pipeline",
    "PipelineSpec",
    "PublicationReceipt",
    "PublicationOutcome",
    "PublisherPort",
    "build_artifact_manifest",
    "build_publish_packet",
    "discover_inventors",
    "inspect_publish_packet",
    "load_manifest",
]

__version__ = "0.1.0"
