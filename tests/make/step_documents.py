"""Deterministic STEP fixtures shaped like the Open CASCADE writer's output."""

from __future__ import annotations


def srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def linear_channels(hex_color: str):
    return tuple(
        srgb_to_linear(int(hex_color[index : index + 2], 16) / 255.0)
        for index in (1, 3, 5)
    )


def srgb_channels(hex_color: str):
    """The raw channels build123d seals for ``Color(r, g, b)`` picked as sRGB."""

    return tuple(int(hex_color[index : index + 2], 16) / 255.0 for index in (1, 3, 5))


def step_document(parts, *, colours=True) -> bytes:
    """Build a STEP shaped exactly like the Open CASCADE writer's output."""

    lines = [
        "ISO-10303-21;",
        "HEADER;",
        "FILE_DESCRIPTION(('Open CASCADE Model'),'2;1');",
        "FILE_NAME('demo','1970-01-01T00:00:00',('Author'),(",
        "    'Open CASCADE'),'Open CASCADE STEP processor 7.9','cadgen','Unknown'",
        "  );",
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));",
        "ENDSEC;",
        "DATA;",
        "#1 = APPLICATION_CONTEXT('core data');",
        "#2 = PRODUCT_DEFINITION_CONTEXT('part definition',#1,'design');",
        "#3 = PRODUCT_CONTEXT('',#1,'mechanical');",
        "#4 = ( GEOMETRIC_REPRESENTATION_CONTEXT(3)",
        "GLOBAL_UNIT_ASSIGNED_CONTEXT((#5)) REPRESENTATION_CONTEXT('',''));",
        "#5 = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) );",
    ]
    identifier = 10
    for name, colour in parts:
        base = identifier
        lines.extend(
            [
                "#%d = SHAPE_DEFINITION_REPRESENTATION(#%d,#%d);" % (base, base + 1, base + 5),
                "#%d = PRODUCT_DEFINITION_SHAPE('','',#%d);" % (base + 1, base + 2),
                "#%d = PRODUCT_DEFINITION('design','',#%d,#2);" % (base + 2, base + 3),
                "#%d = PRODUCT_DEFINITION_FORMATION('','',#%d);" % (base + 3, base + 4),
                "#%d = PRODUCT('%s','%s','',(#3));" % (base + 4, name, name),
                "#%d = ADVANCED_BREP_SHAPE_REPRESENTATION('',(#%d),#4);"
                % (base + 5, base + 6),
                "#%d = MANIFOLD_SOLID_BREP('',#%d);" % (base + 6, base + 7),
                "#%d = CLOSED_SHELL('',());" % (base + 7),
            ]
        )
        if colours and colour is not None:
            lines.extend(
                [
                    "#%d = STYLED_ITEM('color',(#%d),#%d);"
                    % (base + 8, base + 9, base + 6),
                    "#%d = PRESENTATION_STYLE_ASSIGNMENT((#%d));" % (base + 9, base + 10),
                    "#%d = SURFACE_STYLE_USAGE(.BOTH.,#%d);" % (base + 10, base + 11),
                    "#%d = SURFACE_SIDE_STYLE('',(#%d));" % (base + 11, base + 12),
                    "#%d = SURFACE_STYLE_FILL_AREA(#%d);" % (base + 12, base + 13),
                    "#%d = FILL_AREA_STYLE('',(#%d));" % (base + 13, base + 14),
                    "#%d = FILL_AREA_STYLE_COLOUR('',#%d);" % (base + 14, base + 15),
                    "#%d = COLOUR_RGB('',%.12f,%.12f,\n  %.12f);"
                    % ((base + 15,) + srgb_channels(colour)),
                ]
            )
        identifier += 20
    lines.extend(["ENDSEC;", "END-ISO-10303-21;", ""])
    return "\n".join(lines).encode("ascii")
