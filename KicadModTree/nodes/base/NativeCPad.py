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
# (C) 2024 by C. Kuhlmann, gitlab @CKuhlmann

from __future__ import annotations

from KicadModTree import Vector2D
from KicadModTree.nodes.base.Pad import Pad, RoundRadiusHandler
from KicadModTree.util.paramUtil import getOptionalNumberTypeParam, \
    getOptionalBoolTypeParam, toVectorUseCopyIfNumber

from typing import TypedDict, Callable
from typing_extensions import Unpack


class CornerSelectionNative():
    r"""Class for handling chamfer selection
        :param chamfer_select:
            * A list of bools do directly set the corners
              (top left, top right, bottom right, bottom left)
            * A dict with keys (constands see below)
            * The integer 1 means all corners
            * The integer 0 means no corners
            * A list of corner KiCad corner names that should be selected (with corners not in the list deselected)

        :constants:
            * CornerSelection.TOP_LEFT
            * CornerSelection.TOP_RIGHT
            * CornerSelection.BOTTOM_RIGHT
            * CornerSelection.BOTTOM_LEFT
    """

    TOP_LEFT = 'tl'
    TOP_RIGHT = 'tr'
    BOTTOM_RIGHT = 'br'
    BOTTOM_LEFT = 'bl'

    VALID_CORNER_VALUES = [0, 1, 2, 3, TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT]
    VALID_CORNER_NAMES = [TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT]

    def __init__(self, chamfer_select):
        self.top_left = False
        self.top_right = False
        self.bottom_right = False
        self.bottom_left = False

        if chamfer_select == 1:
            self.selectAll()
            return

        if chamfer_select == 0:
            return

        if chamfer_select is None:
            return

        if type(chamfer_select) is dict:
            for key in chamfer_select:
                self[key] = bool(chamfer_select[key])
        else:
            for i, value in enumerate(chamfer_select):
                if ((i not in CornerSelectionNative.VALID_CORNER_NAMES)
                        and (value in CornerSelectionNative.VALID_CORNER_NAMES)):
                    self[value] = True
                else:
                    self[i] = bool(value)

    def selectAll(self):
        for i in range(len(self)):
            self[i] = True

    def clearAll(self):
        for i in range(len(self)):
            self[i] = False

    def setLeft(self, value=1):
        self.top_left = bool(value)
        self.bottom_left = bool(value)

    def setTop(self, value=1):
        self.top_left = bool(value)
        self.top_right = bool(value)

    def setRight(self, value=1):
        self.top_right = bool(value)
        self.bottom_right = bool(value)

    def setBottom(self, value=1):
        self.bottom_left = bool(value)
        self.bottom_right = bool(value)

    def isAnySelected(self):
        for v in self:
            if v:
                return True
        return False

    def rotateCW(self):
        top_left_old = self.top_left

        self.top_left = self.bottom_left
        self.bottom_left = self.bottom_right
        self.bottom_right = self.top_right
        self.top_right = top_left_old
        return self

    def rotateCCW(self):
        top_left_old = self.top_left

        self.top_left = self.top_right
        self.top_right = self.bottom_right
        self.bottom_right = self.bottom_left
        self.bottom_left = top_left_old
        return self

    def __or__(self, other):
        return CornerSelectionNative([s or o for s, o in zip(self, other)])

    def __ior__(self, other):
        for i in range(len(self)):
            self[i] |= other[i]
        return self

    def __and__(self, other):
        return CornerSelectionNative([s and o for s, o in zip(self, other)])

    def __iand__(self, other):
        for i in range(len(self)):
            self[i] &= other[i]
        return self

    def __len__(self):
        return 4

    def __iter__(self):
        yield self.top_left
        yield self.top_right
        yield self.bottom_right
        yield self.bottom_left

    def __getitem__(self, item):
        if item in [0, CornerSelectionNative.TOP_LEFT]:
            return self.top_left
        if item in [1, CornerSelectionNative.TOP_RIGHT]:
            return self.top_right
        if item in [2, CornerSelectionNative.BOTTOM_RIGHT]:
            return self.bottom_right
        if item in [3, CornerSelectionNative.BOTTOM_LEFT]:
            return self.bottom_left

        raise IndexError('Index {} is out of range'.format(item))

    def __setitem__(self, item, value):
        if item in [0, CornerSelectionNative.TOP_LEFT,
                    NativeCPad.TOP_LEFT]:
            self.top_left = bool(value)
        elif item in [1, CornerSelectionNative.TOP_RIGHT,
                      NativeCPad.TOP_RIGHT]:
            self.top_right = bool(value)
        elif item in [2, CornerSelectionNative.BOTTOM_RIGHT,
                      NativeCPad.BOTTOM_RIGHT]:
            self.bottom_right = bool(value)
        elif item in [3, CornerSelectionNative.BOTTOM_LEFT,
                      NativeCPad.BOTTOM_LEFT]:
            self.bottom_left = bool(value)
        else:
            raise IndexError('Index {} is out of range'.format(item))

    def to_dict(self):
        return {
            CornerSelectionNative.TOP_LEFT: self.top_left,
            CornerSelectionNative.TOP_RIGHT: self.top_right,
            CornerSelectionNative.BOTTOM_RIGHT: self.bottom_right,
            CornerSelectionNative.BOTTOM_LEFT: self.bottom_left
        }

    def __str__(self):
        return str(self.to_dict())


