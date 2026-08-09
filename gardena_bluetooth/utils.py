"""Rendering helpers built on top of the parsed data models."""

from math import cos, radians, sin

from .parse import ContourPoints

CONTOUR_COLOR = "#03a9f4"
SPRINKLER_COLOR = "#ff9800"
CONTOUR_MARGIN = 1.05


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
    # Points arrive in the order the sprinkler pans through them, and it waters
    # outwards along its own radius, so the area is a sector closed via the center.
    path = "0.0,0.0 " + " ".join(
        _point_to_svg(point.angle, point.distance) for point in points
    )
    jet = ""
    if spray is not None:
        jet = (
            f'<path d="M 0.0,0.0 {_point_to_svg(*spray)}" '
            f'stroke="{SPRINKLER_COLOR}" stroke-width="{size * 0.015:.2f}" '
            'stroke-linecap="round"/>'
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-size:.1f} {-size:.1f} {2 * size:.1f} {2 * size:.1f}">'
        f'<path d="M {path} Z" fill="{CONTOUR_COLOR}" fill-opacity="0.3" '
        f'stroke="{CONTOUR_COLOR}" stroke-width="{size * 0.01:.2f}" '
        'stroke-linejoin="round"/>'
        f"{jet}"
        f'<circle r="{size * 0.02:.2f}" fill="{SPRINKLER_COLOR}"/>'
        "</svg>"
    ).encode()
