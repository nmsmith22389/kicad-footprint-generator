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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) 2018 by Rene Poeschl, github @poeschlr

import copy
import dataclasses
import enum
import math
from typing import Union

from KicadModTree.util.corner_selection import CornerSelection
from KicadModTree.util.corner_handling import RoundRadiusHandler, ChamferSizeHandler
from kilibs.geom import BoundingBox, Vector2D
from kilibs.util.param_util import toVectorUseCopyIfNumber, getOptionalBoolTypeParam, getOptionalNumberTypeParam
from KicadModTree.nodes.Node import Node
from KicadModTree.util.kicad_util import lispString
from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.base.Circle import Circle
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Polygon import Polygon


class Pad(Node):
    r"""Add a Pad to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *number* (``int``, ``str``) --
          number/name of the pad (default: \"\")
        * *type* (``Pad.TYPE_THT``, ``Pad.TYPE_SMT``, ``Pad.TYPE_CONNECT``, ``Pad.TYPE_NPTH``) --
          type of the pad
        * *shape* (``Pad.SHAPE_CIRCLE``, ``Pad.SHAPE_OVAL``, ``Pad.SHAPE_RECT``, ``SHAPE_ROUNDRECT``,
          ``Pad.SHAPE_TRAPEZE``, ``SHAPE_CUSTOM``) --
          shape of the pad
        * *layers* (``Pad.LAYERS_SMT``, ``Pad.LAYERS_THT``, ``Pad.LAYERS_NPTH``) --
          layers on which are used for the pad
        * *fab_property* (``Pad.PROPERTY_BGA``, ``Pad.PROPERTY_FIDUCIAL_GLOBAL``,
          ``Pad.PROPERTY_FIDUCIAL_LOCAL``, ``Pad.PROPERTY_TESTPOINT``, ``Pad.PROPERTY_HEATSINK``,
          ``Pad.PROPERTY_CASTELLATED``) -- the pad fabrication property

        * *at* (``Vector2D``) --
          center position of the pad
        * *rotation* (``float``) --
          rotation of the pad
        * *size* (``float``, ``Vector2D``) --
          size of the pad
        * *offset* (``Vector2D``) --
          offset of the pad
        * *drill* (``float``, ``Vector2D``) --
          drill-size of the pad

        * *round_radius_handler* (``RoundRadiusHandler``) --
          An instance of the RoundRadiusHandler class
          Ignored for every shape except round rect
        * *clearance* (``float``) --
          The optional clearance token attribute defines the clearance from all copper to the pad. If not set,
          the footprint clearance is used. (default:None = use footprint clearance)
        * *tuning_properties* (``PadTuningProperties``, ``None`) --
          Pad tuning properties. None for "undefined", which is the KiCad
          default state (default None)

        * *solder_paste_margin_ratio* (``float``) --
          solder paste margin ratio of the pad (default: 0)
        * *solder_paste_margin* (``float``) --
          solder paste margin of the pad (default: 0)
        * *solder_mask_margin* (``float``) --
          solder mask margin of the pad (default: 0)

        * *zone_connection* (``Pad.ZoneConnection``) --
          zone connection of the pad (default: Pad.ZoneConnection.INHERIT)
        * *thermal_width* (``float, None``) --
          The optional thermal_width token attribute defines the thermal relief spoke width used for zone connection
          for the pad. This only affects a pad connected to a zone with a thermal relief. If not set,
          the footprint thermal_width setting is used.
        * *thermal_gap* (``float, None``) --
          The optional thermal_gap token attribute defines the distance from the pad to the zone of the thermal
          relief connection for the pad. This only affects a pad connected to a zone with a thermal relief.
          If not set, the footprint thermal_gap setting is used.
        * *thermal_bridge_angle*  (``float, None``) --
          The optional thermal bridge angle. If not given this defaults to the same default as KiCad
          (45 for circular pads, 90 for everything else)

        * *unconnected_layer_mode* (``UnconnectedLayerMode``) --
          Define how the pad behaves on layers where it is not connected
          (default: KEEP_ALL)

        * *x_mirror* (``[int, float](mirror offset)``) --
          mirror x direction around offset "point"
        * *y_mirror* (``[int, float](mirror offset)``) --
          mirror y direction around offset "point"

    :Example:

    >>> from KicadModTree import *
    >>> Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
    ...     at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT)
    """

    TYPE_THT = 'thru_hole'
    TYPE_SMT = 'smd'
    TYPE_CONNECT = 'connect'
    TYPE_NPTH = 'np_thru_hole'
    _TYPES = [TYPE_THT, TYPE_SMT, TYPE_CONNECT, TYPE_NPTH]

    SHAPE_CIRCLE = 'circle'
    SHAPE_OVAL = 'oval'
    SHAPE_RECT = 'rect'
    SHAPE_ROUNDRECT = 'roundrect'
    SHAPE_TRAPEZE = 'trapezoid'
    SHAPE_CUSTOM = 'custom'
    _SHAPES = [SHAPE_CIRCLE, SHAPE_OVAL, SHAPE_RECT, SHAPE_ROUNDRECT, SHAPE_TRAPEZE, SHAPE_CUSTOM]

    LAYERS_SMT = ['F.Cu', 'F.Paste', 'F.Mask']
    LAYERS_THT = ['*.Cu', '*.Mask']
    LAYERS_NPTH = ['*.Cu', '*.Mask']
    LAYERS_CONNECT_FRONT = ['F.Cu', 'F.Mask']
    LAYERS_CONNECT_BACK = ['B.Cu', 'B.Mask']

    ANCHOR_CIRCLE = 'circle'
    ANCHOR_RECT = 'rect'
    _ANCHOR_SHAPE = [ANCHOR_CIRCLE, ANCHOR_RECT]

    SHAPE_IN_ZONE_CONVEX = 'convexhull'
    SHAPE_IN_ZONE_OUTLINE = 'outline'
    _SHAPE_IN_ZONE = [SHAPE_IN_ZONE_CONVEX, SHAPE_IN_ZONE_OUTLINE]

    class FabProperty(enum.Enum):
        """
        Type-safe pad fabrication property
        """

        # Note that these constants do not necessarily correspond to the
        # strings used in the KiCad file format.
        BGA = 'bga'
        FIDUCIAL_GLOBAL = 'fiducial_global'
        FIDUCIAL_LOCAL = 'fiducial_local'
        TESTPOINT = 'testpoint'
        HEATSINK = 'heatsink'
        CASTELLATED = 'castellated'

    class ZoneConnection(enum.Enum):
        """
        Type-safe pad zone connection.
        """

        # Note that these constants do not necessarily correspond to the
        # values used in the KiCad file format, thay can be anything
        INHERIT = 0
        """For a pad, inherits from footprint, for a footprint, inherits from board."""
        NONE = 1
        THERMAL_RELIEF = 2
        SOLID = 3

    class UnconnectedLayerMode(enum.Enum):
        """
        Behaviour of a Padstack on layers without connection.

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

    def __init__(self, **kwargs):
        Node.__init__(self)

        self._initNumber(**kwargs)
        self._initType(**kwargs)
        self._initFabProperty(**kwargs)
        self._initShape(**kwargs)
        self._initPosition(**kwargs)
        self._initSize(**kwargs)
        self._initOffset(**kwargs)
        self._initDrill(**kwargs)  # requires pad type and offset
        self._initSolderPasteMargin(**kwargs)
        self._initSolderPasteMarginRatio(**kwargs)
        self._initSolderMaskMargin(**kwargs)
        self._initZoneConnection(**kwargs)

        self._initClearance(**kwargs)

        self._initThermalBridgeWidth(**kwargs)
        self._initThermalGap(**kwargs)
        self._initThermalBridgeAngle(**kwargs)

        self._initUnconnectedLayerMode(**kwargs)

        self.tuning_properties = kwargs.get("tuning_properties", None)

        self._initLayers(**kwargs)
        self._initMirror(**kwargs)

        self._round_radius_handler = kwargs.get("round_radius_handler", None)
        self.chamfer_size_handler = None
        self.chamfer_ratio = None

        if self.shape == self.SHAPE_OVAL and self.size[0] == self.size[1]:
            self.shape = self.SHAPE_CIRCLE

        if self.shape == Pad.SHAPE_ROUNDRECT:

            self._initChamferRatio(**kwargs)
            self._initChamferCorners(**kwargs)

            if not self._round_radius_handler:
                raise KeyError('round_radius_handler not declared for roundrect pads')

        if self.shape == Pad.SHAPE_CUSTOM:
            self._initAnchorShape(**kwargs)
            self._initShapeInZone(**kwargs)

            self.primitives = []
            if 'primitives' not in kwargs:
                raise KeyError('primitives must be declared for custom pads')

            for p in kwargs['primitives']:
                self.addPrimitive(p)

    def _initMirror(self, **kwargs):
        self.mirror = [None, None]
        if 'x_mirror' in kwargs and type(kwargs['x_mirror']) in [float, int]:
            self.mirror[0] = kwargs['x_mirror']
        if 'y_mirror' in kwargs and type(kwargs['y_mirror']) in [float, int]:
            self.mirror[1] = kwargs['y_mirror']

        if self.mirror[0] is not None:
            self.at.x = 2 * self.mirror[0] - self.at.x
            self.offset.x *= -1
        if self.mirror[1] is not None:
            self.at.y = 2 * self.mirror[1] - self.at.y
            self.offset.y *= -1

    def _initNumber(self, **kwargs):
        self.number = kwargs.get('number', "")  # default to an un-numbered pad

    def _initType(self, **kwargs):
        if not kwargs.get('type'):
            raise KeyError('type not declared (like "type=Pad.TYPE_THT")')
        self.type = kwargs.get('type')
        if self.type not in Pad._TYPES:
            raise ValueError('{type} is an invalid type for pads'.format(type=self.type))

    def _initFabProperty(self, **kwargs):
        prop = kwargs.get('fab_property', None)

        if prop is not None:
            self._fab_property = Pad.FabProperty(prop)
        else:
            self._fab_property = None

    def _initShape(self, **kwargs):
        if not kwargs.get('shape'):
            raise KeyError('shape not declared (like "shape=Pad.SHAPE_CIRCLE")')
        self.shape = kwargs.get('shape')
        if self.shape not in Pad._SHAPES:
            raise ValueError('{shape} is an invalid shape for pads'.format(shape=self.shape))

    def _initPosition(self, **kwargs):
        if not kwargs.get('at'):
            raise KeyError('center position not declared (like "at=[0,0]")')
        self.at = Vector2D(kwargs.get('at'))

        self.rotation = kwargs.get('rotation', 0)

    def _initSize(self, **kwargs):
        if not kwargs.get('size'):
            raise KeyError('pad size not declared (like "size=[1,1]")')
        self.size = toVectorUseCopyIfNumber(kwargs.get('size'), low_limit=0)

    def _initOffset(self, **kwargs):
        self.offset = Vector2D(kwargs.get('offset', [0, 0]))

    def _initDrill(self, **kwargs):
        if self.type in [Pad.TYPE_THT, Pad.TYPE_NPTH]:
            if not kwargs.get('drill'):
                raise KeyError('drill size required (like "drill=1")')
            self.drill = toVectorUseCopyIfNumber(kwargs.get('drill'), low_limit=0)
        else:
            self.drill = None
            if kwargs.get('drill'):
                pass  # TODO: throw warning because drill is not supported

    def _initSolderPasteMarginRatio(self, **kwargs):
        self.solder_paste_margin_ratio = kwargs.get('solder_paste_margin_ratio', 0)

    def _initSolderPasteMargin(self, **kwargs):
        self.solder_paste_margin = kwargs.get('solder_paste_margin', 0)

    def _initSolderMaskMargin(self, **kwargs):
        self.solder_mask_margin = kwargs.get('solder_mask_margin', 0)

    def _initZoneConnection(self, **kwargs):
        self.zone_connection = kwargs.get(
            "zone_connection", Pad.ZoneConnection.INHERIT
        )

    def _initThermalBridgeWidth(self, **kwargs):
        param_name = 'thermal_bridge_width'
        self.thermal_bridge_width = getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initThermalGap(self, **kwargs):
        param_name = 'thermal_gap'
        self.thermal_gap = getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initThermalBridgeAngle(self, **kwargs):
        param_name = 'thermal_bridge_angle'
        self.thermal_bridge_angle = getOptionalNumberTypeParam(kwargs,
                                                               param_name,
                                                               default_value=None)  # TODO: use default_value=90

    def _initUnconnectedLayerMode(self, **kwargs):
        self.unconnected_layer_mode = kwargs.get(
            "unconnected_layer_mode", Pad.UnconnectedLayerMode.KEEP_ALL
        )

    def _initClearance(self, **kwargs):
        param_name = 'clearance'
        self.clearance = getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initLayers(self, **kwargs):
        if not kwargs.get('layers'):
            raise KeyError('layers not declared (like "layers=[\'*.Cu\', \'*.Mask\', \'F.SilkS\']")')
        self.layers = kwargs.get('layers')

    def _initChamferRatio(self, **kwargs):

        if kwargs.get('chamfer_size_handler', None) is not None:
            self.chamfer_size_handler = kwargs['chamfer_size_handler']
        else:
            self.chamfer_size_handler = ChamferSizeHandler(must_be_square=True, **kwargs)

        self.chamfer_ratio = self.chamfer_size_handler.getChamferRatio(min(self.size))
        return self.chamfer_ratio

    def _initChamferCorners(self, **kwargs):
        val = kwargs.get('chamfer_corners', None)
        self._chamfer_corners = CornerSelection(val)

    def _initAnchorShape(self, **kwargs):
        self.anchor_shape = kwargs.get('anchor_shape', Pad.ANCHOR_CIRCLE)
        if self.anchor_shape not in Pad._ANCHOR_SHAPE:
            raise ValueError('{shape} is an illegal anchor shape'.format(shape=self.anchor_shape))

    def _initShapeInZone(self, **kwargs):
        self.shape_in_zone = kwargs.get('shape_in_zone', Pad.SHAPE_IN_ZONE_OUTLINE)
        if self.shape_in_zone not in Pad._SHAPE_IN_ZONE:
            raise ValueError('{shape} is an illegal specifier for the shape in zone option'
                             .format(shape=self.shape_in_zone))

    def rotate(self, angle, origin=(0, 0), use_degrees=True):
        r""" Rotate pad around given origin

        :params:
            * *angle* (``float``)
                rotation angle
            * *origin* (``Vector2D``)
                origin point for the rotation. default: (0, 0)
            * *use_degrees* (``boolean``)
                rotation angle is given in degrees. default:True
        """

        self.at.rotate(angle=angle, origin=origin, use_degrees=use_degrees)
        a = angle if use_degrees else math.degrees(angle)

        # subtraction because kicad text field rotation is the wrong way round
        self.rotation -= a
        return self

    def translate(self, distance_vector):
        r""" Translate pad

        :params:
            * *distance_vector* (``Vector2D``)
                2D vector defining by how much and in what direction to translate.
        """

        self.at += distance_vector
        return self

    # calculate the outline of a pad
    def calculateBoundingBox(self):
        if (self.shape in [Pad.SHAPE_CIRCLE]):
            return BoundingBox(
                min_pt=self.at - self.size / 2,
                max_pt=self.at + self.size / 2,
            )
        elif (self.shape in [Pad.SHAPE_RECT, Pad.SHAPE_ROUNDRECT, Pad.SHAPE_OVAL]):
            from ..specialized import RectLine
            rect = RectLine(start=- self.size / 2,
                            end=self.size / 2,
                            layer=None, width=0).rotate(self.rotation).translate(self.at)
            return rect.calculateBoundingBox()
        else:
            raise NotImplementedError("calculateBoundingBox is not implemented for pad shape '%s'" % self.shape)

    def _getRenderTreeText(self):
        render_strings = ['pad']
        render_strings.append(lispString(self.number))
        render_strings.append(lispString(self.type))
        render_strings.append(lispString(self.shape))
        render_strings.append('(at {x} {y})'.format(**self.at.to_dict()))
        render_strings.append('(size {x} {y})'.format(**self.size.to_dict()))
        render_strings.append('(drill {})'.format(self.drill))
        render_strings.append('(layers {})'.format(' '.join(self.layers)))

        render_text = Node._getRenderTreeText(self)
        render_text += ' ({})'.format(' '.join(render_strings))

        return render_text

    def copy_with(
        self,
        at: Vector2D | None = None,
        shape: str | None = None,
        number: str | int | None = None,
    ):
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

    def addPrimitive(self, p):
        r""" add a primitive to a custom pad

        :param p: the primitive to add
        """
        self.primitives.append(p)

    def getRoundRadius(self):
        if self.shape == Pad.SHAPE_CUSTOM:
            r_max = 0
            for p in self.primitives:
                r = p.width/2
                if r > r_max:
                    r_max = r
            return r_max
        return self._round_radius_handler.getRoundRadius(min(self.size))

    @property
    def fab_property(self) -> Union[FabProperty, None]:
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
    def thermal_bridge_angle(self, angle: float | None):
        """
        None means the default for the pad shape.
        """
        self._thermal_bridge_angle = angle

    @property
    def roundRadius(self):
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
