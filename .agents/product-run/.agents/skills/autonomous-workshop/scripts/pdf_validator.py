#!/usr/bin/env python3
"""Resource-bounded structural and render validation for one static PDF manual.

This file is immutable product-run tooling.  Both the trusted Workshop host and
the materialized stage finalizer execute these exact bytes in a short-lived
subprocess.  Resource limits are installed before either PDF parser is imported
or any untrusted PDF bytes are read.
"""

from __future__ import annotations

import io
import json
import logging
import math
import os
import signal
import sys
from collections.abc import Mapping
from typing import Any


MAX_PDF_BYTES = 16 * 1024 * 1024
MAX_PDF_PAGES = 64
MAX_PDF_OBJECTS = 50_000
MAX_PDF_GRAPH_NODES = 200_000
MAX_PDF_GRAPH_DEPTH = 64
MAX_PDF_CONTAINER_ITEMS = 4_096
MAX_PDF_STREAM_BYTES = 8 * 1024 * 1024
MAX_PDF_TOTAL_STREAM_BYTES = 32 * 1024 * 1024
MAX_PDF_PAGE_CONTENT_BYTES = 4 * 1024 * 1024
MAX_PDF_TOTAL_PAGE_CONTENT_BYTES = 16 * 1024 * 1024
MAX_PDF_IMAGE_DIMENSION = 8_192
MAX_PDF_IMAGE_PIXELS = 32_000_000
MAX_PDF_TOTAL_IMAGE_PIXELS = 64_000_000
MAX_PDF_EXTRACTED_TEXT_CHARACTERS = 4 * 1024 * 1024
MAX_PDF_FILTER_CHAIN = 8
MAX_RENDER_DIMENSION = 1_536
MAX_RENDER_PIXELS = 4_000_000
# Darwin reserves a very large virtual address range before this script starts.
# Its unbounded address-family limits are handled explicitly below; finite
# inherited limits are still tightened to this ceiling.  Linux uses the smaller
# ceiling as an additional hostile-input bound.
MAX_LINUX_PROCESS_ADDRESS_BYTES = 384 * 1024 * 1024
MAX_DARWIN_PROCESS_ADDRESS_BYTES = 40 * 1024 * 1024 * 1024
MAX_PROCESS_CPU_SECONDS = 6
MAX_PROCESS_WALL_SECONDS = 12
PDF_WORD_RE_MINIMUM = 4

FORBIDDEN_KEYS = frozenset(
    (
        "/A",
        "/AA",
        "/AcroForm",
        "/AF",
        "/Annots",
        "/Collection",
        "/DOS",
        "/EF",
        "/EmbeddedFiles",
        "/F",
        "/FDecodeParms",
        "/FFilter",
        "/FS",
        "/ImportData",
        "/JavaScript",
        "/JS",
        "/Launch",
        "/Mac",
        "/OpenAction",
        "/OPI",
        "/Ref",
        "/RichMedia",
        "/SubmitForm",
        "/UF",
        "/Unix",
        "/URI",
        "/URL",
        "/XFA",
    )
)
FORBIDDEN_ACTIONS = frozenset(
    (
        "/GoTo",
        "/GoTo3DView",
        "/GoToE",
        "/GoToR",
        "/Hide",
        "/ImportData",
        "/JavaScript",
        "/Launch",
        "/Movie",
        "/Named",
        "/Rendition",
        "/ResetForm",
        "/RichMediaExecute",
        "/SetOCGState",
        "/Sound",
        "/SubmitForm",
        "/Thread",
        "/Trans",
        "/URI",
    )
)
FORBIDDEN_TYPES = frozenset(
    (
        "/Action",
        "/Annot",
        "/EmbeddedFile",
        "/Filespec",
        "/OPI",
        "/Rendition",
    )
)
FORBIDDEN_SUBTYPES = frozenset(
    (
        "/3D",
        "/Caret",
        "/Circle",
        "/FileAttachment",
        "/FreeText",
        "/GoTo3DView",
        "/Highlight",
        "/Ink",
        "/Line",
        "/Link",
        "/Movie",
        "/PolyLine",
        "/Polygon",
        "/Popup",
        "/PrinterMark",
        "/Projection",
        "/PS",
        "/Redact",
        "/RichMedia",
        "/Screen",
        "/Sound",
        "/Square",
        "/Squiggly",
        "/Stamp",
        "/StrikeOut",
        "/Text",
        "/TrapNet",
        "/Underline",
        "/Watermark",
        "/Widget",
    )
)
PDF_FILTER_ALIASES = {
    "/A85": "/ASCII85Decode",
    "/AHx": "/ASCIIHexDecode",
    "/CCF": "/CCITTFaxDecode",
    "/DCT": "/DCTDecode",
    "/Fl": "/FlateDecode",
    "/LZW": "/LZWDecode",
    "/RL": "/RunLengthDecode",
}
BOUNDED_PDF_FILTERS = frozenset(
    (
        "/ASCII85Decode",
        "/ASCIIHexDecode",
        "/CCITTFaxDecode",
        "/DCTDecode",
        "/FlateDecode",
        "/JPXDecode",
        "/LZWDecode",
        "/RunLengthDecode",
    )
)
JPEG_START_OF_FRAME_MARKERS = frozenset(
    (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)
)


