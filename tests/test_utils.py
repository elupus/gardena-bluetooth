import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.image import SVGImageSnapshotExtension

from gardena_bluetooth.parse import ContourPoint
from gardena_bluetooth.utils import contour_to_svg


@pytest.fixture
def svg_snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    return snapshot.with_defaults(extension_class=SVGImageSnapshotExtension)


CONTOUR = [ContourPoint(a, 150 + 50 * ((a // 30) % 3)) for a in range(0, 360, 20)]


def test_contour_to_svg_returns_none_for_no_points():
    assert contour_to_svg(None) is None
    assert contour_to_svg([]) is None


def test_contour_to_svg_returns_none_for_zero_extent():
    points = [ContourPoint(0, 0), ContourPoint(90, 0)]
    assert contour_to_svg(points) is None


def test_contour_to_svg_snapshot_idle(svg_snapshot: SnapshotAssertion):
    svg = contour_to_svg(CONTOUR)
    assert svg is not None
    assert svg.decode() == svg_snapshot


def test_contour_to_svg_snapshot_spraying_within_contour(
    svg_snapshot: SnapshotAssertion,
):
    svg = contour_to_svg(CONTOUR, spray=(40, 180))
    assert svg is not None
    assert svg.decode() == svg_snapshot


def test_contour_to_svg_snapshot_spraying_past_contour(
    svg_snapshot: SnapshotAssertion,
):
    svg = contour_to_svg(CONTOUR, spray=(200, 260))
    assert svg is not None
    assert svg.decode() == svg_snapshot


def test_contour_to_svg_snapshot_narrow_close_spray(svg_snapshot: SnapshotAssertion):
    points = [ContourPoint(a, 90) for a in range(300, 361, 10)] + [
        ContourPoint(a, 90) for a in range(0, 61, 10)
    ]
    svg = contour_to_svg(points, spray=(0, 90))
    assert svg is not None
    assert svg.decode() == svg_snapshot