class ChamferSizeHandler(object):
    r"""Handles chamfer setting of a pad

    :param \**kwargs:
        See below

    :Keyword Arguments:
    * *chamfer_ratio* (``float [0 <= r <= 0.5]``) --
      The chamfer ratio of the rounded rectangle. (default set by default_chamfer_ratio)
    * *maximum_chamfer* (``float``) --
      The maximum radius for the rounded rectangle.
      If the radius produced by the chamfer_ratio parameter for the pad would
      exceed the maximum radius, the ratio is reduced to limit the radius.
      (This is useful for IPC-7351C compliance as it suggests 25% ratio with limit 0.25mm)
    * *chamfer_exact* (``float``) --
      Set an exact round chamfer size for a pad.
    * *default_chamfer_ratio* (``float [0 <= r <= 0.5]``) --
      This parameter allows to set the default chamfer ratio
    """

    def __init__(self, **kwargs):
        default_chamfer_ratio = getOptionalNumberTypeParam(
            kwargs, 'default_chamfer_ratio', default_value=0.25,
            low_limit=0, high_limit=0.5)
        self.chamfer_ratio = getOptionalNumberTypeParam(
            kwargs, 'chamfer_ratio', default_value=default_chamfer_ratio,
            low_limit=0, high_limit=0.5)

        self.maximum_chamfer = getOptionalNumberTypeParam(
            kwargs, 'maximum_chamfer')
        chamfer_size = toVectorUseCopyIfNumber(kwargs.get(
            'chamfer_size'), low_limit=0, must_be_larger=False)

        # ChamferedPad, ChamferedNativePad use chamfer_size vector
        if (chamfer_size is not None) and ('chamfer_size' in kwargs.keys()) and (len(chamfer_size) > 1):
            chamfer_size = chamfer_size[0]
        else:
            chamfer_size = None

        self.chamfer_exact = getOptionalNumberTypeParam(
            kwargs, 'chamfer_exact', default_value=chamfer_size)

    def getChamferRatio(self, shortest_sidelength):
        r"""get the resulting chamfer ratio

        :param shortest_sidelength: shortest sidelength of a pad
        :return: the resulting round radius ratio to be used for the pad
        """

        if self.chamfer_exact is not None:
            if self.chamfer_exact > shortest_sidelength/2:
                raise ValueError(
                    "requested round radius of {} is too large for pad size of {}"
                    .format(self.chamfer_exact, shortest_sidelength)
                )
            if self.maximum_chamfer is not None:
                return min(self.chamfer_exact, self.maximum_chamfer)/shortest_sidelength
            else:
                return self.chamfer_exact/shortest_sidelength
        if self.maximum_chamfer is not None:
            if self.chamfer_ratio*shortest_sidelength > self.maximum_chamfer:
                return self.maximum_chamfer/shortest_sidelength

        return self.chamfer_ratio

    def getChamferSize(self, shortest_sidelength):
        r"""get the resulting round radius

        :param shortest_sidelength: shortest sidelength of a pad
        :return: the resulting round radius to be used for the pad
        """
        return self.getChamferRatio(shortest_sidelength)*shortest_sidelength

    def roundingRequested(self):
        r"""Check if the pad has a rounded corner

        :return: True if rounded corners are required
        """
        if self.kicad4_compatible:
            return False

        if self.maximum_chamfer == 0:
            return False

        if self.chamfer_exact == 0:
            return False

        if self.chamfer_ratio == 0:
            return False

        return True

    def limitMaxChamfer(self, limit):
        r"""Set a new maximum limit

        :param limit: the new limit.
        """

        if not self.roundingRequested():
            return
        if self.maximum_chamfer is not None:
            self.maximum_chamfer = min(self.maximum_chamfer, limit)
        else:
            self.maximum_chamfer = limit

    def __str__(self):
        return "ratio {}, max {}, exact {}, v4 compatible {}".format(
            self.chamfer_ratio, self.maximum_chamfer,
            self.chamfer_exact, self.kicad4_compatible
        )