class PdfRejected(Exception):
    """One stable, public-safe reason the manual was rejected."""


def _resource_limit_signal(_signum: int, _frame: Any) -> None:
    raise PdfRejected("exceeded PDF validation resource limits")


def _cap_resource(
    resource_module: Any,
    name: str,
    maximum: int,
    *,
    required: bool,
    allow_unbounded: bool = False,
) -> bool:
    resource_id = getattr(resource_module, name, None)
    if resource_id is None:
        if required:
            raise PdfRejected("requires %s process resource limits" % name)
        return False
    try:
        current_soft, current_hard = resource_module.getrlimit(resource_id)
    except (OSError, TypeError, ValueError) as exc:
        raise PdfRejected("could not inspect %s process resource limit" % name) from exc
    infinity = resource_module.RLIM_INFINITY
    if allow_unbounded and current_soft == infinity and current_hard == infinity:
        return False
    soft = maximum if current_soft == infinity else min(current_soft, maximum)
    if current_hard != infinity:
        soft = min(soft, current_hard)
    # A soft limit bounds the worker without irreversibly lowering the hard
    # limit inherited by the tiny validation process.  Some POSIX platforms
    # reject a hard memory limit below their already-reserved address space.
    try:
        resource_module.setrlimit(resource_id, (soft, current_hard))
        observed_soft, _observed_hard = resource_module.getrlimit(resource_id)
    except (OSError, TypeError, ValueError) as exc:
        raise PdfRejected("could not install %s process resource limit" % name) from exc
    if observed_soft == infinity or observed_soft > soft:
        raise PdfRejected("could not verify %s process resource limit" % name)
    return True


def _install_resource_limits(
    *,
    _platform: str | None = None,
    _resource_module: Any = None,
    _signal_module: Any = None,
) -> None:
    selected_platform = sys.platform if _platform is None else _platform
    if selected_platform not in ("darwin", "linux"):
        raise PdfRejected("unsupported PDF validation platform: %s" % selected_platform)

    if _resource_module is None:
        try:
            import resource as _resource_module
        except ImportError as exc:  # pragma: no cover - fail closed off POSIX
            raise PdfRejected("requires POSIX process resource limits") from exc
    if _signal_module is None:
        _signal_module = signal

    if selected_platform == "linux":
        maximum_address_bytes = MAX_LINUX_PROCESS_ADDRESS_BYTES
        _cap_resource(
            _resource_module,
            "RLIMIT_AS",
            maximum_address_bytes,
            required=True,
        )
        for name in ("RLIMIT_DATA", "RLIMIT_RSS"):
            _cap_resource(
                _resource_module,
                name,
                maximum_address_bytes,
                required=False,
            )
    else:
        maximum_address_bytes = MAX_DARWIN_PROCESS_ADDRESS_BYTES
        # CPython on macOS rejects lowering the inherited infinite
        # address/data/RSS soft limits even when the hard limit remains
        # infinite.  Skip only that exact platform case.  Finite inherited
        # memory limits are preserved or tightened, and every other failure is
        # still a rejection.
        for name in ("RLIMIT_AS", "RLIMIT_DATA", "RLIMIT_RSS"):
            _cap_resource(
                _resource_module,
                name,
                maximum_address_bytes,
                required=False,
                allow_unbounded=True,
            )

    _cap_resource(
        _resource_module,
        "RLIMIT_CPU",
        MAX_PROCESS_CPU_SECONDS,
        required=True,
    )
    _cap_resource(
        _resource_module,
        "RLIMIT_NOFILE",
        64,
        required=True,
    )
    try:
        sigalrm = _signal_module.SIGALRM
        _signal_module.signal(sigalrm, _resource_limit_signal)
        sigxcpu = getattr(_signal_module, "SIGXCPU", None)
        if sigxcpu is not None:
            _signal_module.signal(sigxcpu, _resource_limit_signal)
        _signal_module.alarm(MAX_PROCESS_WALL_SECONDS)
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        raise PdfRejected("could not install PDF validation timeout") from exc


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise PdfRejected("%s must be a finite PDF number" % label)
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PdfRejected("%s must be a finite PDF number" % label) from exc
    if not math.isfinite(number):
        raise PdfRejected("%s must be a finite PDF number" % label)
    return number


