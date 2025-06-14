# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) 2018 by Rene Poeschl, github @poeschlr
# (C) The KiCad Librarian Team

from __future__ import annotations

import copy
import dataclasses
import enum
import math
from typing import cast

from KicadModTree.nodes.base import Polygon
from KicadModTree.nodes.Node import Node
from KicadModTree.util.corner_handling import ChamferSizeHandler, RoundRadiusHandler
from KicadModTree.util.corner_selection import CornerSelection
from kilibs.geom import BoundingBox, GeomRectangle, Vec2DCompatible, Vector2D
from kilibs.util.param_util import toVectorUseCopyIfNumber


class Pad(Node):
    """Create a Pad.

    Args:
        type: Type of the pad.
        shape: Shape of the pad.
        layers: Layers which are used for the pad.
        at: Center position of the pad.
        size: Size of the pad.

        number: Number/name of the pad.
        offset: Offset of the pad.
        rotation: Rotation of the pad.
        fab_property: The pad fabrication property.
        drill: Drill-size of the pad.

        solder_paste_margin_ratio: Solder paste margin ratio of the pad.
        solder_paste_margin: Solder paste margin of the pad.
        solder_mask_margin: Solder mask margin of the pad.

        tuning_properties: Pad tuning properties. None for "undefined", which is the
            KiCad default state.
        round_radius_handler: An instance of the RoundRadiusHandler class. Ignored for
            every shape except round rect.
        zone_connection: Zone connection of the pad.
        shape_in_zone: Shape in zone.
        unconnected_layer_mode: Define how the pad behaves on layers where it is not
            connected.
        clearance: The optional clearance token attribute defines the clearance from all
            copper to the pad. If not set, the footprint clearance is used.
        thermal_bridge_width: The optional thermal_width token attribute defines the
            thermal relief spoke width used for zone connection for the pad. This only
            affects a pad connected to a zone with a thermal relief. If not set, the
            footprint thermal_width setting is used.
        thermal_bridge_angle: The optional thermal bridge angle. If not given this
            defaults to the same default as KiCad (45 for circular pads, 90 for
            everything else).
        thermal_gap: The optional thermal_gap token attribute defines the distance from
            the pad to the zone of the thermal relief connection for the pad. This only
            affects a pad connected to a zone with a thermal relief. If not set, the
            footprint thermal_gap setting is used.
        anchor_shape: Anchor shape.

        chamfer_corners: Chamfer corners.
        maximum_chamfer: Maximum chamfer.
        chamfer_size: Chamfer size.
        chamfer_exact: Chamfer exact size.
        chamfer_size_handler: Chamfer size handler.

        primitives: Polygon primitives used for pads with custom shape.
        x_mirror: Mirror x direction around offset "point".
        y_mirror: Mirror y direction around offset "point".

    :Example:
        >>> from KicadModTree import *
        >>> Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
        ...     at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT)
    """

    TYPE_THT = "thru_hole"
    TYPE_SMT = "smd"
    TYPE_CONNECT = "connect"
    TYPE_NPTH = "np_thru_hole"
    _TYPES = [TYPE_THT, TYPE_SMT, TYPE_CONNECT, TYPE_NPTH]

    SHAPE_CIRCLE = "circle"
    SHAPE_OVAL = "oval"
    SHAPE_RECT = "rect"
    SHAPE_ROUNDRECT = "roundrect"
    SHAPE_TRAPEZE = "trapezoid"
    SHAPE_CUSTOM = "custom"
    _SHAPES = [
        SHAPE_CIRCLE,
        SHAPE_OVAL,
        SHAPE_RECT,
        SHAPE_ROUNDRECT,
        SHAPE_TRAPEZE,
        SHAPE_CUSTOM,
    ]

    LAYERS_SMT = ["F.Cu", "F.Paste", "F.Mask"]
    LAYERS_THT = ["*.Cu", "*.Mask"]
    LAYERS_NPTH = ["*.Cu", "*.Mask"]
    LAYERS_CONNECT_FRONT = ["F.Cu", "F.Mask"]
    LAYERS_CONNECT_BACK = ["B.Cu", "B.Mask"]

    ANCHOR_CIRCLE = "circle"
    ANCHOR_RECT = "rect"
    _ANCHOR_SHAPE = [ANCHOR_CIRCLE, ANCHOR_RECT]

    SHAPE_IN_ZONE_CONVEX = "convexhull"
    SHAPE_IN_ZONE_OUTLINE = "outline"
    _SHAPE_IN_ZONE = [SHAPE_IN_ZONE_CONVEX, SHAPE_IN_ZONE_OUTLINE]

    class FabProperty(enum.Enum):
        """Type-safe pad fabrication property"""

        # Note that these constants do not necessarily correspond to the
        # strings used in the KiCad file format.
        BGA = "bga"
        FIDUCIAL_GLOBAL = "fiducial_global"
        FIDUCIAL_LOCAL = "fiducial_local"
        TESTPOINT = "testpoint"
        HEATSINK = "heatsink"
        CASTELLATED = "castellated"

    class ZoneConnection(enum.Enum):
        """Type-safe pad zone connection."""

        # Note that these constants do not necessarily correspond to the
        # values used in the KiCad file format, thay can be anything
        INHERIT = 0
        """For a pad, inherits from footprint, for a footprint, inherits from board."""
        NONE = 1
        THERMAL_RELIEF = 2
        SOLID = 3

    class UnconnectedLayerMode(enum.Enum):
        """Behaviour of a Padstack on layers without connection.

        (Should move to Padstack when implemented)
        """

        KEEP_ALL = 0
        REMOVE_ALL = 1
        REMOVE_EXCEPT_START_AND_END = 2

    @dataclasses.dataclass
    class TuningProperties:
        """
        Complete decription of a pad's die/tuning properties
        """

        die_length: float = 0
        """
        The die length between the component pad and the physical
        chip bond pad inside the component package (in mm).
        KiCad uses 0 to mean not specfied.
        """
        # die_delay: float // Will be in v10 (units?)

    at: Vector2D
    size: Vector2D
    number: str | int
    type: str
    _fab_property: FabProperty | None
    zone_connection: ZoneConnection
    _chamfer_corners: CornerSelection
    thermal_bridge_width: float | None
    """None means inherit from the footprint (like KiCad)"""
    thermal_gap: float | None
    """None means inherit from the footprint (like KiCad)"""
    _thermal_bridge_angle: float | None
    unconnected_layer_mode: UnconnectedLayerMode
    clearance: float | None

    tuning_properties: TuningProperties | None

    _round_radius_handler: RoundRadiusHandler | None
    mirror: list[float | None]

    def __init__(
        self,
        type: str,
        shape: str,
        layers: list[str],
        at: Vec2DCompatible,
        size: float | Vector2D,
        number: int | str = "",
        offset: Vec2DCompatible = [0, 0],
        rotation: float = 0.0,
        fab_property: FabProperty | None = None,
        drill: float | Vec2DCompatible | None = None,
        solder_paste_margin_ratio: float = 0,
        solder_paste_margin: float = 0,
        solder_mask_margin: float = 0,
        tuning_properties: TuningProperties | None = None,
        round_radius_handler: RoundRadiusHandler | None = None,
        zone_connection: ZoneConnection = ZoneConnection.INHERIT,
        shape_in_zone: str = SHAPE_IN_ZONE_OUTLINE,
        unconnected_layer_mode: UnconnectedLayerMode = UnconnectedLayerMode.KEEP_ALL,
        clearance: float | None = None,
        thermal_bridge_width: float | None = None,
        thermal_bridge_angle: float | None = None,
        thermal_gap: float | None = None,
        anchor_shape: str = ANCHOR_CIRCLE,
        chamfer_corners: list[bool] | dict[str, bool] | int | None = None,
        maximum_chamfer: float | None = None,
        chamfer_size: float | None = None,
        chamfer_exact: float | None = None,
        chamfer_size_handler: ChamferSizeHandler | None = None,
        primitives: list[Polygon] | None = None,
        x_mirror: float | None = None,
        y_mirror: float | None = None,
        **kwargs,  # TODO: remove **kwargs. Currently there to catch all parameters that are not used.
    ) -> None:
        Node.__init__(self)
        self.number = number
        self.type = type
        if self.type not in Pad._TYPES:
            raise ValueError(f"{type} is an invalid type for pads.")
        self._fab_property = Pad.FabProperty(fab_property) if fab_property else None
        self.shape = shape
        if self.shape not in Pad._SHAPES:
            raise ValueError(f"{shape} is an invalid shape for pads")
        self.at = Vector2D(at)
        self.rotation = rotation
        self.size = cast(Vector2D, toVectorUseCopyIfNumber(size, low_limit=0))
        self.offset = Vector2D(offset)
        self.solder_paste_margin_ratio = solder_paste_margin_ratio
        self.solder_paste_margin = solder_paste_margin
        self.solder_mask_margin = solder_mask_margin
        self.zone_connection = zone_connection
        self.clearance = clearance
        self.thermal_bridge_width = thermal_bridge_width
        self.thermal_bridge_angle = thermal_bridge_angle  # TODO: use default_value=90
        self.thermal_gap = thermal_gap
        self.unconnected_layer_mode = unconnected_layer_mode
        self.tuning_properties = tuning_properties
        self.layers = layers
        self.chamfer_size_handler = None
        self.chamfer_ratio = None
        self._round_radius_handler = round_radius_handler
        self._init_drill(drill)  # requires pad type and offset
        self._init_mirror(x_mirror, y_mirror)

        if self.shape == self.SHAPE_OVAL and self.size[0] == self.size[1]:
            self.shape = self.SHAPE_CIRCLE

        elif self.shape == Pad.SHAPE_ROUNDRECT:
            if chamfer_size_handler:
                self.chamfer_size_handler = chamfer_size_handler
            else:
                self.chamfer_size_handler = ChamferSizeHandler(
                    must_be_square=True,
                    maximum_chamfer=maximum_chamfer,
                    chamfer_size=chamfer_size,
                    chamfer_exact=chamfer_exact,
                )
            self.chamfer_ratio = self.chamfer_size_handler.getChamferRatio(
                min(self.size)
            )
            self._chamfer_corners = CornerSelection(chamfer_corners)
            if not self._round_radius_handler:
                raise KeyError("round_radius_handler not declared for roundrect pads")

        elif self.shape == Pad.SHAPE_CUSTOM:
            self.anchor_shape = anchor_shape
            if self.anchor_shape not in Pad._ANCHOR_SHAPE:
                raise ValueError(f"{anchor_shape} is an illegal anchor shape")
            self.shape_in_zone = shape_in_zone
            if self.shape_in_zone not in Pad._SHAPE_IN_ZONE:
                raise ValueError(
                    f"{shape_in_zone} is an illegal specifier for the shape in zone option"
                )
            self.primitives: list[Polygon] = []
            if primitives:
                for primitive in primitives:
                    self.primitives.append(primitive)
            else:
                raise KeyError("primitives must be declared for custom pads")

    def _init_mirror(self, x_mirror: float | None, y_mirror: float | None) -> None:
        self.mirror = [None, None]
        if x_mirror is not None:
            self.mirror[0] = x_mirror
            self.at.x = 2 * self.mirror[0] - self.at.x
            self.offset.x *= -1
        if y_mirror is not None:
            self.mirror[1] = y_mirror
            self.at.y = 2 * self.mirror[1] - self.at.y
            self.offset.y *= -1

    def _init_drill(self, drill: float | Vec2DCompatible | None) -> None:
        if self.type in [Pad.TYPE_THT, Pad.TYPE_NPTH]:
            if not drill:
                raise KeyError('drill size required (like "drill=1")')
            self.drill = toVectorUseCopyIfNumber(drill, low_limit=0)
        else:
            self.drill = None
            if drill:
                pass  # TODO: throw warning because drill is not supported

    def rotate(
        self, angle: float, origin: Vec2DCompatible = (0, 0), use_degrees: bool = True
    ) -> Pad:
        r"""Rotate pad around given origin

        :params:
            * *angle* (``float``)
                rotation angle
            * *origin* (``Vector2D``)
                origin point for the rotation. default: (0, 0)
            * *use_degrees* (``boolean``)
                rotation angle is given in degrees. default:True
        """

        self.at.rotate(angle=angle, origin=Vector2D(origin), use_degrees=use_degrees)
        a = angle if use_degrees else math.degrees(angle)

        # subtraction because kicad text field rotation is the wrong way round
        self.rotation -= a
        return self

    def translate(self, vector: Vector2D) -> Pad:
        r"""Translate pad

        :params:
            * *vector* (``Vector2D``)
                2D vector defining by how much and in what direction to translate.
        """

        self.at += vector
        return self

    # calculate the outline of a pad
    def bbox(self) -> BoundingBox:
        if self.shape in [Pad.SHAPE_CIRCLE]:
            return BoundingBox(
                self.at - self.size / 2,
                self.at + self.size / 2,
            )
        elif self.shape in [Pad.SHAPE_RECT, Pad.SHAPE_ROUNDRECT, Pad.SHAPE_OVAL]:
            rect = GeomRectangle(center=self.at, size=self.size, angle=self.rotation)
            return rect.bbox()
        else:
            bounding_box = BoundingBox()
            for point in self.primitives[0].points:
                bounding_box.include_point(point + self.at)
            bounding_box.inflate(self.primitives[0].width / 2.0)
            return bounding_box

    def copy_with(
        self,
        at: Vector2D | None = None,
        shape: str | None = None,
        number: str | int | None = None,
    ) -> Pad:
        """
        Helper functon for a very common operation: copying a pad
        with a new position, shape or number.

        You can add more parameters if you want to, but at some
        point it might be better to create a whole new pad yourself.
        """
        new = copy.deepcopy(self)

        if at is not None:
            new.at = at
        if shape is not None:
            new.shape = shape
        if number is not None:
            new.number = number

        return new

    def getRoundRadius(self) -> float:
        if self.shape == Pad.SHAPE_CUSTOM:
            r_max = 0
            for p in self.primitives:
                r = p.width / 2
                if r > r_max:
                    r_max = r
            return r_max
        if self._round_radius_handler:
            return self._round_radius_handler.getRoundRadius(min(self.size))
        else:
            raise RuntimeError(
                "getRoundRadius() called but _round_radius_handler is None."
            )

    @property
    def fab_property(self) -> FabProperty | None:
        """
        The fabrication property of the pad.

        :return: one of the Pad.PROPERTY_* constants, or None
        """
        return self._fab_property

    @property
    def thermal_bridge_angle(self) -> float:
        """
        KiCad has a slightly weird default system here. Rather than trying to update the default
        when the pad shape changes, internally we store a None and return the default value as needed.

        But the Pad always does actually have an angle to report.
        """

        if self._thermal_bridge_angle is not None:
            return self._thermal_bridge_angle

        if self.shape == Pad.SHAPE_CIRCLE or (
            self.shape == Pad.SHAPE_CUSTOM and self.anchor_shape == Pad.SHAPE_CIRCLE
        ):
            return 45

        return 90

    @thermal_bridge_angle.setter
    def thermal_bridge_angle(self, angle: float | None) -> None:
        """
        None means the default for the pad shape.
        """
        self._thermal_bridge_angle = angle

    @property
    def roundRadius(self) -> float:
        return self.getRoundRadius()

    @property
    def radius_ratio(self) -> float:
        # A pad shape that doesn't support round radii will return 0.0
        if not self._round_radius_handler:
            return 0.0
        return self._round_radius_handler.getRadiusRatio(min(self.size.x, self.size.y))

    @property
    def chamfer_corners(self) -> CornerSelection:
        return self._chamfer_corners
