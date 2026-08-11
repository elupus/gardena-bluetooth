"""Rendering helpers built on top of the parsed data models."""

from math import cos, radians, sin
from xml.etree.ElementTree import Element, SubElement, indent, tostring

from .parse import ContourPoints

CONTOUR_COLOR = "#03a9f4"
SPRINKLER_COLOR = "#ff9800"
CONTOUR_MARGIN = 1.05
SPRAY_SPREAD = 8.0
"""Total angular width, in degrees, the spray jet is drawn with."""
SPRAY_PULSE_DURATION = "1.2s"


def _point_to_svg(angle: int, distance: float) -> str:
    """Project a polar contour point onto svg coordinates, with zero degrees up."""
    return f"{distance * sin(radians(angle)):.1f},{-distance * cos(radians(angle)):.1f}"


def contour_to_svg(
    points: ContourPoints | None, spray: tuple[int, int] | None = None
) -> bytes | None:
    """Render a contour as a top down map with the sprinkler at the center.

    `spray` is the (angle, distance) the sprinkler is currently throwing at,
    drawn as a jet from the center - the sprinkler can be throwing past the
    contour it is tracking, which is accounted for when sizing the canvas.
    """
    if not points:
        return None

    extent = max(point.distance for point in points)
    if spray is not None:
        extent = max(extent, spray[1])
    if not extent:
        return None

    size = extent * CONTOUR_MARGIN
    svg = Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": f"{-size:.1f} {-size:.1f} {2 * size:.1f} {2 * size:.1f}",
        },
    )

    # Points arrive in the order the sprinkler pans through them, and it waters
    # outwards along its own radius, so the area is a sector closed via the center.
    path = "0.0,0.0 " + " ".join(
        _point_to_svg(point.angle, point.distance) for point in points
    )
    SubElement(
        svg,
        "path",
        {
            "d": f"M {path} Z",
            "fill": CONTOUR_COLOR,
            "fill-opacity": "0.3",
            "stroke": CONTOUR_COLOR,
            "stroke-width": f"{size * 0.01:.2f}",
            "stroke-linejoin": "round",
        },
    )

    if spray is not None:
        angle, distance = spray
        left = _point_to_svg(angle - SPRAY_SPREAD / 2, distance)
        right = _point_to_svg(angle + SPRAY_SPREAD / 2, distance)
        triangle_d = f"M 0.0,0.0 L {left} L {right} Z"

        # A dim static triangle stays underneath for a constant direction
        # indicator.
        SubElement(
            svg,
            "path",
            {"d": triangle_d, "fill": SPRINKLER_COLOR, "fill-opacity": "0.3"},
        )

        # The triangle's apex sits at the origin (the sprinkler), so scaling
        # it - which SVG does around the local origin by default - grows a
        # wave outward from there to the tip, not just a flat pulse in place.
        wave = SubElement(svg, "path", {"d": triangle_d, "fill": SPRINKLER_COLOR})
        SubElement(
            wave,
            "animateTransform",
            {
                "attributeName": "transform",
                "type": "scale",
                "values": "0;1",
                "dur": SPRAY_PULSE_DURATION,
                "repeatCount": "indefinite",
            },
        )
        SubElement(
            wave,
            "animate",
            {
                "attributeName": "fill-opacity",
                "values": "0;0.9;0",
                "keyTimes": "0;0.6;1",
                "dur": SPRAY_PULSE_DURATION,
                "repeatCount": "indefinite",
            },
        )

    SubElement(svg, "circle", {"r": f"{size * 0.02:.2f}", "fill": SPRINKLER_COLOR})

    indent(svg, space="  ")
    return tostring(svg, encoding="unicode").encode()
