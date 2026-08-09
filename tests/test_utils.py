from gardena_bluetooth.parse import ContourPoint
from gardena_bluetooth.utils import contour_to_svg


def test_contour_to_svg_returns_none_for_no_points():
    assert contour_to_svg(None) is None
    assert contour_to_svg([]) is None


def test_contour_to_svg_returns_none_for_zero_extent():
    points = [ContourPoint(0, 0), ContourPoint(90, 0)]
    assert contour_to_svg(points) is None


def test_contour_to_svg_renders_contour_path():
    points = [ContourPoint(0, 100), ContourPoint(90, 200), ContourPoint(180, 100)]
    svg = contour_to_svg(points)

    assert svg is not None
    assert svg.startswith(b"<svg")
    assert svg.endswith(b"</svg>")
    assert b"0.0,0.0" in svg
    assert b"#03a9f4" in svg
    assert b"<path" in svg


def test_contour_to_svg_draws_spray_jet_and_widens_extent_for_overshoot():
    points = [ContourPoint(0, 100)]

    without_spray = contour_to_svg(points)
    with_overshoot = contour_to_svg(points, spray=(45, 500))

    assert without_spray is not None
    assert b"stroke-linecap" not in without_spray

    assert with_overshoot is not None
    assert b"stroke-linecap" in with_overshoot
    # The spray overshoots the contour, so the canvas grows to fit it.
    assert b"-525.0 -525.0" in with_overshoot