def _positive_integer(value: Any, label: str, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or int(value) != float(value)
        or not 1 <= int(value) <= maximum
    ):
        raise PdfRejected("%s must be an integer from 1 through %d" % (label, maximum))
    return int(value)


def _page_box(box: Any, label: str, *, user_unit: float) -> None:
    try:
        coordinates = list(box)
    except (TypeError, ValueError) as exc:
        raise PdfRejected("%s must contain four finite coordinates" % label) from exc
    if len(coordinates) != 4:
        raise PdfRejected("%s must contain four finite coordinates" % label)
    left, bottom, right, top = (
        _finite_number(value, label) for value in coordinates
    )
    width = (right - left) * user_unit
    height = (top - bottom) * user_unit
    if not 18 <= width <= 14_400 or not 18 <= height <= 14_400:
        raise PdfRejected(
            "%s must describe a printable page from 18 through 14400 points" % label
        )


def _object_references(reader: Any, indirect_type: type[Any]) -> list[Any]:
    references: set[tuple[int, int]] = set()
    xref = getattr(reader, "xref", None)
    if not isinstance(xref, Mapping):
        raise PdfRejected("has an unavailable PDF object table")
    for generation, entries in xref.items():
        if type(generation) is not int or not isinstance(entries, Mapping):
            raise PdfRejected("has an invalid PDF object table")
        for object_number in entries:
            if type(object_number) is int and object_number > 0:
                references.add((object_number, generation))
    object_streams = getattr(reader, "xref_objStm", None)
    if isinstance(object_streams, Mapping):
        for object_number in object_streams:
            if type(object_number) is int and object_number > 0:
                references.add((object_number, 0))
    if len(references) > MAX_PDF_OBJECTS:
        raise PdfRejected("has too many PDF objects")
    return [
        indirect_type(object_number, generation, reader)
        for object_number, generation in sorted(references)
    ]


def _preflight_page_tree(reader: Any, indirect_type: type[Any]) -> int:
    try:
        catalog = reader.trailer["/Root"]
        if isinstance(catalog, indirect_type):
            catalog = catalog.get_object()
        pages = catalog["/Pages"]
    except Exception as exc:
        raise PdfRejected("has an unreadable page tree") from exc

    seen_indirect: set[tuple[int, int]] = set()
    seen_direct: set[int] = set()

    def walk(value: Any, depth: int) -> int:
        if depth > MAX_PDF_GRAPH_DEPTH:
            raise PdfRejected("page tree is too deep")
        if isinstance(value, indirect_type):
            identity = (value.idnum, value.generation)
            if identity in seen_indirect:
                raise PdfRejected("page tree contains a cycle or reused node")
            seen_indirect.add(identity)
            try:
                value = value.get_object()
            except Exception as exc:
                raise PdfRejected("has an unreadable page-tree object") from exc
        if not isinstance(value, Mapping):
            raise PdfRejected("page tree contains a non-dictionary node")
        identity = id(value)
        if identity in seen_direct:
            raise PdfRejected("page tree contains a cycle or reused node")
        seen_direct.add(identity)
        node_type = str(value.get("/Type", ""))
        if node_type == "/Page":
            return 1
        if node_type != "/Pages":
            raise PdfRejected("page tree contains an invalid node")
        kids = value.get("/Kids")
        if isinstance(kids, indirect_type):
            kids = kids.get_object()
        if not isinstance(kids, (list, tuple)) or not 1 <= len(kids) <= MAX_PDF_PAGES:
            raise PdfRejected("must contain 1 through 64 pages")
        actual = 0
        for child in kids:
            actual += walk(child, depth + 1)
            if actual > MAX_PDF_PAGES:
                raise PdfRejected("must contain 1 through 64 pages")
        declared = _positive_integer(
            value.get("/Count"), "page-tree Count", MAX_PDF_PAGES
        )
        if declared != actual:
            raise PdfRejected("page-tree Count differs from its exact pages")
        return actual

    count = walk(pages, 0)
    if not 1 <= count <= MAX_PDF_PAGES:
        raise PdfRejected("must contain 1 through 64 pages")
    return count


