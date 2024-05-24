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

import re
from typing import Optional

from KicadModTree.FileHandler import FileHandler
from KicadModTree.util.kicad_util import SexprSerializer
from KicadModTree.nodes.base.Pad import Pad  # TODO: why .KicadModTree is not enough?
from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.base.Circle import Circle
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Polygon import Polygon
from KicadModTree.nodes.Footprint import Footprint, FootprintType
from KicadModTree.nodes.base.Zone import PadConnection, ZoneFill, Keepouts


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
    Get the KiCad sorting key for a layer name
    """

    layer_map = {
        "F.Cu": 0,
        "B.Cu": 31,
        "B.Adhes": 32,
        "F.Adhes": 33,
        "B.Paste": 34,
        "F.Paste": 35,
        "B.Silk": 36,
        "F.Silk": 37,
        "B.Mask": 38,
        "F.MasK": 39,
        "Dwgs.User": 40,
        "Cmts.User": 41,
        "Eco1.User": 42,
        "Eco2.User": 43,
        "Edge.Cuts": 44,
        "Margin": 45,
        "B.CrtYd": 46,
        "F.CrtYd": 47,
        "B.Fab": 48,
        "F.Fab": 49,
    }

    try:
        return layer_map[layer]
    except KeyError:
        # inner layers
        if m := re.match(r'^In(\d+)\.$', layer):
            return int(m.group(1))
        # user layers
        if m := re.match(r'^User\.(\d)$', layer):
            return 49 + int(m.group(1))
    return 0


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
    FORMAT_VERSION: int = 20240108

    # The name of the generator (this is put in the .kicad_mod file)
    #
    # In theory, this could also encode which sub-generator was used, but for now
    # this is just a fixed string, same as for KiCad v7 generators.
    GENERATOR_NAME: str = 'kicad-footprint-generator'

    def __init__(self, kicad_mod: Footprint):
        FileHandler.__init__(self, kicad_mod)

    def serialize(self, **kwargs):
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

        return str(SexprSerializer(sexpr))

    def _serialize_attributes(self):
        attributes = []

        footprint_type_str = self._typeToAttributeSymbol(self.kicad_mod.footprintType)

        # If not unspecified, add the attribute
        if (footprint_type_str is not None):
            attributes.append(footprint_type_str)

        if self.kicad_mod.excludeFromPositionFiles:
            attributes.append(SexprSerializer.Symbol('exclude_from_pos_files'))

        if self.kicad_mod.excludeFromBOM:
            attributes.append(SexprSerializer.Symbol('exclude_from_bom'))

        if self.kicad_mod.allow_soldermask_bridges:
            attributes.append(SexprSerializer.Symbol('allow_soldermask_bridges'))

        return attributes

    def _serializeTree(self):
        nodes = self.kicad_mod.serialize()

        grouped_nodes = {}

        for single_node in nodes:
            node_type = single_node.__class__.__name__

            current_nodes = grouped_nodes.get(node_type, [])
            current_nodes.append(single_node)

            grouped_nodes[node_type] = current_nodes

        sexpr = []

        # serialize initial property nodes
        for property_node in grouped_nodes.get('Property', []):
            sexpr.append(self._serialize_Property(property_node))

        # Kicad 8 puts the attributes at the end of the properties

        attributes = self._serialize_attributes()
        # There might be no attributes
        if len(attributes) > 0:
            sexpr.append([SexprSerializer.Symbol('attr')] + attributes)

        # serialize the rest of the nodes

        for key, value in sorted(grouped_nodes.items()):
            # check if key is a base node, except Model
            if key not in {'Arc', 'Circle', 'Line', 'Pad', 'Polygon', 'Text', 'Zone'}:
                continue

            # render base nodes
            for node in value:
                sexpr.append(self._callSerialize(node))

        # serialize 3D Models at the end
        if grouped_nodes.get('Model'):
            for node in grouped_nodes.get('Model'):
                sexpr.append(self._serialize_Model(node))

        return sexpr

    def _typeToAttributeSymbol(self, footprintType: FootprintType) -> SexprSerializer.Symbol:
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

        return [
            [SexprSerializer.Symbol('width'), width],
            [SexprSerializer.Symbol('type'), SexprSerializer.Symbol('solid')],
        ]

    def _serialize_ArcPoints(self, node):
        start_pos = node.getRealPosition(node.getStartPoint())
        end_pos = node.getRealPosition(node.getEndPoint())
        mid_pos = node.getRealPosition(node.getMidPoint())
        # swap start and end for negative angles to overcome a bug in KiCAD v6 and some v7 versions
        if (node.angle < 0):
            start_pos, end_pos = end_pos, start_pos
        return [
            [SexprSerializer.Symbol('start'), start_pos.x, start_pos.y],
            [SexprSerializer.Symbol('mid'), mid_pos.x, mid_pos.y],
            [SexprSerializer.Symbol('end'), end_pos.x, end_pos.y],
        ]

    def _serialize_Arc(self, node):
        sexpr = [SexprSerializer.Symbol('fp_arc')]
        sexpr += self._serialize_ArcPoints(node)
        sexpr += [
                  [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
                  [SexprSerializer.Symbol('layer'), node.layer],
                 ]  # NOQA

        return sexpr

    def _serialize_CirclePoints(self, node):
        center_pos = node.getRealPosition(node.center_pos)
        end_pos = node.getRealPosition(node.center_pos + (node.radius, 0))

        return [
            [SexprSerializer.Symbol('center'), center_pos.x, center_pos.y],
            [SexprSerializer.Symbol('end'), end_pos.x, end_pos.y]
        ]

    def _serialize_Circle(self, node):
        sexpr = [SexprSerializer.Symbol('fp_circle')]
        sexpr += self._serialize_CirclePoints(node)
        sexpr += [
            [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
            [SexprSerializer.Symbol('layer'), node.layer],
        ]

        return sexpr

    def _serialise_Layers(self, node):
        layers = sorted(node.layers, key=layer_key_func)
        return [SexprSerializer.Symbol('layers')] + layers

    def _serialize_LinePoints(self, node):
        start_pos = node.getRealPosition(node.start_pos)
        end_pos = node.getRealPosition(node.end_pos)
        return [
            [SexprSerializer.Symbol('start'), start_pos.x, start_pos.y],
            [SexprSerializer.Symbol('end'), end_pos.x, end_pos.y]
        ]

    def _serialize_Line(self, node):
        sexpr = [SexprSerializer.Symbol('fp_line')]
        sexpr += self._serialize_LinePoints(node)
        sexpr += [
            [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
            [SexprSerializer.Symbol('layer'), node.layer],
        ]

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

        return sexpr

    def _serialize_Text(self, node):
        """Serialise a normal text node
        """
        sexpr = [
            # would be gr_text in a PCB
            SexprSerializer.Symbol('fp_text'),
            SexprSerializer.Symbol('user')
        ]
        sexpr += self._serialize_TextBaseNode(node)
        return sexpr

    def _serialize_Property(self, node):
        """Serialise a property node
        """
        sexpr = [
            SexprSerializer.Symbol('property'),
            node.name,
        ]
        sexpr += self._serialize_TextBaseNode(node)
        return sexpr

    def _serialize_Model(self, node):
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

    def _serialize_CustomPadPrimitives(self, pad):
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
                if isinstance(p, Polygon):
                    sp = [SexprSerializer.Symbol('gr_poly'),
                          self._serialize_PolygonPoints(p)
                         ]  # NOQA
                elif isinstance(p, Line):
                    sp = [SexprSerializer.Symbol('gr_line')] + self._serialize_LinePoints(p)
                elif isinstance(p, Circle):
                    sp = [SexprSerializer.Symbol('gr_circle')] + self._serialize_CirclePoints(p)
                elif isinstance(p, Arc):
                    sp = [SexprSerializer.Symbol('gr_arc')] + self._serialize_ArcPoints(p)
                else:
                    raise TypeError('Unsuported type of primitive for custom pad.')
                sp.append([SexprSerializer.Symbol('width'),
                           DEFAULT_WIDTH_POLYGON_PAD if p.width is None else p.width])
                sexpr_primitives.append(sp)

        return sexpr_primitives

    def _serialize_PadFabProperty(self, node) -> SexprSerializer.Symbol:
        mapping = {
            Pad.FabProperty.BGA: 'pad_prop_bga',
            Pad.FabProperty.FIDUCIAL_GLOBAL: 'pad_prop_pad_prop_heatsink',
            Pad.FabProperty.FIDUCIAL_LOCAL: 'pad_prop_fiducial_loc',
            Pad.FabProperty.HEATSINK: 'pad_prop_heatsink',
            Pad.FabProperty.TESTPOINT: 'pad_prop_testpoint',
            Pad.FabProperty.CASTELLATED: 'pad_prop_castellated',
        }
        return SexprSerializer.Symbol(mapping[node.fab_property])

    def _serialize_PadZoneConnection(self, node):
        # Inherited zone connection is implicit in the s-exp by a missing zone_connection node
        if node.zone_connection == Pad.ZoneConnection.INHERIT_FROM_FOOTPRINT:
            return None

        mapping = {
            Pad.ZoneConnection.NONE: 0,
            Pad.ZoneConnection.THERMAL_RELIEF: 1,
            Pad.ZoneConnection.SOLID: 2,
        }
        return mapping[node.zone_connection]

    def _serialize_Pad(self, node):
        sexpr = [
            SexprSerializer.Symbol('pad'),
            str(node.number),
            SexprSerializer.Symbol(node.type),
            SexprSerializer.Symbol(node.shape)
        ]

        position, rotation = node.getRealPosition(node.at, node.rotation)
        if not rotation % 360 == 0:
            sexpr.append([SexprSerializer.Symbol('at'), position.x, position.y, rotation])
        else:
            sexpr.append([SexprSerializer.Symbol('at'), position.x, position.y])

        sexpr.append([SexprSerializer.Symbol('size'), node.size.x, node.size.y])

        if node.type in [Pad.TYPE_THT, Pad.TYPE_NPTH]:

            if node.drill.x == node.drill.y:
                drill_config = [SexprSerializer.Symbol('drill'), node.drill.x]
            else:
                drill_config = [SexprSerializer.Symbol('drill'),
                                SexprSerializer.Symbol('oval'),
                                node.drill.x, node.drill.y]

            # append offset only if necessary
            if node.offset.x != 0 or node.offset.y != 0:
                drill_config.append([SexprSerializer.Symbol('offset'), node.offset.x,  node.offset.y])

            sexpr.append(drill_config)

        # As of format 20231231, 'property' contains only the fab value.
        if node.fab_property is not None:
            property_value = self._serialize_PadFabProperty(node)
            sexpr.append([SexprSerializer.Symbol('property'), property_value])

        sexpr.append([SexprSerializer.Symbol('layers')] + node.layers)
        if node.shape == Pad.SHAPE_ROUNDRECT:
            sexpr.append([SexprSerializer.Symbol('roundrect_rratio'), node.radius_ratio])

        if node.shape == Pad.SHAPE_CUSTOM:
            # gr_line, gr_arc, gr_circle or gr_poly
            sexpr.append(
                [SexprSerializer.Symbol('options'),
                    [SexprSerializer.Symbol('clearance'), SexprSerializer.Symbol(node.shape_in_zone)],
                    [SexprSerializer.Symbol('anchor'), SexprSerializer.Symbol(node.anchor_shape)]])

            sexpr_primitives = self._serialize_CustomPadPrimitives(node)
            sexpr.append([SexprSerializer.Symbol('primitives')] + sexpr_primitives)

        if node.solder_paste_margin_ratio != 0 or node.solder_mask_margin != 0 or node.solder_paste_margin != 0:
            if node.solder_mask_margin != 0:
                sexpr.append([SexprSerializer.Symbol('solder_mask_margin'),
                              node.solder_mask_margin])
            if node.solder_paste_margin_ratio != 0:
                sexpr.append([SexprSerializer.Symbol('solder_paste_margin_ratio'),
                              node.solder_paste_margin_ratio])
            if node.solder_paste_margin != 0:
                sexpr.append([SexprSerializer.Symbol('solder_paste_margin'),
                              node.solder_paste_margin])

        zone_connection_value = self._serialize_PadZoneConnection(node)
        if zone_connection_value is not None:
            sexpr.append([SexprSerializer.Symbol('zone_connect'), zone_connection_value])

        return sexpr

    def _serialize_PolygonPoints(self, node):
        node_points = [SexprSerializer.Symbol('pts')]
        for n in node.nodes:
            n_pos = node.getRealPosition(n)
            node_points.append([SexprSerializer.Symbol('xy'), n_pos.x, n_pos.y])

        return node_points

    def _serialize_Polygon(self, node):
        node_points = self._serialize_PolygonPoints(node)

        sexpr = [SexprSerializer.Symbol('fp_poly'),
                 node_points,
                 [SexprSerializer.Symbol('stroke')] + self._serialize_Stroke(node),
                 [SexprSerializer.Symbol('fill'), SexprSerializer.Symbol('solid')],
                 [SexprSerializer.Symbol('layer'), node.layer],
                ]  # NOQA

        return sexpr

    def _serialize_Zone(self, node):

        def _allow_or_not(allow: bool) -> SexprSerializer.Symbol:
            return SexprSerializer.Symbol('allowed') if allow else SexprSerializer.Symbol('not_allowed')

        def _serialise_Keepout(keepouts):

            sexpr = [SexprSerializer.Symbol('keepout')]

            def add_keepout(keepout_property, sexp_keyword: str) -> None:
                sexpr.append([
                    SexprSerializer.Symbol(sexp_keyword),
                    _allow_or_not(keepout_property == Keepouts.ALLOW)])

            add_keepout(keepouts.tracks, 'tracks')
            add_keepout(keepouts.vias, 'vias')
            add_keepout(keepouts.copperpour, 'copperpour')
            add_keepout(keepouts.pads, 'pads')
            add_keepout(keepouts.footprints, 'footprints')

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

        def _serialise_ZoneFill(node):
            sexpr = [SexprSerializer.Symbol('fill')]

            # no fill, all other tokens are unnecessary
            if node is None:
                return sexpr

            # we do have a fill
            sexpr.append(SexprSerializer.Symbol('yes'))

            def node_if_not_none(property: Optional[str], keyword: str) -> list:
                if property is None:
                    return []
                return [
                    [SexprSerializer.Symbol(keyword), SexprSerializer.Symbol(property)]
                ]

            # soild is encoded as no mode
            if node.fill != ZoneFill.FILL_SOLID:
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
                        [SexprSerializer.Symbol('radius'), node.smoothing_radius]],
                ]

            if node.island_removal_mode is not None:
                # Look up the encoding
                island_removal_mode = {
                    ZoneFill.ISLAND_REMOVAL_REMOVE: 0,
                    ZoneFill.ISLAND_REMOVAL_FILL: 1,
                    ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA: 2,
                }[node.island_removal_mode]

                sexpr + [SexprSerializer.Symbol('island_removal_mode'), island_removal_mode]

                # only valid in mode 2
                if node.island_removal_mode == 'minimum_area':
                    sexpr += [SexprSerializer.Symbol('island_area_min'), node.island_area_min]

            sexpr += node_if_not_none(node.hatch_thickness, 'hatch_thickness')
            sexpr += node_if_not_none(node.hatch_gap, 'hatch_gap')
            sexpr += node_if_not_none(node.hatch_orientation, 'hatch_orientation')
            sexpr += node_if_not_none(node.hatch_smoothing_level, 'hatch_smoothing_level')
            sexpr += node_if_not_none(node.hatch_smoothing_value, 'hatch_smoothing_value')
            sexpr += node_if_not_none(node.hatch_border_algorithm, 'hatch_border_algorithm')
            sexpr += node_if_not_none(node.hatch_min_hole_area, 'hatch_min_hole_area')
            return sexpr

        sexpr = [
            SexprSerializer.Symbol('zone'),
            [SexprSerializer.Symbol('net'), node.net],
            [SexprSerializer.Symbol('net_name'), node.net_name],
            self._serialise_Layers(node),
            [SexprSerializer.Symbol('name'), node.name],
            _serialize_Hatch(node.hatch)
        ]

        # Optional node
        if node.priority is not None:
            sexpr += [
                [SexprSerializer.Symbol('priority'), node.priority],
            ]

        sexpr += [
            _serialize_ConnectPads(node.connect_pads),
            # technically optional, but we can just always put it in
            self._serialise_Boolean('filled_areas_thickness', node.filled_areas_thickness),
            [SexprSerializer.Symbol('min_thickness'), node.min_thickness],
        ]

        # Optional node
        if node.keepouts is not None:
            sexpr += [
                _serialise_Keepout(node.keepouts),
            ]

        sexpr += [
            _serialise_ZoneFill(node.fill),
            [
                SexprSerializer.Symbol('polygon'),
                self._serialize_PolygonPoints(node)
            ]
        ]

        return sexpr
