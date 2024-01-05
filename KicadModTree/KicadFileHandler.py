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

        sexpr = ['footprint', self.kicad_mod.name,
                 ['version', '20221018'],
                 ['generator', 'kicad-footprint-generator'],
                 SexprSerializer.NEW_LINE,
                 ['layer', 'F.Cu'],
                 SexprSerializer.NEW_LINE,
                ]  # NOQA

        if self.kicad_mod.description:
            sexpr.append(['descr', self.kicad_mod.description])
            sexpr.append(SexprSerializer.NEW_LINE)

        if self.kicad_mod.tags:
            sexpr.append(["tags", " ".join(self.kicad_mod.tags)])
            sexpr.append(SexprSerializer.NEW_LINE)

        attributes = []

        footprint_type_str = self._typeToAttributeString(self.kicad_mod.footprintType)

        # If not unspecified, add the attribute
        if (footprint_type_str is not None):
            attributes.append(footprint_type_str)

        if self.kicad_mod.excludeFromBOM:
            attributes.append('exclude_from_bom')

        if self.kicad_mod.excludeFromPositionFiles:
            attributes.append('exclude_from_pos_files')

        if self.kicad_mod.allow_soldermask_bridges:
            attributes.append('allow_soldermask_bridges')

        # There might be no attributes
        if len(attributes) > 0:
            sexpr.append(['attr'] + attributes)
            sexpr.append(SexprSerializer.NEW_LINE)

        if self.kicad_mod.maskMargin:
            sexpr.append(['solder_mask_margin', self.kicad_mod.maskMargin])
            sexpr.append(SexprSerializer.NEW_LINE)

        if self.kicad_mod.pasteMargin:
            sexpr.append(['solder_paste_margin', self.kicad_mod.pasteMargin])
            sexpr.append(SexprSerializer.NEW_LINE)

        if self.kicad_mod.pasteMarginRatio:
            sexpr.append(['solder_paste_ratio', self.kicad_mod.pasteMarginRatio])
            sexpr.append(SexprSerializer.NEW_LINE)

        sexpr.extend(self._serializeTree())

        return str(SexprSerializer(sexpr))

    def _serializeTree(self):
        nodes = self.kicad_mod.serialize()

        grouped_nodes = {}

        for single_node in nodes:
            node_type = single_node.__class__.__name__

            current_nodes = grouped_nodes.get(node_type, [])
            current_nodes.append(single_node)

            grouped_nodes[node_type] = current_nodes

        sexpr = []

        # serialize initial text nodes
        if 'Text' in grouped_nodes:
            reference_nodes = list(filter(lambda node: node.type == 'reference', grouped_nodes['Text']))
            for node in reference_nodes:
                sexpr.append(self._serialize_Text(node))
                sexpr.append(SexprSerializer.NEW_LINE)
                grouped_nodes['Text'].remove(node)

            value_nodes = list(filter(lambda node: node.type == 'value', grouped_nodes['Text']))
            for node in value_nodes:
                sexpr.append(self._serialize_Text(node))
                sexpr.append(SexprSerializer.NEW_LINE)
                grouped_nodes['Text'].remove(node)

        for key, value in sorted(grouped_nodes.items()):
            # check if key is a base node, except Model
            if key not in {'Arc', 'Circle', 'Line', 'Pad', 'Polygon', 'Text', 'Zone'}:
                continue

            # render base nodes
            for node in value:
                sexpr.append(self._callSerialize(node))
                sexpr.append(SexprSerializer.NEW_LINE)

        # serialize 3D Models at the end
        if grouped_nodes.get('Model'):
            for node in grouped_nodes.get('Model'):
                sexpr.append(self._serialize_Model(node))
                sexpr.append(SexprSerializer.NEW_LINE)

        return sexpr

    def _typeToAttributeString(self, footprintType: FootprintType):
        """
        Convert the footprint type to the corresponding attribute string
        in the .kicad_mod format s-expr attr node
        """
        return {
            FootprintType.UNSPECIFIED: None,
            FootprintType.SMD: 'smd',
            FootprintType.THT: 'through_hole',
        }[footprintType]

    def _callSerialize(self, node):
        '''
        call the corresponding method to serialize the node
        '''
        method_type = node.__class__.__name__
        method_name = "_serialize_{0}".format(method_type)
        if hasattr(self, method_name):
            return getattr(self, method_name)(node)
        else:
            exception_string = "{name} (node) not found, cannot serialized the node of type {type}"
            raise NotImplementedError(exception_string.format(name=method_name, type=method_type))

    def _serialize_Stroke(self, node):
        width = _get_layer_width(node.layer, node.width)

        return [
            ['width', width],
            ['type', 'solid'],
        ]

    def _serialize_ArcPoints(self, node):
        start_pos = node.getRealPosition(node.getStartPoint())
        end_pos = node.getRealPosition(node.getEndPoint())
        mid_pos = node.getRealPosition(node.getMidPoint())
        # swap start and end for negative angles to overcome a bug in KiCAD v6 and some v7 versions
        if (node.angle < 0):
            start_pos, end_pos = end_pos, start_pos
        return [
            ['start', start_pos.x, start_pos.y],
            ['mid', mid_pos.x, mid_pos.y],
            ['end', end_pos.x, end_pos.y],
        ]

    def _serialize_Arc(self, node):
        sexpr = ['fp_arc']
        sexpr += self._serialize_ArcPoints(node)
        sexpr += [
                  SexprSerializer.NEW_LINE,
                  ['stroke'] + self._serialize_Stroke(node),
                  ['layer', node.layer],
                 ]  # NOQA

        return sexpr

    def _serialize_CirclePoints(self, node):
        center_pos = node.getRealPosition(node.center_pos)
        end_pos = node.getRealPosition(node.center_pos + (node.radius, 0))

        return [
            ['center', center_pos.x, center_pos.y],
            ['end', end_pos.x, end_pos.y]
        ]

    def _serialize_Circle(self, node):
        sexpr = ['fp_circle']
        sexpr += self._serialize_CirclePoints(node)
        sexpr += [
                  SexprSerializer.NEW_LINE,
                  ['stroke'] + self._serialize_Stroke(node),
                  ['layer', node.layer],
                 ]  # NOQA

        return sexpr

    def _serialise_Layers(self, node):
        layers = node.layers

        # Maybe one day this be simplified in the s-expr format
        if len(layers) == 1:
            return ['layer', layers[0]]

        return ['layers'] + layers

    def _serialize_LinePoints(self, node):
        start_pos = node.getRealPosition(node.start_pos)
        end_pos = node.getRealPosition(node.end_pos)
        return [
            ['start', start_pos.x, start_pos.y],
            ['end', end_pos.x, end_pos.y]
        ]

    def _serialize_Line(self, node):
        sexpr = ['fp_line']
        sexpr += self._serialize_LinePoints(node)
        sexpr += [
            SexprSerializer.NEW_LINE,
            ['stroke'] + self._serialize_Stroke(node),
            ['layer', node.layer],
        ]

        return sexpr

    def _serialize_Text(self, node):
        sexpr = ['fp_text', node.type, node.text]

        position, rotation = node.getRealPosition(node.at, node.rotation)
        if rotation:
            sexpr.append(['at', position.x, position.y, rotation])
        else:
            sexpr.append(['at', position.x, position.y])

        sexpr.append(['layer', node.layer])
        if node.hide:
            sexpr.append('hide')
        sexpr.append(SexprSerializer.NEW_LINE)

        effects = [
            'effects',
            ['font',
             ['size', node.size.x, node.size.y],
             ['thickness', node.thickness]]]

        justify = []
        if node.mirror:
            justify.append('mirror')
        if node.justify:
            justify.append(node.justify)
        if (len(justify)):
            effects.append(['justify'] + justify)

        sexpr.append(effects)
        sexpr.append(SexprSerializer.NEW_LINE)

        return sexpr

    def _serialize_Model(self, node):
        sexpr = ['model', node.filename,
                 SexprSerializer.NEW_LINE,
                 ['offset', ['xyz', node.at.x, node.at.y, node.at.z]],
                 SexprSerializer.NEW_LINE,
                 ['scale', ['xyz', node.scale.x, node.scale.y, node.scale.z]],
                 SexprSerializer.NEW_LINE,
                 ['rotate', ['xyz', node.rotate.x, node.rotate.y, node.rotate.z]],
                 SexprSerializer.NEW_LINE
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
                    sp = ['gr_poly',
                          self._serialize_PolygonPoints(p, newline_after_pts=True)
                         ]  # NOQA
                elif isinstance(p, Line):
                    sp = ['gr_line'] + self._serialize_LinePoints(p)
                elif isinstance(p, Circle):
                    sp = ['gr_circle'] + self._serialize_CirclePoints(p)
                elif isinstance(p, Arc):
                    sp = ['gr_arc'] + self._serialize_ArcPoints(p)
                else:
                    raise TypeError('Unsuported type of primitive for custom pad.')
                sp.append(['width', DEFAULT_WIDTH_POLYGON_PAD if p.width is None else p.width])
                sexpr_primitives.append(sp)
                sexpr_primitives.append(SexprSerializer.NEW_LINE)

        return sexpr_primitives

    def _serialize_PadFabProperty(self, node):
        mapping = {
            Pad.FabProperty.BGA: 'pad_prop_bga',
            Pad.FabProperty.FIDUCIAL_GLOBAL: 'pad_prop_pad_prop_heatsink',
            Pad.FabProperty.FIDUCIAL_LOCAL: 'pad_prop_fiducial_loc',
            Pad.FabProperty.HEATSINK: 'pad_prop_heatsink',
            Pad.FabProperty.TESTPOINT: 'pad_prop_testpoint',
            Pad.FabProperty.CASTELLATED: 'pad_prop_castellated',
        }
        return mapping[node.fab_property]

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
        sexpr = ['pad', node.number, node.type, node.shape]

        position, rotation = node.getRealPosition(node.at, node.rotation)
        if not rotation % 360 == 0:
            sexpr.append(['at', position.x, position.y, rotation])
        else:
            sexpr.append(['at', position.x, position.y])

        sexpr.append(['size', node.size.x, node.size.y])

        if node.type in [Pad.TYPE_THT, Pad.TYPE_NPTH]:

            if node.drill.x == node.drill.y:
                drill_config = ['drill', node.drill.x]
            else:
                drill_config = ['drill', 'oval', node.drill.x, node.drill.y]

            # append offset only if necessary
            if node.offset.x != 0 or node.offset.y != 0:
                drill_config.append(['offset', node.offset.x,  node.offset.y])

            sexpr.append(drill_config)

        # As of format 20231231, 'property' contains only the fab value.
        if node.fab_property is not None:
            property_value = self._serialize_PadFabProperty(node)
            sexpr.append(['property', property_value])

        sexpr.append(['layers'] + node.layers)
        if node.shape == Pad.SHAPE_ROUNDRECT:
            sexpr.append(['roundrect_rratio', node.radius_ratio])

        if node.shape == Pad.SHAPE_CUSTOM:
            # gr_line, gr_arc, gr_circle or gr_poly
            sexpr.append(SexprSerializer.NEW_LINE)
            sexpr.append(['options',
                         ['clearance', node.shape_in_zone],
                         ['anchor', node.anchor_shape]
                        ])  # NOQA
            sexpr.append(SexprSerializer.NEW_LINE)
            sexpr_primitives = self._serialize_CustomPadPrimitives(node)
            sexpr.append(['primitives', SexprSerializer.NEW_LINE] + sexpr_primitives)

        if node.solder_paste_margin_ratio != 0 or node.solder_mask_margin != 0 or node.solder_paste_margin != 0:
            sexpr.append(SexprSerializer.NEW_LINE)
            if node.solder_mask_margin != 0:
                sexpr.append(['solder_mask_margin', node.solder_mask_margin])
            if node.solder_paste_margin_ratio != 0:
                sexpr.append(['solder_paste_margin_ratio', node.solder_paste_margin_ratio])
            if node.solder_paste_margin != 0:
                sexpr.append(['solder_paste_margin', node.solder_paste_margin])

        zone_connection_value = self._serialize_PadZoneConnection(node)
        if zone_connection_value is not None:
            sexpr.append(SexprSerializer.NEW_LINE)
            sexpr.append(['zone_connect', zone_connection_value])

        return sexpr

    def _serialize_PolygonPoints(self, node, newline_after_pts=False,
                                 newline_after_n_points=4):
        node_points = ['pts']
        if newline_after_pts:
            node_points.append(SexprSerializer.NEW_LINE)
        points_appended = 0
        for n in node.nodes:
            if points_appended >= newline_after_n_points:
                points_appended = 0
                node_points.append(SexprSerializer.NEW_LINE)
            points_appended += 1

            n_pos = node.getRealPosition(n)
            node_points.append(['xy', n_pos.x, n_pos.y])

        return node_points

    def _serialize_Polygon(self, node):
        node_points = self._serialize_PolygonPoints(node)

        sexpr = ['fp_poly',
                 node_points,
                 SexprSerializer.NEW_LINE,
                 ['stroke'] + self._serialize_Stroke(node),
                 ['fill', 'solid'],
                 ['layer', node.layer],
                ]  # NOQA

        return sexpr

    def _serialize_Zone(self, node):

        def _serialise_Keepout(keepouts):

            sexpr = ['keepout']

            def add_keepout(keepout_property, sexp_keyword: str) -> None:
                sexpr.append([sexp_keyword, 'allowed' if (keepout_property == Keepouts.ALLOW) else 'not_allowed'])

            add_keepout(keepouts.tracks, 'tracks')
            add_keepout(keepouts.vias, 'vias')
            add_keepout(keepouts.copperpour, 'copperpour')
            add_keepout(keepouts.pads, 'pads')
            add_keepout(keepouts.footprints, 'footprints')

            return sexpr

        def _serialize_Hatch(node):
            return ['hatch', node.style, node.pitch]

        def _serialize_ConnectPads(node):
            sexpr = ['connect_pads']
            type = node.type
            if type is not PadConnection.THERMAL_RELIEF:
                sexpr.append(type)

            sexpr.append(['clearance', node.clearance])
            return sexpr

        def _serialise_ZoneFill(node):
            sexpr = ['fill']

            # no fill, all other tokens are unnecessary
            if node is None:
                return sexpr

            # we do have a fill
            sexpr.append('yes')

            def node_if_not_none(property, keyword: str) -> list:
                if property is None:
                    return []
                return [
                    SexprSerializer.NEW_LINE,
                    [keyword, property]
                ]

            # soild is encoded as no mode
            if node.fill != ZoneFill.FILL_SOLID:
                sexpr += [
                    SexprSerializer.NEW_LINE,
                    ['mode', node.fill],
                ]

            # Thermal gap and bridge with aren't optional
            sexpr += [
                SexprSerializer.NEW_LINE,
                ['thermal_gap', node.thermal_gap],
                SexprSerializer.NEW_LINE,
                ['thermal_bridge_width', node.thermal_bridge_width],
            ]

            if node.smoothing is not None:
                sexpr += [
                    SexprSerializer.NEW_LINE,
                    ['smoothing', node.smoothing, ['radius', node.smoothing_radius]],
                ]

            if node.island_removal_mode is not None:
                # Look up the encoding
                island_removal_mode = {
                    ZoneFill.ISLAND_REMOVAL_REMOVE: 0,
                    ZoneFill.ISLAND_REMOVAL_FILL: 1,
                    ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA: 2,
                }[node.island_removal_mode]
                sexpr += node_if_not_none(island_removal_mode, 'island_removal_mode')

                # only valid in mode 2
                if node.island_removal_mode == 'minimum_area':
                    sexpr += node_if_not_none(node.island_area_min, 'island_area_min')

            sexpr += node_if_not_none(node.hatch_thickness, 'hatch_thickness')
            sexpr += node_if_not_none(node.hatch_gap, 'hatch_gap')
            sexpr += node_if_not_none(node.hatch_orientation, 'hatch_orientation')
            sexpr += node_if_not_none(node.hatch_smoothing_level, 'hatch_smoothing_level')
            sexpr += node_if_not_none(node.hatch_smoothing_value, 'hatch_smoothing_value')
            sexpr += node_if_not_none(node.hatch_border_algorithm, 'hatch_border_algorithm')
            sexpr += node_if_not_none(node.hatch_min_hole_area, 'hatch_min_hole_area')
            return sexpr

        sexpr = [
            'zone',
            SexprSerializer.NEW_LINE,
            ['net', node.net],
            SexprSerializer.NEW_LINE,
            ['net_name', node.net_name],
            SexprSerializer.NEW_LINE,
            self._serialise_Layers(node),
            SexprSerializer.NEW_LINE,
            ['name', node.name],
            SexprSerializer.NEW_LINE,
            _serialize_Hatch(node.hatch)
        ]

        # Optional node
        if node.priority is not None:
            sexpr += [
                SexprSerializer.NEW_LINE,
                ['priority', node.priority],
            ]

        sexpr += [
            SexprSerializer.NEW_LINE,
            _serialize_ConnectPads(node.connect_pads),
            SexprSerializer.NEW_LINE,
            # technically optional, but we can just always put it in
            ['filled_areas_thickness', 'yes' if node.filled_areas_thickness else 'no'],
            SexprSerializer.NEW_LINE,
            ['min_thickness', node.min_thickness],
            SexprSerializer.NEW_LINE,
        ]

        # Optional node
        if node.keepouts is not None:
            sexpr += [
                _serialise_Keepout(node.keepouts),
                SexprSerializer.NEW_LINE,
            ]

        sexpr += [
            _serialise_ZoneFill(node.fill),
            SexprSerializer.NEW_LINE,
            ['polygon', self._serialize_PolygonPoints(
                node, newline_after_pts=True, newline_after_n_points=1)]
        ]

        return sexpr