def _static_dictionary(value: Mapping[str, Any]) -> tuple[str, str]:
    names = {str(key) for key in value}
    forbidden = sorted(names & FORBIDDEN_KEYS)
    if forbidden:
        raise PdfRejected(
            "contains active or external PDF features (actions or annotations): %s"
            % forbidden
        )
    transition = value.get("/Trans")
    if transition is not None and (
        not isinstance(transition, Mapping) or bool(transition)
    ):
        raise PdfRejected("contains an active page transition")
    action = str(value.get("/S", ""))
    if action in FORBIDDEN_ACTIONS:
        raise PdfRejected("contains a forbidden PDF action: %s" % action)
    object_type = str(value.get("/Type", ""))
    if object_type in FORBIDDEN_TYPES:
        raise PdfRejected("contains a forbidden PDF object: %s" % object_type)
    subtype = str(value.get("/Subtype", ""))
    if subtype in FORBIDDEN_SUBTYPES:
        raise PdfRejected("contains a forbidden PDF subtype: %s" % subtype)
    return object_type, subtype


def _stream_filters(value: Any, indirect_type: type[Any]) -> tuple[str, ...]:
    filters = value.get("/Filter")
    if filters is None:
        return ()
    if isinstance(filters, indirect_type):
        try:
            filters = filters.get_object()
        except Exception as exc:
            raise PdfRejected("contains an unreadable PDF stream filter") from exc
    if isinstance(filters, str):
        raw_filters = [filters]
    elif isinstance(filters, (list, tuple)):
        if not 1 <= len(filters) <= MAX_PDF_FILTER_CHAIN:
            raise PdfRejected("contains an oversized PDF stream filter chain")
        raw_filters = list(filters)
    else:
        raise PdfRejected("contains an invalid PDF stream filter")
    result: list[str] = []
    for raw_filter in raw_filters:
        if isinstance(raw_filter, indirect_type):
            try:
                raw_filter = raw_filter.get_object()
            except Exception as exc:
                raise PdfRejected("contains an unreadable PDF stream filter") from exc
        if not isinstance(raw_filter, str):
            raise PdfRejected("contains an invalid PDF stream filter")
        name = PDF_FILTER_ALIASES.get(str(raw_filter), str(raw_filter))
        if name == "/JBIG2Decode":
            raise PdfRejected("contains the unsupported external JBIG2 PDF filter")
        if name == "/Crypt" or name not in BOUNDED_PDF_FILTERS:
            raise PdfRejected("contains an unsupported PDF stream filter: %s" % name)
        result.append(name)
    return tuple(result)


