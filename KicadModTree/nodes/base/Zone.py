# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2023 by John Beard, <john.j.beard@gmail.com>

from KicadModTree.Vector import *
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.Polygon import Polygon
import KicadModTree.PolygonPoints as PPts


class PadConnection(Node):
    clearance: float = 0
    type: str = None

    THRU_HOLE_ONLY = "thru_hole_only"
    FULL = "full"
    NO = "no"
    THERMAL_RELIEF = "thermal_relief"

    def __init__(self, **kwargs):
        Node.__init__(self)

        self.clearance = kwargs.get("clearance", 0)
        self.type = self._get_type(**kwargs)

    def _get_type(self, **kwargs):
        type = kwargs.get("type", self.THERMAL_RELIEF)

        valid_types = [self.THRU_HOLE_ONLY, self.FULL, self.NO, self.THERMAL_RELIEF]
        if type not in valid_types:
            raise ValueError("Invalid pad connection type: %s" % type)

        return type


class Keepouts(Node):
    r"""
    Add a keepout definition to the render tree
    """

    ALLOW = False
    DENY = True

    def __init__(self, **kwargs):
        Node.__init__(self)

        self.tracks = self._get_keepout("tracks", kwargs)
        self.vias = self._get_keepout("vias", kwargs)
        self.copperpour = self._get_keepout("copperpour", kwargs)
        self.pads = self._get_keepout("pads", kwargs)
        self.footprints = self._get_keepout("footprints", kwargs)

    def _get_keepout(self, keepout_name, keepout_spec):
        """
        Get the value of a keepout rule. The default is to allow everything.
        """
        allowed = keepout_spec.get(keepout_name, self.ALLOW)

        valid_allowance = [self.ALLOW, self.DENY]
        if allowed not in valid_allowance:
            raise ValueError(
                f"Keepout rule {keepout_name} must be either '{self.ALLOW}' or '{self.DENY}'"
            )

        return allowed


class Hatch(Node):
    NONE = "none"
    EDGE = "edge"
    FULL = "full"

    def __init__(self, style, pitch):
        Node.__init__(self)
        self.style = style
        self.pitch = pitch

        valid_styles = [self.NONE, self.EDGE, self.FULL]

        if style not in valid_styles:
            raise ValueError("Invalid hatch style: %s" % style)


