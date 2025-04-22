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
# (C) 2016-2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

import abc
import re
from pathlib import Path
from typing import Optional, List

from kilibs.geom import PolygonPoints
from KicadModTree.FileHandler import FileHandler
from KicadModTree.util.kicad_util import SexprSerializer
from KicadModTree.util.kicad_util import *
from KicadModTree.util.corner_selection import CornerSelection
# TODO: why .KicadModTree is not enough?
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.EmbeddedFonts import EmbeddedFonts
from KicadModTree.nodes.base.Group import Group
from KicadModTree.nodes.base.Rect import Rect
from KicadModTree.nodes.base.Text import Text, Property
from KicadModTree.nodes.base.Pad import Pad
from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.base.Circle import Circle
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.LineStyle import LineStyle
from KicadModTree.nodes.base.Polygon import Polygon
from KicadModTree.nodes.base.PolygonArc import PolygonArc
from KicadModTree.nodes.base.CompoundPolygon import CompoundPolygon
from KicadModTree.nodes.base.Model import Model
from KicadModTree.nodes.Footprint import Footprint, FootprintType
from KicadModTree.nodes.base.Zone import Zone, PadConnection, ZoneFill, Keepouts


DEFAULT_LAYER_WIDTH = {'F.SilkS': 0.12,
                       'B.SilkS': 0.12,
                       'F.Fab': 0.10,
                       'B.Fab': 0.10,
                       'F.CrtYd': 0.05,
                       'B.CrtYd': 0.05}

DEFAULT_WIDTH_POLYGON_PAD = 0

DEFAULT_WIDTH = 0.15


def _get_layer_width(layer, width=None):
    if width is not None:
        return width
    else:
        return DEFAULT_LAYER_WIDTH.get(layer, DEFAULT_WIDTH)


def layer_key_func(layer: str) -> int:
    """
    Get the KiCad sorting key for a layer name.

    Approximate sorting order from PCB_IO_KICAD_SEXPR::formatLayers()
    """

    layer_map = {

        # These are specials in this order in formatLayers()
        # which come first
        "*.Cu": -1000,
        "F&B.Cu": -999,
        "*.Adhes": -998,
        "*.Paste": -997,
        "*.SilkS": -996,
        "*.Mask": -995,
        "*.CrtYd": -994,
        "*.Fab": -993,

        # Single layer IDs come after
        # Copper layers are even numbers
        "F.Cu": 0,
        "B.Cu": 2,

        "F.Mask": 1,
        "B.Mask": 3,
        "F.SilkS": 5,
        "B.SilkS": 7,
        "F.Adhes": 9,
        "B.Adhes": 11,
        "F.Paste": 13,
        "B.Paste": 15,

        "Dwgs.User": 17,
        "Cmts.User": 19,
        "Eco1.User": 21,
        "Eco2.User": 23,

        "Edge.Cuts": 25,
        "Margin": 27,

        "B.CrtYd": 29,
        "F.CrtYd": 31,

        "B.Fab": 33,
        "F.Fab": 35,
    }

    try:
        return layer_map[layer]
    except KeyError:
        # inner layers: even numbers from 4
        if m := re.match(r'^In(\d+)\.Cu$', layer):
            return (int(m.group(1)) + 1) * 2
        # user layers from 39 onwards
        if m := re.match(r'^User\.(\d)$', layer):
            return 38 + int(m.group(1))

    raise ValueError(f"Unhandled layer for sorting: {layer}")


def group_key_func(item) -> List[int]:
    keys = []

    if item.hasValidTStamp():
        keys += [item.getTStamp()]

    if item.getGroupMemberNodes() is not None:
        keys += [len(item.getGroupMemberNodes())]

    return keys


def graphic_key_func(item) -> List[int]:
    """
    Approximate sorting order from FOOTPRINT::cmp_drawings in KiCad's
    pcbnew/footprint.cpp.

    The KiCad drawing function handles text too, but we separate that
    out earlier.
    """

    def graphic_shape_key(item):
        if isinstance(item, Line):
            return 0
        elif isinstance(item, Rect):
            return 1
        elif isinstance(item, Arc):
            return 2
        elif isinstance(item, Circle):
            return 3
        elif isinstance(item, Polygon):
            return 4
        elif isinstance(item, CompoundPolygon):
            return 4
        # Not yet implements
        # elif isinstance(item, Bezier):
            # return 5

        raise ValueError(f"Graphic shape ordering not defined: {item}")

    keys = [layer_key_func(item.layer), graphic_shape_key(item)]

    # after this point, the different shape types will only
    # be compared amongst themselves

    if isinstance(item, (Line, Rect)):
        start_pos = item.getRealPosition(item.start_pos)
        end_pos = item.getRealPosition(item.end_pos)
        keys += [
            start_pos.x, start_pos.y,
            end_pos.x, end_pos.y
        ]
    elif isinstance(item, Arc):
        start_pos = item.getStartPoint()
        end_pos = item.getEndPoint()
        # Match KiCad normalisation of negative arc angles
        # (and the one in _serialize_ArcPoints).
        if item.angle < 0:
            start_pos, end_pos = end_pos, start_pos
        keys += [
            start_pos.x, start_pos.y,
            end_pos.x, end_pos.y,
            item.center_pos.x, item.center_pos.y,
        ]
    elif isinstance(item, Circle):
        center_pos = item.getRealPosition(item.center_pos)
        keys += [
            center_pos.x, center_pos.y,
            center_pos.x + item.radius, center_pos.y,
        ]

    if isinstance(item, Polygon):
        keys += [len(item.nodes)]
        keys += [[item.getRealPosition(pt).x, item.getRealPosition(pt).y] for pt in item.nodes]

    if isinstance(item, Text):
        keys += [item.thickness]
    elif item.width is not None:
        keys += [item.width]

    if item.hasValidTStamp():
        keys += [item.getTStamp()]

    return keys