def _preflight_stream_decode(value: Any, indirect_type: type[Any]) -> None:
    raw_data = getattr(value, "_data", None)
    if not isinstance(raw_data, bytes):
        raise PdfRejected("contains an unavailable encoded PDF stream")
    maximum_output = len(raw_data)
    for filter_name in _stream_filters(value, indirect_type):
        if filter_name in ("/FlateDecode", "/LZWDecode", "/RunLengthDecode"):
            # pypdf's corresponding decoder caps are set before PdfReader is
            # constructed.  Treat their maximum possible result as the bound
            # for the next filter in a chain.
            maximum_output = MAX_PDF_STREAM_BYTES
        elif filter_name == "/ASCII85Decode":
            # Adobe ASCII85's single-byte ``z`` shorthand expands to four
            # NUL bytes, so malformed input can expand fourfold rather than
            # following the usual 5-to-4 ratio.
            maximum_output *= 4
        elif filter_name == "/ASCIIHexDecode":
            maximum_output = math.ceil(maximum_output / 2)
        elif filter_name == "/CCITTFaxDecode":
            maximum_output += 512
        # DCT and JPX remain encoded when pypdf validates stream structure.
        if maximum_output > MAX_PDF_STREAM_BYTES:
            raise PdfRejected("contains a PDF stream whose decoded bound is too large")


def _jpeg_dimensions(content: bytes) -> tuple[int, int]:
    if not content.startswith(b"\xff\xd8"):
        raise PdfRejected("DCT image data must have a JPEG header")
    position = 2
    while position < len(content):
        if content[position] != 0xFF:
            raise PdfRejected("DCT image data has an invalid JPEG marker")
        while position < len(content) and content[position] == 0xFF:
            position += 1
        if position >= len(content):
            break
        marker = content[position]
        position += 1
        if marker in (0x01, 0xD8) or 0xD0 <= marker <= 0xD7:
            continue
        if marker in (0x00, 0xD9, 0xDA) or position + 2 > len(content):
            break
        segment_length = int.from_bytes(content[position : position + 2], "big")
        if segment_length < 2 or position + segment_length > len(content):
            raise PdfRejected("DCT image data has an invalid JPEG segment")
        if marker in JPEG_START_OF_FRAME_MARKERS:
            if segment_length < 8:
                raise PdfRejected("DCT image data has an invalid JPEG frame")
            height = int.from_bytes(content[position + 3 : position + 5], "big")
            width = int.from_bytes(content[position + 5 : position + 7], "big")
            if width < 1 or height < 1:
                raise PdfRejected("DCT image data has unbounded JPEG dimensions")
            return width, height
        position += segment_length
    raise PdfRejected("DCT image data lacks bounded JPEG dimensions")


def _content_operations(value: Any, label: str) -> list[Any]:
    try:
        operations = value.operations
    except Exception as exc:
        raise PdfRejected("%s content operators are unreadable" % label) from exc
    if any(operator == b"INLINE IMAGE" for _, operator in operations):
        raise PdfRejected(
            "%s contains an unsupported inline image; use an image XObject" % label
        )
    return operations


def _validate_nested_content_stream(
    value: Any,
    reader: Any,
    content_stream_type: type[Any],
    label: str,
) -> None:
    try:
        decoded = value.get_data()
    except Exception as exc:
        raise PdfRejected("%s is unreadable" % label) from exc
    if len(decoded) > MAX_PDF_PAGE_CONTENT_BYTES:
        raise PdfRejected("%s is too large" % label)
    try:
        content = content_stream_type(value, reader)
    except Exception as exc:
        raise PdfRejected("%s content operators are unreadable" % label) from exc
    _content_operations(content, label)