class ZoneFill(Node):
    r"""
    Add a zone fill definition to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:

        * *fill* (``str``) --
            fill style of the zone (default: 'solid')
        * *thermal_gap* (``float``) --
            thermal gap of the zone (default: None)
        * *thermal_bridge_width* (``float``) --
            thermal bridge width of the zone (default: None)
        * *smoothing* (``str``) --
            smoothing of the zone (default: None)

    """

    FILL_SOLID = "solid"
    FILL_HATCHED = "hatched"

    SMOOTHING_CHAMFER = "chamfer"
    SMOOTHING_FILLET = "fillet"

    ISLAND_REMOVAL_REMOVE = "remove"
    ISLAND_REMOVAL_FILL = "fill"
    ISLAND_REMOVAL_MINIMUM_AREA = "minimum_area"

    HATCH_SMOOTHING_NONE = "none"
    HATCH_SMOOTHING_FILLET = "fillet"
    HATCH_SMOOTHING_ARC_MINIMUM = "arc_minimum"
    HATCH_SMOOTHING_ARC_MAXIMUM = "arc_maximum"

    HATCH_BORDER_MINIMUM_THICKNESS = "minimum_thickness"
    HATCH_BORDER_HATCH_THICKNESS = "hatch_thickness"

    def __init__(self, **kwargs):
        self.fill = kwargs.get("fill", self.FILL_SOLID)

        valid_fills = [self.FILL_SOLID, self.FILL_HATCHED]

        if self.fill not in valid_fills:
            raise ValueError("Invalid fill style: %s" % self.fill)

        self.thermal_gap = kwargs.get("thermal_gap", 0.5)
        self.thermal_bridge_width = kwargs.get("thermal_bridge_width", 0.5)

        valid_smoothing = [None, self.SMOOTHING_CHAMFER, self.SMOOTHING_FILLET]
        self.smoothing = kwargs.get("smoothing", None)
        if self.smoothing not in valid_smoothing:
            raise ValueError("Invalid smoothing: %s" % self.smoothing)

        self.smoothing_radius = kwargs.get("smoothing_radius", None)

        self.island_removal_mode = kwargs.get("island_removal_mode", None)

        valid_island_removal_modes = [
            None,
            self.ISLAND_REMOVAL_REMOVE,
            self.ISLAND_REMOVAL_FILL,
            self.ISLAND_REMOVAL_MINIMUM_AREA,
        ]
        if self.island_removal_mode not in valid_island_removal_modes:
            raise ValueError(
                "Invalid island removal mode: %s" % self.island_removal_mode
            )

        self.island_area_min = kwargs.get("island_area_min", None)

        if (
            self.island_area_min is not None
            and self.island_removal_mode != self.ISLAND_REMOVAL_MINIMUM_AREA
        ):
            raise ValueError(
                "Island area minimum can only be used with minimum_area island removal mode"
            )
        elif (
            self.island_area_min is None
            and self.island_removal_mode == self.ISLAND_REMOVAL_MINIMUM_AREA
        ):
            raise ValueError(
                "Island area minimum must be specified with minimum_area island removal mode"
            )

        self.hatch_thickness = kwargs.get("hatch_thickness", None)
        self.hatch_gap = kwargs.get("hatch_gap", None)
        self.hatch_orientation = kwargs.get("hatch_orientation", None)
        self.hatch_smoothing_level = kwargs.get("hatch_smoothing_level", None)

        valid_hatch_smoothing_levels = [
            None,  # Same as NONE?
            self.HATCH_SMOOTHING_NONE,
            self.HATCH_SMOOTHING_FILLET,
            self.HATCH_SMOOTHING_ARC_MINIMUM,
            self.HATCH_SMOOTHING_ARC_MAXIMUM,
        ]
        if self.hatch_smoothing_level not in valid_hatch_smoothing_levels:
            raise ValueError(
                "Invalid hatch smoothing level: %s" % self.hatch_smoothing_level
            )

        self.hatch_smoothing_value = kwargs.get("hatch_smoothing_value", None)

        self.hatch_border_algorithm = kwargs.get("hatch_border_algorithm", None)

        valid_hatch_border_algorithms = [
            None,
            self.HATCH_BORDER_MINIMUM_THICKNESS,
            self.HATCH_BORDER_HATCH_THICKNESS,
        ]
        if self.hatch_border_algorithm not in valid_hatch_border_algorithms:
            raise ValueError(
                "Invalid hatch border algorithm: %s" % self.hatch_border_algorithm
            )

        self.hatch_min_hole_area = kwargs.get("hatch_min_hole_area", None)


class Zone(Node):
    r"""Add a Line to the render tree

    :param polygon_pts (``list``) --
        list of points defining the polygon of the zone
    :param hatch (``Hatch``) --
        hatch parameters of the zone
    :param keepouts (``Keepouts``) --
        keepout rules for the zone
    :param fill (``ZoneFill``) --
        Zone fill parameters (or none)
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *layers* (``list``) --
            layers the zone is present on
        * *polygon_pts* (``list``) --
            list of points defining the polygon of the zone
        * *net* (``int``) --
            net number of the zone
        * *net_name* (``str``) --
            net name of the zone
        * *name* (``str``) --
            human readable name of the zone
        * *hatch* (``Hatch``) --
            hatch parameters of the zone
        * *filled_areas_thickness* (``bool``) --
            if the zone line width should be used when determining the fill area
        * *min_thickness* (``float``) --
            minimum thickness of the zone
        * *keepouts* (``Keepouts``) --
            keepout rules for the zone
        * *connect_pads* (``PadConnection``) --
            pad connection rules for the zone
        * *priority* (``int``) --
            priority of the zone (optional, default None)
    """

    def __init__(
        self,
        polygon_pts: list,
        hatch: Hatch,
        keepouts: Keepouts = None,
        fill=None,
        connect_pads=PadConnection(),
        **kwargs,
    ):
        Node.__init__(self)

        self.layers = kwargs.get("layers", [])
        self.nodes = PPts.PolygonPoints(nodes=polygon_pts)
        self.net = kwargs.get("net", 0)
        self.net_name = kwargs.get("net_name", "")
        self.name = kwargs.get("name", "")
        self.hatch = hatch
        self.filled_areas_thickness = kwargs.get("filled_areas_thickness", False)
        self.min_thickness = kwargs.get("min_thickness", 0.25)
        self.keepouts = keepouts
        self.connect_pads = connect_pads
        self.priority = kwargs.get("priority", None)
        self.fill = fill