def text_key_func(text: Text) -> List[int]:
    """
    Approximate sorting order from FOOTPRINT::cmp_drawings in KiCad's
    pcbnew/footprint.cpp.

    In KiCad, this is done in the same container as graphics, but it's
    easer to separate this here.
    """
    return [layer_key_func(text.layer)]


def pad_shape_key_func(shape: str) -> int:

    shapes = ['circle', 'rect', 'oval', 'trapezoid', 'roundrect', 'custom']

    try:
        return shapes.index(shape)
    except ValueError:
        return 1000


def pad_key_func(pad: Pad) -> List[int]:
    """
    Approximate sorting order from FOOTPRINT::cmp_pads in KiCad's
    pcbnew/footprint.cpp.
    """
    def pad_num_key(n: str) -> list:
        # We want to sort pads with multiple name components such that A2 comes after A1 and before A10,
        # and all the Ax come before all Bx.
        # Example sort order: "", "0", "1", "2", "10", "A", "A1", "A2", "A10", "A100", "B", "B1"...
        # To achieve this, we split by name components such that digit sequences stay as individual tokens.
        # We will later compare lists of tuples, with the list length being the component count.

        # Split the strings into substrings containing digits and those containing everything else.
        # For example: 'a10.2' => ['a', '10', '.', '2']
        substrings = re.findall(r'\d+|[^\d]+', n)
        # To avoid comparing ints to strings, we create tuples with each item and its category number.
        # Ints sort before strings, so they are category 1, and strings get category 2.
        # For example: ['a', '10', '.', '2'] => [(2, 'a'), (1, 10), (2, '.'), (1, 2)]
        return [
            (1, int(substr)) if substr.isdigit() else (2, substr)
            for substr in substrings
        ]

    at = pad.getRealPosition(pad.at)
    keys = [pad_num_key(str(pad.number)),
            at.x, at.y,
            pad.size.x, pad.size.y,
            pad_shape_key_func(pad.shape)
            ]
    return keys


def zone_key_func(zone: Zone) -> List:
    """
    Approximate sorting order from FOOTPRINT::cmp_zones in KiCad's
    pcbnew/footprint.cpp.
    """
    keys = [zone.priority if zone.priority else 0,
            [layer_key_func(layer) for layer in zone.layers],
            len(zone.nodes),
            [[pt.x, pt.y] for pt in zone.nodes]
            ]

    if zone.hasValidTStamp():
        keys += [zone.getTStamp()]

    return keys


def node_key_func(node) -> List:
    """
    Approximate sorting order for all nodes in a Footprint, following
    the logic in PCB_IO_KICAD_SEXPR::format( const FOOTPRINT* ...)
    """

    # This is all graphics, but not the text
    if isinstance(node, (Arc, Circle, Line, Polygon, CompoundPolygon,
                         PolygonArc, Rect)):
        return [100] + round_numbers_in_key_func(graphic_key_func(node))
    elif isinstance(node, Text):
        return [200] + round_numbers_in_key_func(text_key_func(node))
    elif isinstance(node, Pad):
        return [300] + round_numbers_in_key_func(pad_key_func(node))
    elif isinstance(node, Zone):
        return [400] + round_numbers_in_key_func(zone_key_func(node))
    elif isinstance(node, Group):
        return [600] + round_numbers_in_key_func(group_key_func(node))
    elif isinstance(node, EmbeddedFonts):
        return [1000]
    elif isinstance(node, Model):
        # Models right at the end
        return [1100]

    raise ValueError(f"Node ordering not defined: {node}")


# This function rounds all floating numbers inside a nested list
# in order to avoid issues with wrong sorting order in serialized output.
#
# When KiCad sees values like:
#     [ 1E-15, 2]
#     [-1E-15, 3]
# it would serialize them first and then sort them into the following order:
#     (0, 2)
#     (0, 3)
# On the other hand, without this function, Python would sort them as:
#     [-1E-15, 3]
#     [ 1E-15, 2]
# which would lead to wrong serialization:
#     (0, 3)
#     (0, 2)
# So we have to make sure that all numbers get rounded first
# before being fed into a sort function.
def round_numbers_in_key_func(keys: List) -> List:
    for i, key in enumerate(keys):
        if isinstance(key, List):
            keys[i] = round_numbers_in_key_func(key)
        elif isinstance(key, float):
            keys[i] = float(formatFloat(key))
    return keys