def _inspect_object_graph(
    reader: Any,
    references: list[Any],
    indirect_type: type[Any],
    stream_type: type[Any],
    content_stream_type: type[Any],
) -> None:
    stack: list[tuple[Any, int]] = [(reader.trailer, 0)]
    stack.extend((reference, 0) for reference in references)
    seen_indirect: set[tuple[int, int]] = set()
    seen_direct: set[int] = set()
    visited_nodes = 0
    total_stream_bytes = 0
    total_image_pixels = 0
    nested_content_streams: dict[int, tuple[Any, str]] = {}
    while stack:
        value, depth = stack.pop()
        if depth > MAX_PDF_GRAPH_DEPTH:
            raise PdfRejected("object graph is too deep")
        visited_nodes += 1
        if visited_nodes > MAX_PDF_GRAPH_NODES:
            raise PdfRejected("object graph is too large")
        if isinstance(value, indirect_type):
            identity = (value.idnum, value.generation)
            if identity in seen_indirect:
                continue
            seen_indirect.add(identity)
            if len(seen_indirect) > MAX_PDF_OBJECTS:
                raise PdfRejected("has too many PDF objects")
            try:
                stack.append((value.get_object(), depth + 1))
            except Exception as exc:
                raise PdfRejected("contains an unreadable PDF object") from exc
            continue
        if isinstance(value, Mapping):
            identity = id(value)
            if identity in seen_direct:
                continue
            seen_direct.add(identity)
            if len(value) > MAX_PDF_CONTAINER_ITEMS:
                raise PdfRejected("contains an oversized PDF dictionary")
            object_type, subtype = _static_dictionary(value)
            if subtype in ("/Form", "/Image") and not isinstance(value, stream_type):
                raise PdfRejected("%s XObject must be a PDF stream" % subtype)
            if (
                object_type == "/Pattern"
                and value.get("/PatternType") == 1
                and not isinstance(value, stream_type)
            ):
                raise PdfRejected("tiling Pattern must be a PDF stream")
            if isinstance(value, stream_type):
                _preflight_stream_decode(value, indirect_type)
                try:
                    decoded = value.get_data()
                except Exception as exc:
                    raise PdfRejected(
                        "contains an unreadable or oversized PDF stream"
                    ) from exc
                if len(decoded) > MAX_PDF_STREAM_BYTES:
                    raise PdfRejected("contains a decoded PDF stream that is too large")
                total_stream_bytes += len(decoded)
                if total_stream_bytes > MAX_PDF_TOTAL_STREAM_BYTES:
                    raise PdfRejected("decoded PDF streams are too large in total")
                if subtype == "/Form" or (
                    object_type == "/Pattern" and value.get("/PatternType") == 1
                ):
                    nested_content_streams[id(value)] = (
                        value,
                        "nested PDF content stream",
                    )
            if subtype == "/Image":
                width = _positive_integer(
                    value.get("/Width"), "image Width", MAX_PDF_IMAGE_DIMENSION
                )
                height = _positive_integer(
                    value.get("/Height"), "image Height", MAX_PDF_IMAGE_DIMENSION
                )
                pixels = width * height
                if pixels > MAX_PDF_IMAGE_PIXELS:
                    raise PdfRejected("contains an image with too many pixels")
                total_image_pixels += pixels
                if total_image_pixels > MAX_PDF_TOTAL_IMAGE_PIXELS:
                    raise PdfRejected("contains too many image pixels in total")
                filters = _stream_filters(value, indirect_type)
                if "/JPXDecode" in filters:
                    raise PdfRejected("contains an unsupported JPX image encoding")
                if "/DCTDecode" in filters:
                    if filters.count("/DCTDecode") != 1 or filters[-1] != "/DCTDecode":
                        raise PdfRejected("contains an invalid DCT image filter chain")
                    jpeg_width, jpeg_height = _jpeg_dimensions(decoded)
                    if (jpeg_width, jpeg_height) != (width, height):
                        raise PdfRejected(
                            "DCT image JPEG dimensions differ from its PDF dimensions"
                        )
            if subtype == "/Type3":
                char_procs = value.get("/CharProcs")
                if isinstance(char_procs, indirect_type):
                    try:
                        char_procs = char_procs.get_object()
                    except Exception as exc:
                        raise PdfRejected("Type3 CharProcs are unreadable") from exc
                if not isinstance(char_procs, Mapping):
                    raise PdfRejected("Type3 CharProcs must be a PDF dictionary")
                if len(char_procs) > MAX_PDF_CONTAINER_ITEMS:
                    raise PdfRejected("Type3 CharProcs are too large")
                for name, char_proc in char_procs.items():
                    if isinstance(char_proc, indirect_type):
                        try:
                            char_proc = char_proc.get_object()
                        except Exception as exc:
                            raise PdfRejected("Type3 CharProc is unreadable") from exc
                    if not isinstance(char_proc, stream_type):
                        raise PdfRejected("Type3 CharProc must be a PDF stream")
                    nested_content_streams[id(char_proc)] = (
                        char_proc,
                        "Type3 CharProc %s" % str(name),
                    )
            stack.extend((item, depth + 1) for item in value.values())
            continue
        if isinstance(value, (list, tuple)):
            identity = id(value)
            if identity in seen_direct:
                continue
            seen_direct.add(identity)
            if len(value) > MAX_PDF_CONTAINER_ITEMS:
                raise PdfRejected("contains an oversized PDF array")
            stack.extend((item, depth + 1) for item in value)
    for content, label in nested_content_streams.values():
        _preflight_stream_decode(content, indirect_type)
        _validate_nested_content_stream(
            content,
            reader,
            content_stream_type,
            label,
        )


