from KicadModTree.nodes import Footprint, FootprintType
from KicadModTree.nodes.base.Zone import Zone, Keepouts, PadConnection, Hatch, ZoneFill
from KicadModTree.Vector import Vector2D
from KicadModTree.KicadFileHandler import KicadFileHandler

import pytest

RESULT_Basic = """
(footprint zonetest (version 20221018) (generator kicad-footprint-generator)
  (layer F.Cu)
  (zone
    (net 1)
    (net_name GND)
    (layers)
    (name "")
    (hatch edge 0.5)
    (priority 1)
    (connect_pads (clearance 0))
    (filled_areas_thickness no)
    (min_thickness 0.25)
    (keepout (tracks allowed) (vias not_allowed) (copperpour allowed) (pads allowed) (footprints allowed))
    (fill)
    (polygon (pts
       (xy 0 0)
       (xy 0 1)
       (xy 1 1)
       (xy 1 0))))
)"""

RESULT_WithFill = """
(footprint filltest (version 20221018) (generator kicad-footprint-generator)
  (layer F.Cu)
  (zone
    (net 0)
    (net_name "")
    (layers)
    (name "")
    (hatch edge 0.5)
    (connect_pads (clearance 0))
    (filled_areas_thickness no)
    (min_thickness 0.25)
    (fill yes
      (thermal_gap 0.5)
      (thermal_bridge_width 0.5)
      (smoothing fillet (radius 0))
      (island_removal_mode 0))
    (polygon (pts
       (xy 0 0)
       (xy 0 1)
       (xy 1 1)
       (xy 1 0))))
)"""

RESULT_IslandMin = """
(footprint island_min (version 20221018) (generator kicad-footprint-generator)
  (layer F.Cu)
  (zone
    (net 0)
    (net_name "")
    (layers)
    (name "")
    (hatch edge 0.5)
    (connect_pads (clearance 0))
    (filled_areas_thickness no)
    (min_thickness 0.25)
    (fill yes
      (thermal_gap 0.5)
      (thermal_bridge_width 0.5)
      (island_removal_mode 2)
      (island_area_min 0.1))
    (polygon (pts
       (xy 0 0)
       (xy 0 1)
       (xy 1 1)
       (xy 1 0))))
)
"""

DEFAULT_TEST_POLYGON = [
        Vector2D(0, 0),
        Vector2D(0, 1),
        Vector2D(1, 1),
        Vector2D(1, 0),
    ]

DEFAULT_HATCH = Hatch(Hatch.EDGE, 0.5)


def _test_serialisation(kicad_mod, expected, dump=False):
    file_handler = KicadFileHandler(kicad_mod)

    rendered = file_handler.serialize(timestamp=0)

    # can be used to get an update version
    # but make sure the new one is right!
    if dump:
        print(rendered)

    expected = expected.strip()
    assert rendered == expected


def test_basic():
    ko = Keepouts(
        tracks=Keepouts.ALLOW,
        vias=Keepouts.DENY,
    )

    z = Zone(
        net=1,
        net_name="GND",
        hatch=DEFAULT_HATCH,
        polygon_pts=DEFAULT_TEST_POLYGON,
        priority=1,
        keepouts=ko,
        fill=None,  # test that no fill is OK
    )

    # Test that the basic properties are set correctly via the constructor
    assert z.net == 1
    assert z.net_name == "GND"
    assert z.hatch.style == Hatch.EDGE
    assert z.hatch.pitch == 0.5
    assert z.priority == 1
    assert z.keepouts.tracks == Keepouts.ALLOW
    assert z.keepouts.vias == Keepouts.DENY

    assert z.connect_pads.type == PadConnection.THERMAL_RELIEF
    assert z.connect_pads.clearance == 0

    assert z.fill is None

    kicad_mod = Footprint("zonetest", FootprintType.UNSPECIFIED)
    kicad_mod.append(z)

    _test_serialisation(kicad_mod, RESULT_Basic)


def test_fill():
    zf = ZoneFill(
        fill=ZoneFill.FILL_SOLID,
        smoothing=ZoneFill.SMOOTHING_FILLET,
        island_removal_mode=ZoneFill.ISLAND_REMOVAL_REMOVE,
    )

    # Test that the properties are set correctly via the constructor
    assert zf.fill == ZoneFill.FILL_SOLID
    assert zf.smoothing == ZoneFill.SMOOTHING_FILLET
    assert zf.island_removal_mode == ZoneFill.ISLAND_REMOVAL_REMOVE

    assert zf.island_area_min is None

    z = Zone(
        hatch=DEFAULT_HATCH,
        polygon_pts=DEFAULT_TEST_POLYGON,
        fill=zf,
    )

    kicad_mod = Footprint("filltest", FootprintType.UNSPECIFIED)
    kicad_mod.append(z)

    _test_serialisation(kicad_mod, RESULT_WithFill)


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

    z = Zone(
        hatch=DEFAULT_HATCH,
        polygon_pts=DEFAULT_TEST_POLYGON,
        fill=zf,
    )

    kicad_mod = Footprint("island_min", FootprintType.UNSPECIFIED)
    kicad_mod.append(z)

    _test_serialisation(kicad_mod, RESULT_IslandMin)
