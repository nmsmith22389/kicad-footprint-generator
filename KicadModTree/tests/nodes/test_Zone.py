from KicadModTree.nodes.base.Zone import Zone, Keepouts, PadConnection, Hatch, ZoneFill
from KicadModTree.Vector import Vector2D

import pytest


def test_basic():
    ko = Keepouts(
        tracks=Keepouts.ALLOW,
        vias=Keepouts.DENY,
    )

    polygon_pts = [
        Vector2D(0, 0),
        Vector2D(0, 1),
        Vector2D(1, 1),
        Vector2D(1, 0),
    ]

    z = Zone(
        net=1,
        net_name="GND",
        hatch=None,
        polygon_pts=polygon_pts,
        priority=1,
        keepouts=ko,
        fill=None,  # test that no fill is OK
    )

    assert z.net == 1
    assert z.net_name == "GND"
    assert z.hatch is None
    assert z.priority == 1
    assert z.keepouts.tracks == Keepouts.ALLOW
    assert z.keepouts.vias == Keepouts.DENY

    assert z.connect_pads.type == PadConnection.THERMAL_RELIEF
    assert z.connect_pads.clearance == 0

    assert z.fill is None


def test_fill():
    zf = ZoneFill(
        fill=ZoneFill.FILL_SOLID,
        smoothing=ZoneFill.SMOOTHING_FILLET,
        island_removal_mode=ZoneFill.ISLAND_REMOVAL_REMOVE,
    )

    assert zf.fill == ZoneFill.FILL_SOLID
    assert zf.smoothing == ZoneFill.SMOOTHING_FILLET
    assert zf.island_removal_mode == ZoneFill.ISLAND_REMOVAL_REMOVE

    assert zf.island_area_min is None


def test_island_removal_area_min():

    # Test that island_area_min is required when island_removal_mode is
    with pytest.raises(ValueError):
        zf = ZoneFill(
            island_removal_mode=ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA,
            island_area_min=None,
        )

    # Test that island_area_min only works with the correct island_removal_mode
    with pytest.raises(ValueError):
        zf = ZoneFill(
            island_removal_mode=ZoneFill.ISLAND_REMOVAL_REMOVE,
            island_area_min=0.1,
        )

    zf = ZoneFill(
        island_removal_mode=ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA,
        island_area_min=0.1,
    )

    assert zf.island_removal_mode == ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA
    assert zf.island_area_min == 0.1