class KicadFileHandler(FileHandler):
    r"""Implementation of the FileHandler for .kicad_mod files

    :param kicad_mod:
        Main object representing the footprint
    :type kicad_mod: ``KicadModTree.Footprint``

    :Example:

    >>> from KicadModTree import *
    >>> kicad_mod = Footprint("example_footprint", FootprintType.THT)
    >>> file_handler = KicadFileHandler(kicad_mod)
    >>> file_handler.writeFile('example_footprint.kicad_mod')
    """

    # This is the version of the .kicad_mod format that this serialiser produces
    # It is used to set the version field in the .kicad_mod file
    #
    # The version number is a date in the format YYYYMMDD and corresponds to the
    # version in the pcb_io_kicad_sexpr.h file for a stable release of KiCad.
    FORMAT_VERSION: int = 20241229

    # The name of the generator (this is put in the .kicad_mod file)
    #
    # In theory, this could also encode which sub-generator was used, but for now
    # this is just a fixed string, same as for KiCad v7 generators.
    GENERATOR_NAME: str = 'kicad-footprint-generator'

    kicad_mod: Footprint

    angle_tolerance_deg: float = 1e-9  # degrees
    size_tolerance_mm: float = 1e-9  # mm

    def __init__(self, kicad_mod: Footprint):
        super().__init__()
        self.kicad_mod = kicad_mod

    def serialize(self):
        r"""Get a valid string representation of the footprint in the .kicad_mod format

        :Example:

        >>> from KicadModTree import *
        >>> kicad_mod = Footprint("example_footprint", FootprintType.THT)
        >>> file_handler = KicadFileHandler(kicad_mod)
        >>> print(file_handler.serialize())
        """

        sexpr = [
            SexprSerializer.Symbol('footprint'), self.kicad_mod.name,
            [SexprSerializer.Symbol('version'), self.FORMAT_VERSION],
            [SexprSerializer.Symbol('generator'), self.GENERATOR_NAME],
            [SexprSerializer.Symbol('layer'), 'F.Cu'],
        ]

        if self.kicad_mod.hasValidTStamp():
            sexpr.append(self._serialize_TStamp(self.kicad_mod))

        if self.kicad_mod.description:
            sexpr.append([SexprSerializer.Symbol('descr'), self.kicad_mod.description])

        if self.kicad_mod.tags:
            sexpr.append([SexprSerializer.Symbol('tags'), " ".join(self.kicad_mod.tags)])

        if self.kicad_mod.maskMargin:
            sexpr.append([SexprSerializer.Symbol('solder_mask_margin'),
                          self.kicad_mod.maskMargin])

        if self.kicad_mod.pasteMargin:
            sexpr.append([SexprSerializer.Symbol('solder_paste_margin'),
                          self.kicad_mod.pasteMargin])

        if self.kicad_mod.pasteMarginRatio:
            sexpr.append([SexprSerializer.Symbol('solder_paste_ratio'),
                          self.kicad_mod.pasteMarginRatio])

        sexpr.extend(self._serializeTree())

        return str(SexprSerializer(sexpr)) + "\n"

    def _serialize_attributes(self):
        attributes = []

        footprint_type_str = self._typeToAttributeSymbol(self.kicad_mod.footprintType)

        # If not unspecified, add the attribute
        if (footprint_type_str is not None):
            attributes.append(footprint_type_str)

        if self.kicad_mod.not_in_schematic:
            attributes.append(SexprSerializer.Symbol('board_only'))

        if self.kicad_mod.excludeFromPositionFiles:
            attributes.append(SexprSerializer.Symbol('exclude_from_pos_files'))

        if self.kicad_mod.excludeFromBOM:
            attributes.append(SexprSerializer.Symbol('exclude_from_bom'))

        if self.kicad_mod.allow_soldermask_bridges:
            attributes.append(SexprSerializer.Symbol('allow_soldermask_bridges'))

        if self.kicad_mod.allow_missing_courtyard:
            attributes.append(SexprSerializer.Symbol('allow_missing_courtyard'))

        if self.kicad_mod.dnp:
            attributes.append(SexprSerializer.Symbol('dnp'))

        return attributes

    def _serializeTree(self):
        nodes = self.kicad_mod.serialize()

        ordered_nodes = []
        property_nodes = []

        for single_node in nodes:

            if isinstance(single_node, Property):
                property_nodes.append(single_node)

            # add all the 'base' nodes that we know how to serialise
            elif isinstance(single_node, (Arc, Circle, Line, Pad,
                                          Polygon, CompoundPolygon,
                                          PolygonArc, Rect, Group, Text, Zone,
                                          EmbeddedFonts, Model)):
                ordered_nodes.append(single_node)

        sexpr = []

        # serialize initial property nodes
        for property_node in property_nodes:
            sexpr.append(self._serialize_Property(property_node))

        if self.kicad_mod.clearance is not None:
            sexpr.append([SexprSerializer.Symbol('clearance'), self.kicad_mod.clearance])

        sexpr += self._serialize_ZoneConnection(self.kicad_mod.zone_connection)

        # Kicad 8 puts the attributes at the end of the properties
        attributes = self._serialize_attributes()
        # There might be no attributes
        if len(attributes) > 0:
            sexpr.append([SexprSerializer.Symbol('attr')] + attributes)

        # serialize the rest of the nodes

        # reorder to the KiCad native order
        ordered_nodes.sort(key=node_key_func)

        # render base nodes
        for node in ordered_nodes:
            subnode_sexpr = self._callSerialize(node)
            if subnode_sexpr is not None:
                # allow conditionally no additional results to be added,
                # for nodes that may or may not use solely virtual nodes depending on their configuration.
                sexpr.append(subnode_sexpr)

        return sexpr

    def _typeToAttributeSymbol(self, footprintType: FootprintType) -> SexprSerializer.Symbol | None:
        """
        Convert the footprint type to the corresponding attribute string
        in the .kicad_mod format s-expr attr node
        """
        attr_name = {
            FootprintType.UNSPECIFIED: None,
            FootprintType.SMD: 'smd',
            FootprintType.THT: 'through_hole',
        }[footprintType]

        if attr_name is None:
            return None

        return SexprSerializer.Symbol(attr_name)

    def _callSerialize(self, node):
        '''
        call the corresponding method to serialize the node
        '''
        method_type = node.__class__.__name__
        method_name = "_serialize_{0}".format(method_type)

        if hasattr(self, method_name):
            return getattr(self, method_name)(node)
        else:
            exception_string = "{name} (node) not found, cannot serialize the node of type {type}"
            raise NotImplementedError(exception_string.format(name=method_name, type=method_type))

    def _serialize_Stroke(self, node):
        width = _get_layer_width(node.layer, node.width)

        if hasattr(node, 'style'):
            stype = {
                LineStyle.SOLID: "solid",
                LineStyle.DASH: "dash",
                LineStyle.DOT: "dot",
                LineStyle.DASH_DOT: "dash_dot",
                LineStyle.DASH_DOT_DOT: "dash_dot_dot",
            }[node.style]
        else:
            stype = 'solid'

        return [
            [SexprSerializer.Symbol('width'), width],
            [SexprSerializer.Symbol('type'), SexprSerializer.Symbol(stype)],
        ]

    def _serialize_Fill(self, node):

        fill = False
        if hasattr(node, 'fill'):
            if isinstance(node.fill, bool):
                fill = node.fill
            else:
                fill = node.fill == "solid"

        return self._serialise_Boolean('fill', fill)

    def _serialize_ArcPoints(self, node: Arc):
        start_pos = node.getRealPosition(node.getStartPoint())
        end_pos = node.getRealPosition(node.getEndPoint())
        mid_pos = node.getRealPosition(node.getMidPoint())
        # Match KiCad normalisation of negative arc angles.
        # Swap start and end for negative angles to overcome a bug in KiCAD v6 and some v7 versions.
        if node.angle < 0:
            start_pos, end_pos = end_pos, start_pos
        return [
            [SexprSerializer.Symbol('start'), start_pos.x, start_pos.y],
            [SexprSerializer.Symbol('mid'), mid_pos.x, mid_pos.y],
            [SexprSerializer.Symbol('end'), end_pos.x, end_pos.y],
        ]

    def _serialize_PolygonArc(self, node):
        sexpr = [SexprSerializer.Symbol('arc')]
        sexpr += self._serialize_ArcPoints(node)

        return sexpr

    def _serialize_Arc(self, node: Arc):
        sexpr = [SexprSerializer.Symbol('fp_arc')]
        sexpr += self._serialize_ArcPoints(node)
        sexpr += [
                  [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
                  [SexprSerializer.Symbol('layer'), node.layer],
                 ]  # NOQA
        if node.hasValidTStamp():
            sexpr.append(self._serialize_TStamp(node))

        return sexpr

    def _serialize_CirclePoints(self, node: Circle):
        center_pos = node.getRealPosition(node.center_pos)
        end_pos = node.getRealPosition(node.center_pos + (node.radius, 0))

        return [
            [SexprSerializer.Symbol('center'), center_pos.x, center_pos.y],
            [SexprSerializer.Symbol('end'), end_pos.x, end_pos.y]
        ]

    def _serialize_Circle(self, node: Circle):
        sexpr = [SexprSerializer.Symbol('fp_circle')]
        sexpr += self._serialize_CirclePoints(node)
        sexpr += [
            [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
        ]
        if hasattr(node, 'fill'):
            sexpr += [self._serialize_Fill(node)]
        sexpr += [
            [SexprSerializer.Symbol('layer'), node.layer],
        ]

        if node.hasValidTStamp():
            sexpr.append(self._serialize_TStamp(node))

        return sexpr

    def _serialize_Rect(self, node: Rect):
        sexpr: list = [SexprSerializer.Symbol('fp_rect')]
        sexpr += self._serialize_RectPoints(node)
        sexpr += [
                  [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
                 ]  # NOQA
        if hasattr(node, 'fill'):
            sexpr += [self._serialize_Fill(node)]
        sexpr += [
            [SexprSerializer.Symbol('layer'), node.layer],
        ]
        if node.hasValidTStamp():
            sexpr.append(self._serialize_TStamp(node))

        return sexpr

    def _serialise_Layers(self, node):
        layers = sorted(node.layers, key=layer_key_func)
        return [SexprSerializer.Symbol('layers')] + layers

    def _serialize_LinePoints(self, node: Line | Rect):
        start_pos = node.getRealPosition(node.start_pos)
        end_pos = node.getRealPosition(node.end_pos)
        return [
            [SexprSerializer.Symbol('start'), start_pos.x, start_pos.y],
            [SexprSerializer.Symbol('end'), end_pos.x, end_pos.y]
        ]

    def _serialize_RectPoints(self, node: Rect):
        # identical for current kicad format
        return self._serialize_LinePoints(node)

    def _serialize_Line(self, node: Line):
        sexpr = [SexprSerializer.Symbol('fp_line')]
        sexpr += self._serialize_LinePoints(node)
        sexpr += [
            [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
            [SexprSerializer.Symbol('layer'), node.layer],
        ]
        if node.hasValidTStamp():
            sexpr.append(self._serialize_TStamp(node))

        return sexpr

    def _serialise_Boolean(self, name: str, value: bool):
        return [SexprSerializer.Symbol(name), SexprSerializer.Symbol('yes' if value else 'no')]

    def _serialize_TextBaseNode(self, node):
        """Serialise fp_text and property field bodies
        """
        sexpr = [node.text]

        position, rotation = node.getRealPosition(node.at, node.rotation)
        if rotation is None:
            rotation = 0

        # KiCad 8 always writes the 0 rotation
        sexpr.append([SexprSerializer.Symbol('at'),
                      position.x, position.y, rotation])

        sexpr.append([SexprSerializer.Symbol('layer'), node.layer])
        if node.hide:
            sexpr.append(self._serialise_Boolean('hide', True))

        effects = [
            SexprSerializer.Symbol('effects'),
            [SexprSerializer.Symbol('font'),
             [SexprSerializer.Symbol('size'), node.size.x, node.size.y],
             [SexprSerializer.Symbol('thickness'), node.thickness]]]

        justify = []

        if node.mirror:
            justify.append(SexprSerializer.Symbol('mirror'))

        if node.justify:
            justify_as_list = [node.justify] if not isinstance(node.justify, list) else node.justify
            justify += [SexprSerializer.Symbol(j) for j in justify_as_list]

        if (len(justify)):
            effects.append([SexprSerializer.Symbol('justify')] + justify)

        sexpr.append(effects)

        if node.hasValidTStamp():
            sexpr.append(self._serialize_TStamp(node))

        return sexpr

    def _serialize_Text(self, node: Text):
        """Serialise a normal text node
        """
        sexpr = [
            # would be gr_text in a PCB
            SexprSerializer.Symbol('fp_text'),
            SexprSerializer.Symbol('user')
        ]
        sexpr += self._serialize_TextBaseNode(node)
        return sexpr

    def _serialize_Property(self, node: Property):
        """Serialise a property node
        """
        sexpr = [
            SexprSerializer.Symbol('property'),
            node.name,
        ]
        sexpr += self._serialize_TextBaseNode(node)
        return sexpr

    def _serialize_Model(self, node: Model):
        sexpr = [
            SexprSerializer.Symbol('model'), node.filename,
            [
                SexprSerializer.Symbol('offset'),
                [SexprSerializer.Symbol('xyz'), node.at.x, node.at.y, node.at.z]
            ],
            [
                SexprSerializer.Symbol('scale'),
                [SexprSerializer.Symbol('xyz'), node.scale.x, node.scale.y, node.scale.z]
            ],
            [
                SexprSerializer.Symbol('rotate'),
                [SexprSerializer.Symbol('xyz'), node.rotate.x, node.rotate.y, node.rotate.z]
            ],
        ]  # NOQA

        return sexpr

    def _serialize_CustomPadPrimitives(self, pad: Pad):
        all_primitives = []
        for p in pad.primitives:
            all_primitives.extend(p.serialize())

        grouped_nodes = {}

        for single_node in all_primitives:
            node_type = single_node.__class__.__name__

            current_nodes = grouped_nodes.get(node_type, [])
            current_nodes.append(single_node)

            grouped_nodes[node_type] = current_nodes

        sexpr_primitives = []

        for key, value in sorted(grouped_nodes.items()):
            # check if key is a base node, except Model
            if key not in {'Arc', 'Circle', 'Line', 'Pad', 'Polygon', 'Text'}:
                continue

            # render base nodes
            for p in value:

                filled = False
                if isinstance(p, Polygon):

                    sp = [
                        SexprSerializer.Symbol("gr_poly"),
                        self._serialize_PolygonPoints(p),
                    ]
                    filled = p.fill

                elif isinstance(p, Line):
                    sp = [SexprSerializer.Symbol('gr_line')] + self._serialize_LinePoints(p)
                elif isinstance(p, Circle):
                    sp = [SexprSerializer.Symbol('gr_circle')] + self._serialize_CirclePoints(p)
                    filled = p.fill
                elif isinstance(p, Arc):
                    sp = [SexprSerializer.Symbol('gr_arc')] + self._serialize_ArcPoints(p)
                else:
                    raise TypeError('Unsuported type of primitive for custom pad.')
                sp.append([SexprSerializer.Symbol('width'),
                           DEFAULT_WIDTH_POLYGON_PAD if p.width is None else p.width])

                if filled:
                    sp.append([SexprSerializer.Symbol('fill'), SexprSerializer.Symbol('yes')])

                sexpr_primitives.append(sp)
                # sexpr_primitives.append(SexprSerializer.NEW_LINE)

        return sexpr_primitives

    def _serialize_PadFabProperty(self, node: Pad) -> SexprSerializer.Symbol:
        mapping = {
            Pad.FabProperty.BGA: 'pad_prop_bga',
            Pad.FabProperty.FIDUCIAL_GLOBAL: 'pad_prop_pad_prop_heatsink',
            Pad.FabProperty.FIDUCIAL_LOCAL: 'pad_prop_fiducial_loc',
            Pad.FabProperty.HEATSINK: 'pad_prop_heatsink',
            Pad.FabProperty.TESTPOINT: 'pad_prop_testpoint',
            Pad.FabProperty.CASTELLATED: 'pad_prop_castellated',
        }
        return SexprSerializer.Symbol(mapping[node.fab_property])

    def _serialize_ZoneConnection(self, zone_connection: Pad.ZoneConnection):
        # Inherited zone connection is implicit in the s-exp by a missing zone_connection node
        if zone_connection == Pad.ZoneConnection.INHERIT:
            return []

        mapping = {
            Pad.ZoneConnection.NONE: 0,
            Pad.ZoneConnection.THERMAL_RELIEF: 1,
            Pad.ZoneConnection.SOLID: 2,
        }

        return [[SexprSerializer.Symbol("zone_connect"), mapping[zone_connection]]]

    @staticmethod
    def _serializeChamferCorner(name: str, corner: CornerSelection):
        lst = []
        if (corner.top_left):
            lst += [SexprSerializer.Symbol("top_left")]

        if corner.top_right:
            lst += [SexprSerializer.Symbol("top_right")]

        if corner.bottom_left:
            lst += [SexprSerializer.Symbol("bottom_left")]

        if corner.bottom_right:
            lst += [SexprSerializer.Symbol("bottom_right")]

        if len(lst) > 0:
            return [SexprSerializer.Symbol(name)] + lst
        else:
            return []

    def _serialize_Pad(self, node: Pad):

        def _map_shape_type(shape: str) -> SexprSerializer.Symbol:
            mapping = {
                Pad.SHAPE_CIRCLE: 'circle',
                Pad.SHAPE_RECT: 'rect',
                Pad.SHAPE_OVAL: 'oval',
                Pad.SHAPE_TRAPEZE: 'trapezoid',
                Pad.SHAPE_ROUNDRECT: 'roundrect',
                Pad.SHAPE_CUSTOM: 'custom',
            }
            return SexprSerializer.Symbol(mapping[shape])

        def _map_pad_type(pad_type: str) -> SexprSerializer.Symbol:
            mapping = {
                Pad.TYPE_THT: 'thru_hole',
                Pad.TYPE_SMT: 'smd',
                Pad.TYPE_NPTH: 'np_thru_hole',
                Pad.TYPE_CONNECT: 'connect',
            }
            return SexprSerializer.Symbol(mapping[pad_type])

        def _serialise_thermalBridgeAngle(pad: Pad):
            # KiCad (9, at least) doesn't output this in the s-expr in it's slightly esoteric default state
            # But Pads do always have a valid angle.

            tba_default = (
                45
                if pad.shape == Pad.SHAPE_CIRCLE
                or (
                    pad.shape == Pad.SHAPE_CUSTOM
                    and pad.anchor_shape == Pad.SHAPE_CIRCLE
                )
                else 90
            )

            if abs(pad.thermal_bridge_angle - tba_default):
                return [
                    [
                        SexprSerializer.Symbol("thermal_bridge_angle"),
                        pad.thermal_bridge_angle,
                    ]
                ]

            return []

        shape = node.shape

        # Round rects decay to rectangles if the radius ratio is 0
        if shape == Pad.SHAPE_ROUNDRECT:
            if node.radius_ratio == 0:
                shape = Pad.SHAPE_RECT

        sexpr = [
            SexprSerializer.Symbol('pad'),
            str(node.number),
            _map_pad_type(node.type),
            _map_shape_type(shape)
        ]

        position, rotation = node.getRealPosition(node.at, node.rotation)
        if not rotation % 360 == 0:
            sexpr.append([SexprSerializer.Symbol('at'), position.x, position.y, rotation])
        else:
            sexpr.append([SexprSerializer.Symbol('at'), position.x, position.y])

        sexpr.append([SexprSerializer.Symbol('size'), node.size.x, node.size.y])

        if node.type in [Pad.TYPE_THT, Pad.TYPE_NPTH] and (node.drill is not None):

            if abs(node.drill.x - node.drill.y) < self.size_tolerance_mm:
                drill_config = [SexprSerializer.Symbol('drill'), node.drill.x]
            else:
                drill_config = [SexprSerializer.Symbol('drill'),
                                SexprSerializer.Symbol('oval'),
                                node.drill.x, node.drill.y]

            # append offset only if necessary
            if ((node.offset is not None)
                    and ((abs(node.offset.x) > self.size_tolerance_mm)
                         or (abs(node.offset.y) > self.size_tolerance_mm))):
                drill_config.append([SexprSerializer.Symbol('offset'), node.offset.x,  node.offset.y])

            sexpr.append(drill_config)

        # As of format 20231231, 'property' contains only the fab value.
        if node.fab_property is not None:
            property_value = self._serialize_PadFabProperty(node)
            sexpr.append([SexprSerializer.Symbol('property'), property_value])

        sexpr.append(self._serialise_Layers(node))

        if node.type == Pad.TYPE_THT:
            unconn_mode = node.unconnected_layer_mode
            remove_unconn = unconn_mode != Pad.UnconnectedLayerMode.KEEP_ALL

            sexpr.append(self._serialise_Boolean("remove_unused_layers", remove_unconn))

            if remove_unconn:
                sexpr.append(
                    self._serialise_Boolean(
                        "keep_end_layers",
                        unconn_mode
                        == Pad.UnconnectedLayerMode.REMOVE_EXCEPT_START_AND_END,
                    )
                )

        if shape == Pad.SHAPE_ROUNDRECT:
            sexpr.append([SexprSerializer.Symbol('roundrect_rratio'), node.radius_ratio])

            if node.chamfer_ratio is not None and node.chamfer_corners.isAnySelected():
                sexpr.append([SexprSerializer.Symbol('chamfer_ratio'), node.chamfer_ratio])

                sval = self._serializeChamferCorner("chamfer", node.chamfer_corners)
                if (sval is not None) and sval:
                    sexpr.append(sval)

        if shape == Pad.SHAPE_CUSTOM:
            # gr_line, gr_arc, gr_circle or gr_poly
            sexpr.append(
                [SexprSerializer.Symbol('options'),
                    [SexprSerializer.Symbol('clearance'), SexprSerializer.Symbol(node.shape_in_zone)],
                    [SexprSerializer.Symbol('anchor'), SexprSerializer.Symbol(node.anchor_shape)]])

            sexpr_primitives = self._serialize_CustomPadPrimitives(node)

            sexpr.append([SexprSerializer.Symbol('primitives')] + sexpr_primitives)

        if node.hasValidTStamp():
            sexpr.append(self._serialize_TStamp(node))

        if node.tuning_properties is not None:
            if node.tuning_properties.die_length > self.size_tolerance_mm:
                sexpr.append([SexprSerializer.Symbol('die_length'),
                              node.tuning_properties.die_length])

        if node.solder_paste_margin_ratio != 0 or node.solder_mask_margin != 0 or node.solder_paste_margin != 0:
            if (node.solder_mask_margin is not None) and node.solder_mask_margin != 0:
                sexpr.append([SexprSerializer.Symbol('solder_mask_margin'),
                              node.solder_mask_margin])
            if (node.solder_paste_margin_ratio is not None) and node.solder_paste_margin_ratio != 0:
                sexpr.append([SexprSerializer.Symbol('solder_paste_margin_ratio'),
                              node.solder_paste_margin_ratio])
            if (node.solder_paste_margin is not None) and node.solder_paste_margin != 0:
                sexpr.append([SexprSerializer.Symbol('solder_paste_margin'),
                              node.solder_paste_margin])

        sexpr += self._serialize_ZoneConnection(node.zone_connection)

        if node.clearance is not None and abs(node.clearance) > self.size_tolerance_mm:
            sexpr.append([SexprSerializer.Symbol('clearance'), node.clearance])

        if node.thermal_bridge_width is not None and node.thermal_bridge_width > self.size_tolerance_mm:
            sexpr.append([SexprSerializer.Symbol('thermal_bridge_width'), node.thermal_bridge_width])

        sexpr += _serialise_thermalBridgeAngle(node)

        if node.thermal_gap is not None and abs(node.thermal_gap) > self.size_tolerance_mm:
            sexpr.append([SexprSerializer.Symbol('thermal_gap'), node.thermal_gap])

        return sexpr

    def _serialize_PolygonPoints(self, node: PolygonPoints):
        node_points = [SexprSerializer.Symbol('pts')]

        for n in node.nodes:
            n_pos = node.getRealPosition(n)
            node_points.append([SexprSerializer.Symbol('xy'), n_pos.x, n_pos.y])

        return node_points

    def _serialize_Polygon(self, node: Polygon):
        node_points = self._serialize_PolygonPoints(node)

        sexpr = [SexprSerializer.Symbol('fp_poly'),
                 node_points,
                 [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
                 self._serialize_Fill(node),
                 [SexprSerializer.Symbol('layer'), node.layer],
                ]  # NOQA

        if node.hasValidTStamp():
            sexpr += [
                self._serialize_TStamp(node),
            ]

        return sexpr

    def _serialize_CompoundPolygon(self, node: CompoundPolygon):

        def _serialize_PolygonPointsSegment(polygonpoints: PolygonPoints):
            node_points = []

            for n in polygonpoints:
                n_pos = node.getRealPosition(n)
                node_points.append([SexprSerializer.Symbol('xy'), n_pos.x, n_pos.y])

            return node_points

        if node.isSerializedAsFPPoly():

            node_points_sexpr = [SexprSerializer.Symbol('pts')]

            for geom in node.polygon_geometries:
                if isinstance(geom, PolygonPoints):
                    node_points_sexpr.extend(_serialize_PolygonPointsSegment(polygonpoints=geom))
                elif isinstance(geom, PolygonArc):
                    node_points_sexpr.append(
                        self._serialize_PolygonArc(geom))
                else:
                    node_points_sexpr.append(
                        self._callSerialize(geom))
            sexpr = [
                SexprSerializer.Symbol("fp_poly"),
                node_points_sexpr,
                [SexprSerializer.Symbol("stroke")] + self._serialize_Stroke(node),
                self._serialize_Fill(node),
                [SexprSerializer.Symbol("layer"), SexprSerializer.Symbol(node.layer)],
            ]
            if node.hasValidTStamp():
                sexpr.append(self._serialize_TStamp(node))

            return sexpr

        else:  # kicad 7 does not (yet) support open polygons or polylines, therefore convert to virtual nodes
            # for all primitives (see getVirtualChilds, serialize_get_virtual_nodes )
            sexpr = []  # no serialization here, see childs
            return None

    def _serialize_Group(self, node: Group):
        sexpr: list = []
        sexpr.append(SexprSerializer.Symbol('group'))
        sexpr.append(f'{node.getGroupName()}')
        if node.hasValidTStamp():
            tstamp_uuid = str(node.getTStamp())
        else:
            if node.hasValidSeedForTStamp():
                node.getTStampCls().reCalcTStamp()
                if node.hasValidTStamp():
                    tstamp_uuid = str(node.getTStamp())
                else:
                    raise ValueError(
                        "TStamp for Group must be valid once serialization happpens")
            else:
                raise ValueError(
                    "TStamp Seed for Group must be valid once serialization happpens")

        sexpr.append([SexprSerializer.Symbol('id'), SexprSerializer.Symbol(tstamp_uuid)])
        grp_members = [SexprSerializer.Symbol('members')]
        grp_member_ids = []
        for gid in node.getSortedGroupMemberTStamps():
            grp_member_ids.append(gid)
        grp_member_ids.sort()  # sort IDs, this is what KiCad does. ToDo: check order
        for gid in grp_member_ids:
            grp_members.append(SexprSerializer.Symbol(gid))
        sexpr.append(grp_members)

        return sexpr

    def _serialize_Zone(self, node: Zone):

        def _allow_or_not(allow: bool) -> SexprSerializer.Symbol:
            return SexprSerializer.Symbol('allowed') if allow else SexprSerializer.Symbol('not_allowed')

        def _serialise_Keepout(keepouts: Keepouts):

            sexpr = [SexprSerializer.Symbol('keepout')]

            def add_keepout(keepout_property, sexp_keyword: str) -> None:
                sexpr.append([
                    SexprSerializer.Symbol(sexp_keyword),
                    _allow_or_not(keepout_property == Keepouts.ALLOW)])

            add_keepout(keepouts.tracks, 'tracks')
            add_keepout(keepouts.vias, 'vias')
            add_keepout(keepouts.pads, 'pads')
            add_keepout(keepouts.copperpour, 'copperpour')
            add_keepout(keepouts.footprints, 'footprints')

            return sexpr

        def _serialise_Placement():
            """
            For footprint purposes, placement is always disabled
            """
            sexpr = [
                SexprSerializer.Symbol("placement"),
                self._serialise_Boolean("enabled", False),
                [SexprSerializer.Symbol("sheetname"), ""],
            ]

            return sexpr

        def _serialize_Hatch(node):
            return [
                SexprSerializer.Symbol('hatch'),
                SexprSerializer.Symbol(node.style),
                node.pitch,
            ]

        def _serialize_ConnectPads(node):
            sexpr = [SexprSerializer.Symbol('connect_pads')]
            connect_type = node.type
            if connect_type is not PadConnection.THERMAL_RELIEF:
                sexpr.append(SexprSerializer.Symbol(connect_type))

            sexpr.append([SexprSerializer.Symbol('clearance'), node.clearance])
            return sexpr

        def _serialise_ZoneFill(node: Zone):
            sexpr = [SexprSerializer.Symbol('fill')]

            # we do have a fill
            if node.fill != ZoneFill.FILL_NONE:
                sexpr.append(SexprSerializer.Symbol('yes'))

            def node_if_not_none(property: Optional[str], keyword: str) -> list:
                if property is None:
                    return []
                return [
                    [SexprSerializer.Symbol(keyword), SexprSerializer.Symbol(property)]
                ]

            # soild is encoded as no mode
            if node.fill not in [ZoneFill.FILL_NONE, ZoneFill.FILL_SOLID]:
                sexpr += [
                    [SexprSerializer.Symbol('mode'), node.fill],
                ]

            # Thermal gap and bridge with aren't optional
            sexpr += [
                [SexprSerializer.Symbol('thermal_gap'), node.thermal_gap],
                [SexprSerializer.Symbol('thermal_bridge_width'), node.thermal_bridge_width],
            ]

            if node.smoothing is not None:
                sexpr += [
                    [
                        SexprSerializer.Symbol('smoothing'),
                        SexprSerializer.Symbol(node.smoothing),
                    ]
                ]

                if node.smoothing_radius > 0:
                    sexpr += [
                        [
                            SexprSerializer.Symbol('radius'),
                            node.smoothing_radius
                        ],
                    ]

            # KiCad only outputs the island removal mode if it's not the 'remove' default
            if (
                node.island_removal_mode is not None
                and node.island_removal_mode != ZoneFill.ISLAND_REMOVAL_REMOVE
            ):
                # Look up the encoding
                island_removal_mode = {
                    ZoneFill.ISLAND_REMOVAL_REMOVE: 0,
                    ZoneFill.ISLAND_REMOVAL_FILL: 1,
                    ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA: 2,
                }[node.island_removal_mode]

                sexpr += [[SexprSerializer.Symbol('island_removal_mode'), island_removal_mode]]

                # only valid in mode 2
                if node.island_removal_mode == 'minimum_area':
                    sexpr += [[SexprSerializer.Symbol('island_area_min'), node.island_area_min]]

            sexpr += node_if_not_none(node.hatch_thickness, 'hatch_thickness')
            sexpr += node_if_not_none(node.hatch_gap, 'hatch_gap')
            sexpr += node_if_not_none(node.hatch_orientation,
                                      'hatch_orientation')
            sexpr += node_if_not_none(node.hatch_smoothing_level,
                                      'hatch_smoothing_level')
            sexpr += node_if_not_none(node.hatch_smoothing_value,
                                      'hatch_smoothing_value')
            sexpr += node_if_not_none(node.hatch_border_algorithm,
                                      'hatch_border_algorithm')
            sexpr += node_if_not_none(node.hatch_min_hole_area,
                                      'hatch_min_hole_area')
            return sexpr

        sexpr = [
            SexprSerializer.Symbol('zone'),
            [SexprSerializer.Symbol('net'), node.net],
            [SexprSerializer.Symbol('net_name'), node.net_name],
            self._serialise_Layers(node),
            [SexprSerializer.Symbol('name'), node.name],
            _serialize_Hatch(node.hatch)
        ]

        if node.hasValidTStamp():
            sexpr += [
                self._serialize_TStamp(node),
            ]

        # Optional node
        if node.priority is not None:
            sexpr += [
                [SexprSerializer.Symbol('priority'), node.priority],
            ]

        sexpr += [
            _serialize_ConnectPads(node.connect_pads),
            # technically optional, but we can just always put it in
            [SexprSerializer.Symbol('min_thickness'), node.min_thickness],
            self._serialise_Boolean('filled_areas_thickness', node.filled_areas_thickness),
        ]

        is_rule_area = node.keepouts is not None

        # Rule areas always seem to output keepout and placement
        if is_rule_area:
            sexpr += [
                _serialise_Keepout(node.keepouts),
                _serialise_Placement(),
            ]

        sexpr += [
            _serialise_ZoneFill(node.fill),
            [
                SexprSerializer.Symbol('polygon'),
                self._serialize_PolygonPoints(node)
            ]
        ]

        return sexpr

    def _serialize_TStamp(self, node: Node):
        sexpr = []
        if hasattr(node, 'getTStamp') and hasattr(node, 'hasValidTStamp'):
            if (node.hasValidTStamp()):
                tstmp = node.getTStamp()
                sexpr.append(SexprSerializer.Symbol('tstamp'))
                sexpr.append(SexprSerializer.Symbol(str(tstmp)))
                return sexpr
        return [""]

    def _serialize_EmbeddedFonts(self, node: EmbeddedFonts):
        if not node.enabled:
            return self._serialise_Boolean('embedded_fonts', False)

        raise NotImplementedError("'enabled' embedded fonts are not yet supported")


class KicadModLibrary(abc.ABC):
    """
    Abstract base class for serialising a footprint to a library
    (e.g. a .kicad_mod file, a .pretty directory, or a nickname in an
    IPC library).
    """

    @abc.abstractmethod
    def save(self, fp: Footprint):
        pass


class KicadPrettyLibrary(KicadModLibrary):
    """
    Implementation of the KicadModLibrary for .pretty directories
    (i.e. direct file write)
    """

    def __init__(self, lib_name: str, output_dir: Path | None):

        if not lib_name.endswith(".pretty"):
            lib_name += ".pretty"

        # If the environment variable is set, it will be the output
        # prefix to any non-absolute paths.
        #
        # This is a bit of a hack to allow this to work with
        # generate.sh type generators (which don't allow the output
        # dir to be set, ans have no unified interface)
        #
        # The correct thing to do is inject this path properly, but
        # that requires all the generators to be updated to be
        # fully-Python.
        import os
        env_var = os.getenv("KICAD_FP_GENERATOR_OUTPUT_DIR")

        # In these cases, apply the prefix
        if env_var:
            if not output_dir:
                output_dir = Path(env_var)
            elif not output_dir.is_absolute():
                output_dir = Path(env_var) / output_dir

        # No environment variable, or given path
        # Legacy behaviour, just use the current working directory
        if not output_dir:
            output_dir = Path.cwd()

        self.path = output_dir / lib_name

    def save(self, fp: Footprint):

        self.path.mkdir(parents=True, exist_ok=True)

        # Delegate to the s-expression serialiser
        file_handler = KicadFileHandler(fp)
        file_handler.writeFile(self.path / (fp.name + ".kicad_mod"))