def _validate_pages(reader: Any, pages: list[Any]) -> None:
    extracted: list[str] = []
    extracted_characters = 0
    total_page_content = 0
    for index, page in enumerate(pages, start=1):
        label = "page %d" % index
        user_unit = _finite_number(page.get("/UserUnit", 1), label)
        if not 0 < user_unit <= 75_000:
            raise PdfRejected("%s UserUnit must be positive and bounded" % label)
        for box_name in ("mediabox", "cropbox", "bleedbox", "trimbox", "artbox"):
            _page_box(
                getattr(page, box_name),
                "%s %s" % (label, box_name),
                user_unit=user_unit,
            )
        rotation = page.get("/Rotate", 0)
        if (
            isinstance(rotation, bool)
            or not isinstance(rotation, (int, float))
            or not math.isfinite(float(rotation))
            or int(rotation) != float(rotation)
            or int(rotation) % 90
        ):
            raise PdfRejected("%s rotation must be a finite multiple of 90" % label)
        contents = page.get_contents()
        if contents is not None:
            try:
                decoded = contents.get_data()
            except Exception as exc:
                raise PdfRejected("%s content stream is unreadable" % label) from exc
            if len(decoded) > MAX_PDF_PAGE_CONTENT_BYTES:
                raise PdfRejected("%s content stream is too large" % label)
            total_page_content += len(decoded)
            if total_page_content > MAX_PDF_TOTAL_PAGE_CONTENT_BYTES:
                raise PdfRejected("decoded page content is too large")
            _content_operations(contents, label)
        try:
            text = page.extract_text()
        except Exception as exc:
            raise PdfRejected("%s text cannot be extracted" % label) from exc
        if not isinstance(text, str):
            raise PdfRejected("%s text cannot be extracted" % label)
        extracted_characters += len(text)
        if extracted_characters > MAX_PDF_EXTRACTED_TEXT_CHARACTERS:
            raise PdfRejected("extractable text is too large")
        extracted.append(text)

    text = "\n".join(extracted)
    alphanumeric = [character.casefold() for character in text if character.isalnum()]
    words = [word for word in text.split() if len(word.strip(".,:;!?()[]{}")) >= 2]
    if (
        len(alphanumeric) < 32
        or len(set(alphanumeric)) < 8
        or len(words) < PDF_WORD_RE_MINIMUM
    ):
        raise PdfRejected("must contain meaningful extractable text")


def _render_pages(content: bytes, expected_pages: int) -> None:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise PdfRejected(
            "validation requires the pypdfium2 runtime dependency"
        ) from exc
    try:
        document = pdfium.PdfDocument(content)
        try:
            if len(document) != expected_pages:
                raise PdfRejected("rendered page count differs from its page tree")
            for index in range(expected_pages):
                page = document[index]
                try:
                    width, height = page.get_size()
                    width = _finite_number(width, "rendered page width")
                    height = _finite_number(height, "rendered page height")
                    if width <= 0 or height <= 0:
                        raise PdfRejected("rendered page dimensions must be positive")
                    scale = min(1.0, MAX_RENDER_DIMENSION / max(width, height))
                    bitmap = page.render(scale=scale)
                    try:
                        bitmap_width = int(bitmap.width)
                        bitmap_height = int(bitmap.height)
                        if (
                            bitmap_width < 1
                            or bitmap_height < 1
                            or bitmap_width > MAX_RENDER_DIMENSION
                            or bitmap_height > MAX_RENDER_DIMENSION
                            or bitmap_width * bitmap_height > MAX_RENDER_PIXELS
                        ):
                            raise PdfRejected("rendered page bitmap is too large")
                    finally:
                        bitmap.close()
                finally:
                    page.close()
        finally:
            document.close()
    except PdfRejected:
        raise
    except Exception as exc:
        raise PdfRejected("cannot be rendered safely") from exc