class NativeCPadArgs(TypedDict):
    number: int | str
    type: str
    shape: str
    layers: list[str]
    at: Vector2D | tuple | list
    rotation: float
    size: Vector2D | tuple | list

    offset: Vector2D | tuple | list
    drill: float | Vector2D

    radius_ratio: float
    maximum_radius: float
    round_radius_exact: float
    round_radius_handler: Callable

    chamfer_ratio: float
    maximum_chamfer: float
    chamfer_exact: float
    chamfer_size_handler: Callable
    chamfer_corners: list | tuple

    clearance: float
    net: tuple | list
    die_length: float
    solder_paste_margin_ratio: float
    solder_paste_margin: float
    solder_mask_margin: float

    zone_connection: int
    thermal_width: float
    thermal_gap: float

    remove_unused_layer: bool
    keep_end_layers: bool

    x_mirror: bool
    y_mirror: bool
    locked: bool
    property: str


class NativeCPad(Pad):
    r"""Add a Pad to the render tree, that represents a native KiCad rounded and/or chamfered pad

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

        * *at* (``Vector2D``) --
          center position of the pad
        * *rotation* (``float``) --
          rotation of the pad
        * *size* (``float``, ``Vector2D``) --
          size of the pad
        * *offset* (``Vector2D``) --
          offset of the pad's drill hole
        * *drill* (``float``, ``Vector2D``) --
          drill-size of the pad, give two main diameters to create an oval / rounded slot

        * *radius_ratio* (``float``) --
          The radius ratio of the rounded rectangle ranging from 0 to 0.5.
          Ignored for every shape except round rect.
        * *maximum_radius* (``float``) --
          The maximum radius for the rounded rectangle.
          If the radius produced by the radius_ratio parameter for the pad would
          exceed the maximum radius, the ratio is reduced to limit the radius.
          (This is useful for IPC-7351C compliance as it suggests 25% ratio with limit 0.25mm)
          Ignored for every shape except round rect.
        * *round_radius_exact* (``float``) --
          Set an exact round radius for a pad.
          Ignored for every shape except round rect
        * *round_radius_handler* (``RoundRadiusHandler``) --
          An instance of the RoundRadiusHandler class
          If this is given then all other round radius specifiers are ignored
          Ignored for every shape except round rect

        * *chamfer_ratio* (``float``) --
          The optional chamfer_ratio token defines the scaling factor of the pad to chamfer size.
          The scaling factor is a number between 0 and 0.5.
        * *maximum_chamfer* (``float``) --
          The maximum chamfer size for the chamfered (rounded) rectangle.
          If the chamfer produced by the chamfer_ratio parameter for the pad would
          exceed the maximum chamfer, the chamfer ratio is reduced to limit the chamfer size.
        * *chamfer_exact* (``float``) --
          Set an exact chamfer size for a pad.
          Ignored for every shape except round rect
        * *chamfer_size_handler* (``ChamferSizeHandler``) --
          An instance of the ChamferSizeHandler class
          If this is given then all other chamfer specifiers are ignored
          Ignored for every shape except round rect
        * *chamfer_corners* (``[TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT]``,
          ``ChamferedNativePad.CornerSelection``) --
          Defines which corners should be chamfered. Receives a list of corner identifers.
          The optional chamfer token defines a list of one or more rectangular pad corners that get chamfered.
          Valid chamfer corner attributes are
          NativeCPad.TOP_LEFT, NativeCPad.TOP_RIGHT, NativeCPad.BOTTOM_LEFT, NativeCPad.BOTTOM_RIGHT
          or a ChamferedNativePad.CornerSelection class instance

        * *clearance* (``float``) --
          The optional clearance token attribute defines the clearance from all copper to the pad. If not set,
          the footprint clearance is used. (default:None = use footprint clearance)
        * *net* (``(int, string)), NULL``) --
          The optional net token defines the integer number and name string of the net connection for the pad.
        * *die_length* (``float``) --
          The optional die_length token attribute defines the die length between the component pad and physical
          chip inside the component package.

        * *solder_paste_margin_ratio* (``float``) --
          solder paste margin ratio of the pad (default: 0)
        * *solder_paste_margin* (``float``) --
          solder paste margin of the pad (default: 0)
        * *solder_mask_margin* (``float``) --
          solder mask margin of the pad (default: 0)

        * *zone_connection* (``ZONE_NO_CONNECT, ZONE_THERMAL_RELIEF_CONNECT, ZONE_SOLID_CONNECT, int``) --
          The optional zone_connection token attribute defines type of zone connect for the pad. If not defined,
          the footprint zone_connection setting is used. Valid connection types are integers values from 0 to 3
          which defines: ZONE_NO_CONNECT=0, ZONE_THERMAL_RELIEF_CONNECT=1, ZONE_SOLID_CONNECT=2
        * *thermal_width* (``float, None``) --
          The optional thermal_width token attribute defines the thermal relief spoke width used for zone connection
          for the pad. This only affects a pad connected to a zone with a thermal relief. If not set,
          the footprint thermal_width setting is used.
        * *thermal_gap* (``float, None``) --
          The optional thermal_gap token attribute defines the distance from the pad to the zone of the thermal
          relief connection for the pad. This only affects a pad connected to a zone with a thermal relief.
          If not set, the footprint thermal_gap setting is used.

        * *remove_unused_layer* (``bool``) --
          The optional remove_unused_layer token specifies that the copper should be removed from any layers
          the pad is not connected to. (default: False)
        * *keep_end_layers* (``bool``) --
          The optional keep_end_layers token specifies that the top and bottom layers should be retained when
          removing the copper from unused layers.


        * *x_mirror* (``[int, float](mirror offset)``) --
          mirror x direction around offset "point"
        * *y_mirror* (``[int, float](mirror offset)``) --
          mirror y direction around offset "point"

        * *locked* (``bool``) --
          The optional locked token defines if the footprint pad can be edited. (default: False = not locked)

        * *property* (``PAD_PROP_BGA, PAD_PROP_FIDUCIAL_GLOB, PAD_PROP_FIDUCIAL_LOC, PAD_PROP_TESTPOINT,
          PAD_PROP_HEATSINK, PAD_PROP_HEATSINK, PAD_PROP_CASTELLATED``) --
          The optional property token defines any special properties for the pad.
          Valid properties are NativeCPad.PAD_PROP_BGA, NativeCPad.PAD_PROP_FIDUCIAL_GLOB,
          NativeCPad.PAD_PROP_FIDUCIAL_LOC, NativeCPad.PAD_PROP_TESTPOINT, NativeCPad.PAD_PROP_HEATSINK,
          NativeCPad.PAD_PROP_HEATSINK, NativeCPad.PAD_PROP_CASTELLATED.



    :Example:

    >>> from KicadModTree.nodes.base.NativeCPad import *
    >>> NativeCPad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
    ...     at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT)

        NativeCPad(number=, type=, shape=, layers=, at=, rotation=, size=, offset=, drill=, radius_ratio=,
        maximum_radius=, round_radius_exact=, round_radius_handler=, chamfer_ratio=, maximum_chamfer=,
        chamfer_exact=, chamfer_size_handler=, chamfer_corners=, clearance=, net=, die_length=,
        solder_paste_margin_ratio=, solder_paste_margin=, solder_mask_margin=, zone_connection=, thermal_width=,
        thermal_gap=, remove_unused_layer=, keep_end_layers=, x_mirror=, y_mirror=, locked=, property=)
    .
    """

    PAD_PROP_BGA = 'pad_prop_bga'
    PAD_PROP_FIDUCIAL_GLOB = 'pad_prop_fiducial_glob'
    PAD_PROP_FIDUCIAL_LOC = 'pad_prop_fiducial_loc'
    PAD_PROP_TESTPOINT = 'pad_prop_testpoint'
    PAD_PROP_HEATSINK = 'pad_prop_heatsink'
    PAD_PROP_HEATSINK = 'pad_prop_heatsink'
    PAD_PROP_CASTELLATED = 'pad_prop_castellated'

    TOP_LEFT = 'top_left'
    TOP_RIGHT = 'top_right'
    BOTTOM_LEFT = 'bottom_left'
    BOTTOM_RIGHT = 'bottom_right'

    ZONE_NO_CONNECT = 0
    ZONE_THERMAL_RELIEF_CONNECT = 1
    ZONE_SOLID_CONNECT = 2

    def __init__(self, **kwargs: Unpack[NativeCPadArgs]):
        super().__init__(**kwargs)

        self.maximum_chamfer = self._initMaximumChamfer(**kwargs)
        self.chamfer_ratio = self._initChamferRatio(**kwargs)
        self.chamfer_corners = self._initChamferCorners(**kwargs)

        self.clearance = self._initClearance(**kwargs)
        self.net = self._initNet(**kwargs)
        self.die_length = self._initDieLength(**kwargs)

        self.zone_connect = self._initZoneConnection(**kwargs)
        self.thermal_bridge_width = self._initThermalBridgeWidth(**kwargs)
        self.thermal_gap = self._initThermalGap(**kwargs)
        self.thermal_bridge_angle = self._initThermalBridgeAngle(**kwargs)

        self.remove_unused_layer = self._initRemoveUnusedLayer(**kwargs)
        self.keep_end_layers = self._initKeepEndLayers(**kwargs)

        self.locked = self._initLocked(**kwargs)
        self.pad_property = self._initPadProperty(**kwargs)

        pass

    def _initMaximumChamfer(self, **kwargs):
        param_name = 'maximum_chamfer'
        return getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initChamferCorners(self, **kwargs):
        param_name = 'chamfer_corners'
        param_alt_name = 'corner_selection'
        val = kwargs.get(param_name, None)
        val_alt = kwargs.get(param_alt_name, None)
        if (val is None):
            val = val_alt
        elif (val is None) and (val_alt is None) and not (list(val) == list(val_alt)):
            try:
                val = (*val, *val_alt)  # append
            except Exception as e:
                pass

        return CornerSelectionNative(val)

    def _initZoneConnection(self, **kwargs):
        param_name = 'zone_connect'
        val = getOptionalNumberTypeParam(
            kwargs, param_name, default_value=None)
        if val in [NativeCPad.ZONE_NO_CONNECT, NativeCPad.ZONE_THERMAL_RELIEF_CONNECT, NativeCPad.ZONE_SOLID_CONNECT]:
            return val
        return None

    def _initThermalBridgeWidth(self, **kwargs):
        param_name = 'thermal_bridge_width'
        return getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initThermalGap(self, **kwargs):
        param_name = 'thermal_gap'
        return getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initThermalBridgeAngle(self, **kwargs):
        param_name = 'thermal_bridge_angle'
        return getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initRemoveUnusedLayer(self, **kwargs):
        param_name = 'remove_unused_layer'
        return getOptionalBoolTypeParam(kwargs, param_name, default_value=None)

    def _initKeepEndLayers(self, **kwargs):
        param_name = 'keep_end_layers'
        return getOptionalBoolTypeParam(kwargs, param_name, default_value=None)

    def _initNet(self, **kwargs):
        param_name = 'net'
        net_arg = kwargs.get(param_name, None)
        if (net_arg is not None):
            if (len(net_arg) >= 2):
                try:
                    netnum = int(net_arg[0])
                    netname = str(net_arg[1])
                except Exception as e:
                    raise ValueError(
                        "NativeCPad *net* param must be a list or tuple with the first element being an int and "
                        + f"the second a string. Received "+repr(net_arg)+" causing "+str(e)+".")
                return (netnum, netname)
            else:
                raise ValueError(
                    "NativeCPad *net* param must be a list or tuple with the first element being an int and the "
                    + f"second a string. Not enough items, received "+repr(net_arg)+".")
        return None

    def _initClearance(self, **kwargs):
        param_name = 'clearance'
        return getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initDieLength(self, **kwargs):
        param_name = 'die_length'
        return getOptionalNumberTypeParam(kwargs, param_name, default_value=None)

    def _initLocked(self, **kwargs):
        param_name = 'locked'
        return getOptionalBoolTypeParam(kwargs, param_name, default_value=None)

    def _initPadProperty(self, **kwargs):
        param_name = 'property'
        val = kwargs.get(param_name, None)
        if val in [NativeCPad.PAD_PROP_BGA, NativeCPad.PAD_PROP_FIDUCIAL_GLOB, NativeCPad.PAD_PROP_FIDUCIAL_LOC,
                   NativeCPad.PAD_PROP_TESTPOINT, NativeCPad.PAD_PROP_HEATSINK, NativeCPad.PAD_PROP_HEATSINK,
                   NativeCPad.PAD_PROP_CASTELLATED]:
            return val
        return None

    # override from Pad._initRadiusRatio
    def _initRadiusRatio(self, **kwargs):
        # print('_initRadiusRatio override called')

        if ('round_radius_handler' in kwargs) and (kwargs['round_radius_handler'] is not None):
            self.round_radius_handler = kwargs['round_radius_handler']
        else:
            self.round_radius_handler = RoundRadiusHandler(**kwargs)

        self.radius_ratio = self.round_radius_handler.getRadiusRatio(
            min(self.size))
        if self.radius_ratio == 0 and (hasattr(self, "chamfer_ratio") and self.chamfer_ratio == 0):
            self.shape = Pad.SHAPE_RECT
        # else:
        #    self.shape = Pad.SHAPE_ROUNDRECT

        return self.radius_ratio

    def _initChamferRatio(self, **kwargs):

        if ('chamfer_size_handler' in kwargs) and (kwargs['chamfer_size_handler'] is not None):
            self.chamfer_size_handler = kwargs['chamfer_size_handler']
        else:
            self.chamfer_size_handler = ChamferSizeHandler(**kwargs)

        self.chamfer_ratio = self.chamfer_size_handler.getChamferRatio(
            min(self.size))

        if self.chamfer_ratio == 0 and (hasattr(self, "radius_ratio") and self.radius_ratio == 0):
            self.shape = Pad.SHAPE_RECT
        # else:
        #    self.shape = Pad.SHAPE_ROUNDRECT
        return self.chamfer_ratio


