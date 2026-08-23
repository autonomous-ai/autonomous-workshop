from __future__ import annotations

import os
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from cadpy.step_scene import LoadedStepScene, load_step_scene_from_xcaf_doc, step_file_hash
from cadpy.step_metadata import TEXT_TO_CAD_GENERATOR, inject_text_to_cad_step_metadata


def create_bin_xcaf_doc() -> Any:
    from OCP.BinXCAFDrivers import BinXCAFDrivers
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFApp import XCAFApp_Application
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    doc = TDocStd_Document(TCollection_ExtendedString("BinXCAF"))
    application = XCAFApp_Application.GetApplication_s()
    BinXCAFDrivers.DefineFormat_s(application)
    application.NewDocument(TCollection_ExtendedString("BinXCAF"), doc)
    application.InitDocument(doc)
    # 0.001 m per unit = millimetres (the STEP/XCAF working unit).
    XCAFDoc_DocumentTool.SetLengthUnit_s(doc, 0.001)
    return doc


def export_xcaf_doc_step_scene(
    doc: Any,
    output_path: Path,
    *,
    label: str | None = None,
    originating_system: str = "cadquery",
    text_to_cad_entry_kind: str | None = None,
    source_path: str | None = None,
    source_fingerprint: str | None = None,
    source_hash: str | None = None,
    logger: object | None = None,
) -> LoadedStepScene:
    step_hash = write_xcaf_doc_step_file(
        doc,
        output_path,
        label=label,
        originating_system=originating_system,
        text_to_cad_entry_kind=text_to_cad_entry_kind,
        source_path=source_path,
        source_fingerprint=source_fingerprint,
        source_hash=source_hash,
        logger=logger,
    )
    with (logger.timed(f"load scene from XCAF {output_path.name}") if logger is not None else nullcontext()):
        return load_step_scene_from_xcaf_doc(
            output_path,
            doc,
            step_hash=step_hash,
        )


def write_xcaf_doc_step_file(
    doc: Any,
    output_path: Path,
    *,
    label: str | None = None,
    originating_system: str = "cadquery",
    text_to_cad_entry_kind: str | None = None,
    source_path: str | None = None,
    source_fingerprint: str | None = None,
    source_hash: str | None = None,
    logger: object | None = None,
) -> str:
    from OCP.APIHeaderSection import APIHeaderSection_MakeHeader
    from OCP.IFSelect import IFSelect_ReturnStatus
    from OCP.IGESControl import IGESControl_Controller
    from OCP.Interface import Interface_Static
    from OCP.Message import Message, Message_Gravity
    from OCP.STEPCAFControl import STEPCAFControl_Controller, STEPCAFControl_Writer
    from OCP.STEPControl import STEPControl_Controller, STEPControl_StepModelType
    from OCP.TCollection import TCollection_HAsciiString
    from OCP.XSControl import XSControl_WorkSession

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    messenger = Message.DefaultMessenger_s()
    for printer in messenger.Printers():
        printer.SetTraceLevel(Message_Gravity(Message_Gravity.Message_Fail))

    session = XSControl_WorkSession()
    writer = STEPCAFControl_Writer(session, False)
    writer.SetColorMode(True)
    writer.SetLayerMode(True)
    writer.SetNameMode(True)

    header = APIHeaderSection_MakeHeader(writer.Writer().Model())
    if label:
        header.SetName(TCollection_HAsciiString(label))
    header.SetOriginatingSystem(
        TCollection_HAsciiString(TEXT_TO_CAD_GENERATOR if text_to_cad_entry_kind else originating_system)
    )

    STEPCAFControl_Controller.Init_s()
    STEPControl_Controller.Init_s()
    IGESControl_Controller.Init_s()
    Interface_Static.SetIVal_s("write.surfacecurve.mode", 1)
    # 0 == "Average" STEP write precision mode.
    Interface_Static.SetIVal_s("write.precision.mode", 0)
    with (logger.timed(f"transfer XCAF to STEP model {output_path.name}") if logger is not None else nullcontext()):
        writer.Transfer(doc, STEPControl_StepModelType.STEPControl_AsIs)

    with (logger.timed(f"write STEP file {output_path.name}") if logger is not None else nullcontext()):
        if writer.Write(os.fspath(output_path)) != IFSelect_ReturnStatus.IFSelect_RetDone:
            raise RuntimeError(f"Failed to write STEP file: {output_path}")
    if not output_path.exists() or output_path.stat().st_size <= 0:
        raise RuntimeError(f"STEP export did not create {output_path}")
    if text_to_cad_entry_kind:
        with (logger.timed(f"inject STEP metadata {output_path.name}") if logger is not None else nullcontext()):
            inject_text_to_cad_step_metadata(
                output_path,
                entry_kind=text_to_cad_entry_kind,
                source_path=source_path,
                source_fingerprint=source_fingerprint,
                source_hash=source_hash,
            )
    return step_file_hash(output_path)