def _validate(content: bytes) -> None:
    if not 1 <= len(content) <= MAX_PDF_BYTES:
        raise PdfRejected("must be non-empty and at most 16777216 bytes")
    if not content.startswith(b"%PDF-"):
        raise PdfRejected("must have a PDF header")
    eof = content.rfind(b"%%EOF")
    if eof < 0 or content[eof + len(b"%%EOF") :].strip():
        raise PdfRejected("must have a final PDF EOF marker")

    try:
        import pypdf.filters as pdf_filters
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
        from pypdf.generic import (
            ArrayObject,
            ContentStream,
            IndirectObject,
            StreamObject,
        )
    except ImportError as exc:
        raise PdfRejected("validation requires the pypdf runtime dependency") from exc
    required_filter_limits = (
        "FLATE_MAX_BUFFER_SIZE",
        "FLATE_MAX_ROW_LENGTH",
        "JBIG2_MAX_OUTPUT_LENGTH",
        "LZW_MAX_OUTPUT_LENGTH",
        "RUN_LENGTH_MAX_OUTPUT_LENGTH",
        "ZLIB_MAX_OUTPUT_LENGTH",
    )
    if any(not hasattr(pdf_filters, name) for name in required_filter_limits):
        raise PdfRejected("pypdf lacks required PDF stream resource controls")
    for name in required_filter_limits:
        setattr(pdf_filters, name, MAX_PDF_STREAM_BYTES + 1)
    if not hasattr(pdf_filters, "FLATE_MAX_COLUMNS"):
        raise PdfRejected("pypdf lacks required PDF stream resource controls")
    pdf_filters.FLATE_MAX_COLUMNS = MAX_PDF_IMAGE_DIMENSION
    if not hasattr(pdf_filters, "MAX_DECLARED_STREAM_LENGTH"):
        raise PdfRejected("pypdf lacks required PDF stream resource controls")
    pdf_filters.MAX_DECLARED_STREAM_LENGTH = MAX_PDF_BYTES

    original_array_append = ArrayObject.append

    def bounded_array_append(array: Any, item: Any) -> None:
        if len(array) >= MAX_PDF_CONTAINER_ITEMS:
            raise PdfReadError("PDF array exceeds the validation item limit")
        original_array_append(array, item)

    # Install the array bound before PdfReader parses even the Catalog or
    # page-tree /Kids object.  The ordinary post-parse graph check is too late
    # for a tiny file containing hundreds of thousands of repeated references.
    ArrayObject.append = bounded_array_append
    try:
        reader = PdfReader(io.BytesIO(content), strict=True)
    except Exception as exc:
        raise PdfRejected("cannot be parsed safely") from exc
    if reader.is_encrypted or reader.trailer.get("/Encrypt") is not None:
        raise PdfRejected("must be unencrypted")
    references = _object_references(reader, IndirectObject)
    page_count = _preflight_page_tree(reader, IndirectObject)
    _inspect_object_graph(
        reader,
        references,
        IndirectObject,
        StreamObject,
        ContentStream,
    )
    try:
        pages = list(reader.pages)
    except Exception as exc:
        raise PdfRejected("has an unreadable page tree") from exc
    if len(pages) != page_count:
        raise PdfRejected("page-tree Count differs from its exact pages")
    _validate_pages(reader, pages)
    _render_pages(content, page_count)


def _result(ok: bool, error: str | None) -> bytes:
    return json.dumps(
        {"error": error, "ok": ok},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> int:
    if sys.argv != [sys.argv[0], "--isolated-worker"]:
        os.write(1, _result(False, "validator invocation is invalid"))
        return 64
    try:
        _install_resource_limits()
        logging.disable(logging.CRITICAL)
        content = sys.stdin.buffer.read(MAX_PDF_BYTES + 1)
        _validate(content)
    except PdfRejected as exc:
        message = str(exc)
        if not message or len(message) > 1_000:
            message = "cannot be parsed and rendered safely"
        os.write(1, _result(False, message))
        return 2
    except (MemoryError, RecursionError):
        os.write(1, _result(False, "exceeded PDF validation resource limits"))
        return 2
    except BaseException:
        os.write(1, _result(False, "cannot be parsed and rendered safely"))
        return 2
    os.write(1, _result(True, None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