class NativeCPadFactory(object):
    r"""Factory class to add a Pad to the render tree, that represents a native KiCad rounded and/or chamfered pad

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

        * *at* (``Vector2D``) --
          center position of the pad
        * *rotation* (``float``) --
          rotation of the pad
        * *size* (``float``, ``Vector2D``) --
          size of the pad
        * *offset* (``Vector2D``) --
          offset of the pad's drill hole
        * *drill* (``float``, ``Vector2D``) --
          drill-size of the pad

        * *radius_ratio* (``float``) --
          The radius ratio of the rounded rectangle ranging from 0 to 0.5.
          Ignored for every shape except round rect.
        * *maximum_radius* (``float``) --
          The maximum radius for the rounded rectangle.
          If the radius produced by the radius_ratio parameter for the pad would
          exceed the maximum radius, the ratio is reduced to limit the radius.
          (This is useful for IPC-7351C compliance as it suggests 25% ratio with limit 0.25mm)
          Ignored for every shape except round rect.
        * *round_radius_exact* (``float``) --
          Set an exact round radius for a pad.
          Ignored for every shape except round rect
        * *round_radius_handler* (``RoundRadiusHandler``) --
          An instance of the RoundRadiusHandler class
          If this is given then all other round radius specifiers are ignored
          Ignored for every shape except round rect

        * *chamfer_ratio* (``float``) --
          The optional chamfer_ratio token defines the scaling factor of the pad to chamfer size.
          The scaling factor is a number between 0 and 0.5.
        * *maximum_chamfer* (``float``) --
          The maximum chamfer size for the chamfered (rounded) rectangle.
          If the chamfer produced by the chamfer_ratio parameter for the pad would
          exceed the maximum chamfer, the chamfer ratio is reduced to limit the chamfer size.
        * *chamfer_exact* (``float``) --
          Set an exact chamfer size for a pad.
          Ignored for every shape except round rect
        * *chamfer_size_handler* (``ChamferSizeHandler``) --
          An instance of the ChamferSizeHandler class
          If this is given then all other chamfer specifiers are ignored
          Ignored for every shape except round rect
        * *chamfer_corners*
          (``[TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT]``, ``ChamferedNativePad.CornerSelection``) --
          Defines which corners should be chamfered. Receives a list of corner identifers.
          The optional chamfer token defines a list of one or more rectangular pad corners that get chamfered.
          Valid chamfer corner attributes are NativeCPad.TOP_LEFT, NativeCPad.TOP_RIGHT, NativeCPad.BOTTOM_LEFT,
            NativeCPad.BOTTOM_RIGHT or a ChamferedNativePad.CornerSelection class instance

        * *clearance* (``float``) --
          The optional clearance token attribute defines the clearance from all copper to the pad. If not set,
          the footprint clearance is used. (default:None = use footprint clearance)
        * *net* (``(int, string)), NULL``) --
          The optional net token defines the integer number and name string of the net connection for the pad.
        * *die_length* (``float``) --
          The optional die_length token attribute defines the die length between the component pad and physical
          chip inside the component package.

        * *solder_paste_margin_ratio* (``float``) --
          solder paste margin ratio of the pad (default: 0)
        * *solder_paste_margin* (``float``) --
          solder paste margin of the pad (default: 0)
        * *solder_mask_margin* (``float``) --
          solder mask margin of the pad (default: 0)

        * *zone_connection* (``ZONE_NO_CONNECT, ZONE_THERMAL_RELIEF_CONNECT, ZONE_SOLID_CONNECT, int``) --
          The optional zone_connection token attribute defines type of zone connect for the pad. If not defined,
          the footprint zone_connection setting is used.
          Valid connection types are integers values from 0 to 3 which defines: ZONE_NO_CONNECT=0,
          ZONE_THERMAL_RELIEF_CONNECT=1, ZONE_SOLID_CONNECT=2
        * *thermal_width* (``float, None``) --
          The optional thermal_width token attribute defines the thermal relief spoke width used
          for zone connection for the pad. This only affects a pad connected to a zone with a thermal relief.
          If not set, the footprint thermal_width setting is used.
        * *thermal_gap* (``float, None``) --
          The optional thermal_gap token attribute defines the distance from the pad to the zone of the thermal
          relief connection for the pad. This only affects a pad connected to a zone with a thermal relief.
          If not set, the footprint thermal_gap setting is used.

        * *remove_unused_layer* (``bool``) --
          The optional remove_unused_layer token specifies that the copper should be removed from any layers
          the pad is not connected to. (default: False)
        * *keep_end_layers* (``bool``) --
          The optional keep_end_layers token specifies that the top and bottom layers should be
          retained when removing the copper from unused layers.


        * *x_mirror* (``[int, float](mirror offset)``) --
          mirror x direction around offset "point"
        * *y_mirror* (``[int, float](mirror offset)``) --
          mirror y direction around offset "point"

        * *locked* (``bool``) --
          The optional locked token defines if the footprint pad can be edited. (default: False = not locked)

        * *property* (``PAD_PROP_BGA, PAD_PROP_FIDUCIAL_GLOB, PAD_PROP_FIDUCIAL_LOC, PAD_PROP_TESTPOINT,
          PAD_PROP_HEATSINK, PAD_PROP_HEATSINK, PAD_PROP_CASTELLATED``) --
          The optional property token defines any special properties for the pad.
          Valid properties are NativeCPad.PAD_PROP_BGA, NativeCPad.PAD_PROP_FIDUCIAL_GLOB,
          NativeCPad.PAD_PROP_FIDUCIAL_LOC, NativeCPad.PAD_PROP_TESTPOINT, NativeCPad.PAD_PROP_HEATSINK,
          NativeCPad.PAD_PROP_HEATSINK, NativeCPad.PAD_PROP_CASTELLATED.

    :Example:

    >>> from KicadModTree.nodes.base.NativeCPad import *
    >>> NativeCPadCactory(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
    ...     at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT)

        NativeCPadFactory(number=, type=, shape=, layers=, at=, rotation=, size=, offset=, drill=, radius_ratio=,
        maximum_radius=, round_radius_exact=, round_radius_handler=, chamfer_ratio=, maximum_chamfer=, chamfer_exact=,
        chamfer_size_handler=, chamfer_corners=, clearance=, net=, die_length=, solder_paste_margin_ratio=,
        solder_paste_margin=, solder_mask_margin=, zone_connection=, thermal_width=, thermal_gap=,
        remove_unused_layer=, keep_end_layers=, x_mirror=, y_mirror=, locked=, property=)
    .
    """

    def __init__(self,
                 number="", type=NativeCPad.TYPE_SMT, shape=NativeCPad.SHAPE_ROUNDRECT, layers=NativeCPad.LAYERS_SMT,
                 at=(0.0, 0.0), rotation=90.0, size=(1.0, 2.0),
                 offset=(0.0, 0.0), drill=None,
                 radius_ratio=0.2, maximum_radius=0.25, round_radius_exact=None, round_radius_handler=None,
                 chamfer_ratio=0.2, maximum_chamfer=0.25, chamfer_exact=None, chamfer_size_handler=None,
                 chamfer_corners=[NativeCPad.TOP_LEFT, NativeCPad.TOP_RIGHT], clearance=None, net=None,
                 die_length=None, solder_paste_margin_ratio=None, solder_paste_margin=None, solder_mask_margin=None,
                 zone_connection=NativeCPad.ZONE_THERMAL_RELIEF_CONNECT, thermal_width=None, thermal_gap=None,
                 remove_unused_layer=None, keep_end_layers=None,
                 x_mirror=None, y_mirror=None, locked=None, property=None
                 ) -> None:

        self.number = number
        self.type = type
        self.shape = shape
        self.layers = layers
        self.at = at
        self.rotation = rotation
        self.size = size

        self.offset = offset
        self.drill = drill

        self.radius_ratio = radius_ratio
        self.maximum_radius = maximum_radius
        self.round_radius_exact = round_radius_exact
        self.round_radius_handler = round_radius_handler

        self.chamfer_ratio = chamfer_ratio
        self.maximum_chamfer = maximum_chamfer
        self.chamfer_exact = chamfer_exact
        self.chamfer_size_handler = chamfer_size_handler
        self.chamfer_corners = chamfer_corners

        self.clearance = clearance
        self.net = net
        self.die_length = die_length
        self.solder_paste_margin_ratio = solder_paste_margin_ratio
        self.solder_paste_margin = solder_paste_margin
        self.solder_mask_margin = solder_mask_margin

        self.zone_connection = zone_connection
        self.thermal_width = thermal_width
        self.thermal_gap = thermal_gap

        self.remove_unused_layer = remove_unused_layer
        self.keep_end_layers = keep_end_layers

        self.x_mirror = x_mirror
        self.y_mirror = y_mirror
        self.locked = locked
        self.property = property

    def output(self) -> NativeCPad:
        r"""The NaticeCPad class instance output of the factory with the current parameters given during construction
            or set using properties until output is called
        """
        return self.manufacture()

    def manufacture(self) -> NativeCPad:

        self._last_native_c_pad = NativeCPad(
            number=self.number, type=self.type, shape=self.shape, layers=self.layers, at=self.at,
            rotation=self.rotation, size=self.size,
            offset=self.offset, drill=self.drill,
            radius_ratio=self.radius_ratio, maximum_radius=self.maximum_radius,
            round_radius_exact=self.round_radius_exact, round_radius_handler=self.round_radius_handler,
            chamfer_ratio=self.chamfer_ratio, maximum_chamfer=self.maximum_chamfer, chamfer_exact=self.chamfer_exact,
            chamfer_size_handler=self.chamfer_size_handler, chamfer_corners=self.chamfer_corners,
            clearance=self.clearance, net=self.net, die_length=self.die_length,
            solder_paste_margin_ratio=self.solder_paste_margin_ratio, solder_paste_margin=self.solder_paste_margin,
            solder_mask_margin=self.solder_mask_margin,
            zone_connection=self.zone_connection, thermal_width=self.thermal_width, thermal_gap=self.thermal_gap,
            remove_unused_layer=self.remove_unused_layer, keep_end_layers=self.keep_end_layers,
            x_mirror=self.x_mirror, y_mirror=self.y_mirror, locked=self.locked, property=self.property
        )

        return self._last_native_c_pad
