#!/usr/bin/env python3

"""
KicadModTree is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

KicadModTree is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.

Authors:
    - Armin Schoisswohl (@armin.sch), <armin.schoisswohl@myotis.at>
    - Carlos Nieves Ónega (@cnieves1)
    - John Beard (@johnbeard)
    - ... (not complete)
"""

import sys
import os
import warnings
import re

import argparse
import yaml
from math import pi, floor, ceil
from fnmatch import fnmatch
from typing import Iterable, Callable
from dataclasses import dataclass, asdict

# ensure that the kicad-footprint-generator directory is available
#sys.path.append(os.environ.get('KIFOOTPRINTGENERATOR'))  # enable package import from parent directory
#sys.path.append("D:\hardware\KiCAD\kicad-footprint-generator")  # enable package import from parent directory
sys.path.append(os.path.join(sys.path[0], "..", "..", "..")) # load kicad_mod path
#sys.path.append(os.path.join(sys.path[0], "..", "..", "tools")) # load kicad_mod path

from KicadModTree import *  # NOQA
from scripts.tools.footprint_text_fields import addTextFields
from scripts.tools.dict_tools import dictMerge, dictInherit
from scripts.tools.declarative_def_tools import utils, rule_area_properties, shape_properties
from scripts.tools.declarative_def_tools.utils import DotDict
from scripts.tools.declarative_def_tools.ast_evaluator import ASTevaluator, ASTexprEvaluator
from scripts.tools.drawing_tools import point_is_on_segment

DEFAULT_SMT_PAD_SHAPE = 'roundrect'
DEFAULT_THT_PAD_SHAPE = 'circ'
DEFAULT_ROUNDRECT_RRATIO = 0.25
DEFAULT_ROUNDRECT_RMAX = 0.25

KICAD_3DMODEL_DIR = "${KICAD8_3DMODEL_DIR}"


def _get_dims(name: str, spec: dict, base: Vector2D = None, mult: float=1):
    if (base is None):
        base = Vector2D(0, 0)
    vals = spec.get(name, {})
    if isinstance(vals, dict):
        return Vector2D(*[_get_dim(name, spec, dim="xy"[n], mult=mult,
                                   base=base[n]) for n in range(2)])
    elif isinstance(vals, list):
        return Vector2D(*[v for v in vals])
    elif isinstance(vals, (float, int, str)):
        return base + vals
    else:
        return base


def _get_dim(name: str, spec: dict, dim: str, base: float=0.0, mult: float=1):
    if (name not in spec):
        return base
    dim_spec = spec[name]
    if (dim in dim_spec):
        if ("%s_offset" % dim in dim_spec):
            warnings.warn(f"\nboth, {dim} and {dim}_offset are specified; {dim}_offset is overridden by {dim}", Warning)
        return dim_spec[dim]
    elif (base != 0.0 and "%s_offset" % dim in dim_spec):
        value = dim_spec["%s_offset" % dim]
        if isinstance(value, (int, float, str)):
            return base + mult * value
        else:
            return [base + mult * v for v in value]
    else:
        raise LookupError("one of '%s', '%s_offset' has to be specified for '%s'" % (dim, dim, name))


def _round_to(val, base, direction: str=None):
    if (isinstance(val, Iterable)):
        return [round_to(v, base, direction) for v in val]
    if (direction in ['+', 1]):
        return ceil(val / base) * base
    elif (direction in ['-', -1]):
        return floor(val / base) * base
    else:
        return round(val / base) * base


@dataclass
class PadProperties():
    size: Vector2D
    shape: str
    radius_ratio: float
    max_radius: float
    drill: float
    paste: bool
    type: str
    layers: list
    rotation: float

    def __init__(self, pad_spec, *, default_paste: bool = None):
        self.size = self._get_pad_size(pad_spec)
        self.shape = self._get_pad_shape(pad_spec)
        self.radius_ratio = self._get_pad_rratio(pad_spec)
        self.max_radius = self._get_pad_rmax(pad_spec)
        self.drill = self._get_pad_drill(pad_spec)
        self.paste = self._get_pad_paste(pad_spec, default_paste)
        self.type = self._get_pad_type(pad_spec)
        self.layers = self._get_pad_layers(pad_spec, default_paste)
        self.rotation = self._get_pad_rotation(pad_spec)
        if (not self.size or self.size.is_nullvec()):
            self.size = Vector2D(self.drill, self.drill)
        if (self.paste and self.type != Pad.TYPE_NPTH and 'F.Paste' not in self.layers):
            self.layers.append('F.Paste')

    def as_args(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

    def _get_pad_size(self, pad_spec):
        return _get_dims("size", spec=pad_spec)

    def _get_pad_shape(self, pad_spec):
        shape = pad_spec.get("shape", None)
        if (shape is None):
            shape = DEFAULT_THT_PAD_SHAPE if self._get_pad_drill(pad_spec) else DEFAULT_SMT_PAD_SHAPE
        return {"rect": Pad.SHAPE_RECT,
                "roundrect": Pad.SHAPE_ROUNDRECT,
                "circ": Pad.SHAPE_CIRCLE,
                "oval": Pad.SHAPE_OVAL,
                }[shape]

    def _get_pad_rratio(self, pad_spec):
        return pad_spec.get("rratio", DEFAULT_ROUNDRECT_RRATIO)

    def _get_pad_rmax(self, pad_spec):
        return pad_spec.get("rratio", DEFAULT_ROUNDRECT_RMAX)

    def _get_pad_drill(self, pad_spec):
        return pad_spec.get("drill", None)

    def _get_pad_paste(self, pad_spec, default_paste: bool = None):
        if (default_paste is None):
            return pad_spec.get("paste", False if self._get_pad_drill(pad_spec) else True)
        else:
            return pad_spec.get("paste", default_paste)

    def _get_pad_copper(self, pad_spec):
        return pad_spec.get("copper", True)

    def _get_pad_type(self, pad_spec):
        if (self._get_pad_drill(pad_spec)):
            if (self._get_pad_copper(pad_spec) and self._get_pad_drill(pad_spec) < max(self._get_pad_size(pad_spec))):
                return Pad.TYPE_THT
            else:
                return Pad.TYPE_NPTH
        else:
            return Pad.TYPE_SMT

    def _get_pad_layers(self, pad_spec, default_paste: bool = None):
        copper = self._get_pad_copper(pad_spec)
        paste = self._get_pad_paste(pad_spec, default_paste)
        pad_type = self._get_pad_type(pad_spec)
        if (pad_type == Pad.TYPE_NPTH):
            return Pad.LAYERS_NPTH
        elif (pad_type == Pad.TYPE_THT):
            return Pad.LAYERS_THT + ['F.Paste'] if (paste is True) else Pad.LAYERS_THT
        elif (pad_type == Pad.TYPE_SMT):
            if (copper is False):
                return [] if (paste is False) else ['F.Paste']
            else:
                return Pad.LAYERS_CONNECT_FRONT if (paste is False) else Pad.LAYERS_SMT

    def _get_pad_rotation(self, pad_spec):
        return pad_spec.get("rotation", 0)

@dataclass
class FPconfiguration():
    library_name: str
    pad_pitch: float
    num_pos: int
    pad_size: Vector2D
    pad_pos_range: Vector2D
    pad_center_offset: Vector2D
    row_pitch: float = 0.0
    row_x_offset: float = 0.0
    num_rows: int = 1
    gap_pos: int = 0
    gap_size: int = 0
    pad_properties: PadProperties = None
    pad1_properties: PadProperties = None
    is_smt_footprint: bool = True
    skipped_positions: list = None
    num_mount_pads: int = 0
    body_edges: dict = None
    rule_areas: list = None
    silk_fab_offset : float = 0.0
    silk_line_width : float = 0.0
    pin1_pos: str = 'top'
    pin1_body_chamfer: float = 0.0
    pin1_marker_shape: str = None
    pin1_marker_size: float = 0.0
    pin1_marker_pos: Vector2D = None
    pin1_on_fab: bool = True
    parameters: dict = None
    expr_eval: Callable = None

    def __init__(self, spec: dict, *, positions: int, idx: int, configuration: dict):
        self.library_name = spec["library"]
        self.num_pos = positions
        # create the evaluator
        self.asteval = ASTevaluator(protected=True)
        # parse parameters first
        params = spec.get('parameters', {})
        params.update(num_pos=positions, idx=idx)
        self.parameters = self.asteval.eval(params, allow_self_ref=True, symbols=spec, allow_nested=True) # TODO: allow_nested should allow arbitrary eorder evaluations
        # parse spec but skip back the following sections as they may need t, b, l, r, etc.
        self.spec = self.asteval.eval(spec, allow_self_ref=True, raise_errors=True, symbols=self.parameters, allow_nested=True)

        self.pad_pitch = self.spec["pad_pitch"]
        ## row pitch defines if it is a single or dual row connector
        self.row_pitch = self.spec.get("row_pitch", None)
        if (self.row_pitch is None):
            self.row_pitch = 0.0
        self.num_rows = 2 if self.row_pitch else 1

        ## row_x_offset defines if it has staggered pins or not
        self.row_x_offset = self.spec.get("row_x_offset", 0.0)

        ## collection information about an eventual gap in the pin layout
        gap = self.spec.get("gap", {}).get(positions, [0, 0])
        if (isinstance(gap, dict)):
            gap = [ gap.get("position", 0), gap.get("size", 1) ]
        elif (isinstance(gap, int)):
            gap = [gap, 1]
        self.gap_pos, self.gap_size = gap
        if (self.gap_pos and self.gap_size):
            self.skipped_positions = [self.gap_pos + n for n in range(self.gap_size)]
        else:
            self.skipped_positions = []

        ## check if there are mount pads
        self.num_mount_pads = len({ep["name"] for ep in self.spec.get("mount_pads", {}).values() if "name" in ep})

        ## get pad positions and size
        pad_spec = self.spec.get("pads")
        self.pad_properties = PadProperties(pad_spec)
        self.pad_size = self.pad_properties.size
        self.is_smt_footprint = (self.pad_properties.type == Pad.TYPE_SMT)

        self.pad_center_offset = _get_dims("pads", spec=self.spec.get("offset", {}))
        self.pad_pos_range = Vector2D((positions + self.gap_size - 1) * self.pad_pitch, self.row_pitch)

        ## calculate body size
        body_size = _get_dims("body_size", spec=self.spec, base=self.pad_pos_range, mult=2)
        body_center_offset = _get_dims("body", spec=self.spec.get("offset", {}))
        self.body_edges = DotDict({
            "left": -0.5 * body_size.x + body_center_offset.x,
            "right": 0.5 * body_size.x + body_center_offset.x,
            "top": -0.5 * body_size.y + body_center_offset.y,
            "bottom": 0.5 * body_size.y + body_center_offset.y,
        })

        # assemble the dimensions
        self.parameters.update({k[0]: v for k, v in self.body_edges.items()})
        self.parameters.pl = -0.5 * self.pad_pos_range.x + self.pad_center_offset.x
        self.parameters.pr = 0.5 * self.pad_pos_range.x + self.pad_center_offset.x
        self.parameters.pt = -0.5 * self.pad_pos_range.y + self.pad_center_offset.y
        self.parameters.pb = 0.5 * self.pad_pos_range.y + self.pad_center_offset.y

        self.expr_eval = ASTexprEvaluator(symbols=self.parameters)

        ## Get rule areas
        self.rule_areas = rule_area_properties.RuleAreaProperties.from_standard_yaml(self.spec)

        ## get silk-fab-offset (may be overriden in the YAML)
        self.silk_fab_offset = self.spec.get('silk_fab_offset', configuration['silk_fab_offset'])
        self.silk_line_width = configuration['silk_line_width']

        ## get information about 1st pin
        first_pin_spec = self.spec.get("first_pin", {})
        self.pin1_pos = first_pin_spec.get("position", "top")
        if (self.pin1_pos not in ["top", "bottom"]):
            raise ValueError("'first_pin.position' must be one of 'top', 'bottom'")
        if (pad1_spec := first_pin_spec.get("pad", None)):
            self.pad1_properties = PadProperties(pad1_spec)

        ## body chamfer at pin1 corner
        self.pin1_body_chamfer = first_pin_spec.get("body_chamfer", 0.0)
        # on some locations scale_y will do the magic to be on the correct side relative to the pin 1 side
        self.scale_y = { "top": -1, "bottom": 1 }[self.pin1_pos]

        ## pin 1 marker properties
        self.pin1_marker_shape = first_pin_spec.get("marker", {}).get("shape", None)
        self.pin1_marker_size = first_pin_spec.get("marker", {}).get("size", self.pad_size.x) / 2
        pin1_offset = first_pin_spec.get("marker", { }).get("offset", 0)
        if (isinstance(pin1_offset, (int, float))):
            pin1_offset = Vector2D(0, pin1_offset)
        elif (isinstance(pin1_offset, dict)):
            pin1_offset = Vector2D(**pin1_offset)
        else:
            pin1_offset = Vector2D(*pin1_offset)
        pin1_offset.y += self.pin1_marker_size

        self.pin1_marker_pos = Vector2D(-0.5 * (self.pad_pos_range.x + self.row_x_offset) + self.pad_center_offset.x,
                                        self.body_edges[self.pin1_pos]) + pin1_offset * Vector2D(1, self.scale_y)
        self.draw_pin1_marker_on_fab = first_pin_spec.get("marker", { }).get("fab", True)

        ## exclude_from_bom and exclude_from_pos
        self.exclude_from_bom = self.spec.get("exclude_from_bom", False)
        self.exclude_from_pos = self.spec.get("exclude_from_pos", False)

    def eval_coordinate(self, coord):
        return self.asteval.parse_float(coord, symbols=self.parameters)


def parse_body_shape(spec, *, side: str, eval_expr: Callable):
    shape_spec = spec.get(side, {})
    sign = Vector2D(1,1)
    if (shape_spec == "mirror"):
        shape_spec = spec.get({"left": "right", "right": "left", "top": "bottom", "bottom": "top"}[side], {})
        if (side in ["left", "right"]):
            sign.x = -1
        else:
            sign.y = -1

    nodes = []
    if shape_spec:
        for shape in shape_spec.keys():
            if shape == "polyline":
                for node in shape_spec[shape]:
                    try:
                        xy = Vector2D(*[eval_expr(coord) for coord in node])
                        nodes.append(sign * xy)
                    except Exception as e:
                        raise ValueError("failed to parse polyline node '%s'" % node)
            else:
                raise ValueError("only polyline shapes are implemented, not '%s'" % shape)
    # eventuelly revert the node list to make sure we are running clockwise (in the KiCad coordinate system)
    reverse = False
    if (len(nodes) > 1):
        if (side == "left" and nodes[0].y < nodes[-1].y):
            reverse = True
        if (side == "right" and nodes[0].y > nodes[-1].y):
            reverse = True
        if (side == "top" and nodes[0].x > nodes[-1].x):
            reverse = True
        if (side == "bottom" and nodes[0].x < nodes[-1].x):
            reverse = True
    return [_ for _ in reversed(nodes)] if reverse else nodes


def generate_one_footprint(positions: int, *, spec, configuration: dict, idx=0):
    # deprecate doc_parameters
    if ("doc_parameters" in spec):
        if ("parameters" in spec):
            raise KeyError("key 'parameters' replaces deprecated key 'doc_parameters' im YAML specification; your specification contains both")
        warnings.warn("\nUsage of 'doc_parameters' in YAML specification is deprecated; use 'parameters' instead.\nAlso replace 'eval(...)' in all YAMLs by '$(...)'", category=DeprecationWarning)
        spec["parameters"] = spec.pop("doc_parameters")

    for f in ["description", "tags", "fp_name", ]:
        if (f not in spec):
            raise ValueError(f"missing mandatory field '{f}' in footprint specification")

    fp_config = FPconfiguration(spec, positions=positions, idx=idx, configuration=configuration)

    # for format strings both, all fields of the spec and all fields of spec.parameters are accessible
    format_dict = DotDict(**fp_config.spec, **fp_config.parameters)

    ## assemble footprint name
    fp_name = fp_config.spec.fp_name.format(**format_dict)

    rows = fp_config.spec.get('fp_name_rows', fp_config.num_rows)
    pins_per_row = fp_config.spec.get('fp_name_pins_per_row', fp_config.num_pos)
    fp_name += "_%dx%02d"  % (rows, pins_per_row)

    if (fp_config.num_mount_pads):
        fp_name += "-%dMP" % fp_config.num_mount_pads

    pitch = fp_config.spec.get('fp_name_pitch', fp_config.pad_pitch)
    fp_name += "_P%smm" %  pitch

    if (fp_config.gap_pos and fp_config.gap_size):
        fp_name += "_Pol%02d" % fp_config.gap_pos

    fp_name += fp_config.spec.get("fp_suffix", "").format(**format_dict)

    ## information about what is generated
    print("  - %s" % fp_name)

    ## create the footprint
    footprint_type = FootprintType.SMD if fp_config.is_smt_footprint else FootprintType.THT

    kicad_mod = Footprint(fp_name, footprint_type)

    kicad_mod.excludeFromBOM = fp_config.exclude_from_bom
    kicad_mod.excludeFromPositionFiles = fp_config.exclude_from_pos

    ## set the FP description
    description = fp_config.spec.description.format(**format_dict)
    if (src := fp_config.spec.get("source", None)):
        description += " (source: " + src + ")"
    kicad_mod.setDescription(description)

    ## set the FP tags
    tags = fp_config.spec.tags.format(**format_dict)
    kicad_mod.setTags(tags)

    ## create extra pads/drills
    for mp_name, pad_spec in fp_config.spec.get("mount_pads", DotDict()).items():
        add_mount_pad(kicad_mod,
                      pad_pos_range=fp_config.pad_pos_range,
                      pad_spec=pad_spec,
                      pad_center_offset=fp_config.pad_center_offset,
                      default_paste=fp_config.pad_properties.paste,
                      row_x_offset=fp_config.row_x_offset)

    ## collect information from body_shape spec
    body_spec = fp_config.spec.get("body_shape", DotDict())
    body_shape_nodes = build_body_shape(body_spec, fp_config=fp_config)

    ## draw body outline on F.Fab
    fab_outline = PolygonLine(nodes=body_shape_nodes,
                              layer="F.Fab",
                              width=configuration['fab_line_width'])
    kicad_mod.append(fab_outline)

    ## draw additional shapes onto F.Fab
    for name, shape in body_spec.items():
        if (name in ["left", "right", "top", "bottom"]):
            continue
        poly_nodes = parse_body_shape(fp_config.spec.get("body_shape", {}), side=name, eval_expr=fp_config.expr_eval)
        kicad_mod.append(PolygonLine(nodes=poly_nodes, layer="F.Fab", width=configuration["fab_line_width"]))

    ## create Pads
    start_pos_x = -0.5 * (fp_config.pad_pos_range.x + fp_config.row_x_offset) + fp_config.pad_center_offset.x
    for row in range(fp_config.num_rows):
        pos_y = (0.5 if row == 0 else -0.5) * fp_config.pad_pos_range.y * fp_config.scale_y + fp_config.pad_center_offset.y
        row_x_offset = 0 if (row % 2)== 0 else fp_config.row_x_offset
        col_num = 0
        for col in range(ceil(positions) + fp_config.gap_size):
            if (col not in fp_config.skipped_positions):
                pad_number = fp_config.num_rows * col_num + row + 1
                if (pad_number > fp_config.num_rows * positions):
                    continue
                pad_props = fp_config.pad1_properties if (pad_number == 1 and fp_config.pad1_properties) else fp_config.pad_properties
                kicad_mod.append(Pad(number=pad_number,
                                     at=[start_pos_x + col * fp_config.pad_pitch, pos_y],
                                     **pad_props.as_args()))
                col_num += 1
        pos_y *= -1 # switch to opposite row

    ## Create rule areas (keepouts)
    rule_area_zones = rule_area_properties.create_rule_area_zones(fp_config.rule_areas,
                                                                  expr_evaluator=fp_config.expr_eval)
    for rule_area_zone in rule_area_zones:
        kicad_mod.append(rule_area_zone)

    ## calculate the bounding box of the whole footprint (excluding silk)
    bbox = kicad_mod.calculateBoundingBox()

    ## draw silk
    ## duplicate the body shape contour onto F.SilkS with the silk_fab_offset
    silk_outline = fab_outline.duplicate(layer="F.SilkS",
                                         offset=fp_config.silk_fab_offset,
                                         width=fp_config.silk_line_width)
    kicad_mod.append(silk_outline)

    ## pin 1 indicator on Silk
    pin1_silk = make_pin1_marker(pos=fp_config.pin1_marker_pos,
                                 radius=fp_config.pin1_marker_size,
                                 shape=fp_config.pin1_marker_shape,
                                 flip_marker=fp_config.scale_y < 0,
                                 width=fp_config.silk_line_width,
                                 offset=fp_config.silk_fab_offset + 2 * fp_config.silk_line_width)
    if (pin1_silk is not None):
        kicad_mod.append(pin1_silk)

    if (fp_config.draw_pin1_marker_on_fab):
        pin1_fab_pnts = make_pin1_fab_marker_points(fp_config, configuration)
        # close polygon only if the closing line is not contained in the F.Fab outline
        if (not check_if_points_on_lines(kicad_mod, [pin1_fab_pnts[n] for n in [0, -1]], layer='F.Fab')):
            pin1_fab_pnts.append(pin1_fab_pnts[0])
        pin1_fab = PolygonLine(nodes=pin1_fab_pnts, layer='F.Fab', width=configuration['fab_line_width'])
        kicad_mod.append(pin1_fab)

    # calculate CourtYard
    cy_offset = fp_config.spec.get("courtyard_offset", configuration["courtyard_offset"]["connector"])
    courtyard = calculate_courtyard(bbox, offsets= cy_offset, configuration=configuration)
    # append CourtYard rectangle
    kicad_mod.append(RectLine(**courtyard, layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ## clean silk
    if (fp_config.spec.get("clean_silk", True)):
        silk_pad_clearance = fp_config.spec.get("silk_pad_clearance", configuration["silk_pad_clearance"])
        kicad_mod.cleanSilkMaskOverlap(side="F", silk_pad_clearance=silk_pad_clearance, silk_line_width=fp_config.silk_line_width)

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=fp_config.body_edges,
                  courtyard={
                      "left": courtyard["start"].x, "right": courtyard["end"].x,
                      "top": courtyard["start"].y, "bottom": courtyard["end"].y,
                  }, fp_name=fp_name, text_y_inside_position=0)

    lib_name = configuration['lib_name_specific_function_format_string'].format(category=fp_config.library_name)

    ## 3D model
    kicad_mod.append(Model(filename=f"{KICAD_3DMODEL_DIR}/{lib_name}.3dshapes/{fp_name}.wrl", at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(output_dir)
    filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=fp_name)

    # write file
    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)


def calculate_courtyard(bbox, offsets, configuration):
    # TODO: calculate courtyard from all nodes on specific layers
    courtyard = {"start": bbox["min"], "end": bbox["max"]}
    ## get CourtYard offset specification
    if (isinstance(offsets, (int, float))):
        cy_off = { k: Vector2D(offsets, offsets) for k in ["start", "end"] }
    elif isinstance(offsets, dict):
        cy_off = { k: Vector2D(0, 0) for k in ["start", "end"] }
        for e in ["start", "end"]:
            cy_off[e].x = offsets.get('x', configuration["courtyard_offset"]["connector"])
            cy_off[e].y = offsets.get('y', configuration["courtyard_offset"]["connector"])
        cy_off["start"].x = offsets.get("left", cy_off["start"].x)
        cy_off["start"].y = offsets.get("top", cy_off["start"].y)
        cy_off["end"].x = offsets.get("right", cy_off["end"].x)
        cy_off["end"].y = offsets.get("bottom", cy_off["end"].y)
    else:
        raise ValueError("invalid courtyard specification, must be a float or a dictionary")
    courtyard["start"] = Vector2D(*[_round_to(v - off, configuration["courtyard_grid"], '-')
                                    for v, off in zip(courtyard["start"], cy_off["start"])])
    courtyard["end"] = Vector2D(*[_round_to(v + off, configuration["courtyard_grid"], '+')
                                  for v, off in zip(courtyard["end"], cy_off["end"])])
    return courtyard


def make_pin1_marker(*, pos, radius, shape, flip_marker, width, offset):
    offset_vec = Vector2D(0, offset * (1 if flip_marker else -1))
    if (shape == "circle"):
        pin1_silk = Circle(center=pos - offset_vec, radius=radius, layer='F.SilkS', width=width)
    elif (shape == 'line'):
        line_midlength = Vector2D(radius, 0)
        pnts = [pos-offset_vec-line_midlength, pos-offset_vec+line_midlength]
        pin1_silk = PolygonLine(nodes=pnts, layer='F.SilkS', width=width)
    elif (shape == "triangle"):
        pnts = []
        for n in range(3):
            vertex = Vector2D(
                sin(2 * n * pi / 3),
                cos(2 * n * pi / 3) * (1 if flip_marker else -1)
            )
            pnts.append(pos - offset_vec + radius * vertex)
        pin1_silk = PolygonLine(nodes=pnts + pnts[:1], layer='F.SilkS', width=width)
    elif (shape):
        raise ValueError("invalid pin 1 marker shape '%s'" % shape)
    else:
        pin1_silk = None
    return pin1_silk


def check_if_points_on_lines(kicad_mod, points, layer):
    for node in kicad_mod:
        if (isinstance(node, PolygonLine) and node.layer == layer):
            for l in node.lineItems():
                if all(l.isPointOnSelf(p) for p in points):
                    return True
    return False


def make_pin1_fab_marker_points(fp_config: FPconfiguration, configuration: dict) -> list:
    # pin 1 on Fab is a triangle

    # location of the tip in x
    tip_x = -0.5 * (fp_config.pad_pos_range.x + fp_config.row_x_offset) + fp_config.pad_center_offset.x

    # width and height of the triangle
    dx = min(fp_config.pad_pitch, configuration['fab_pin1_marker_length'])
    dy = 0.8 * fp_config.scale_y * dx

    base_y = fp_config.body_edges[fp_config.pin1_pos]

    pnts = [
        Vector2D(tip_x - 0.5 * dx, base_y),
        Vector2D(tip_x, base_y - dy),
        Vector2D(tip_x + 0.5 * dx, base_y),
    ]
    return pnts


def clean_body_shape(body_shape_nodes):
    # Check if there are 3 points in the same line, and remove the center point
    max_index = len(body_shape_nodes)-3
    i = -1
    while i <= max_index and i+2 <=max_index:
        node_a = body_shape_nodes[i]
        node_b = body_shape_nodes[i+1]
        node_c = body_shape_nodes[i+2]
        node_changed = False
        # Check first if some points are the same, otherwise, point_is_on_segment wouldn't work properly.
        if node_a == node_b:
                del body_shape_nodes[i]
                i = i-1 # Reevaluate from the index before to remove duplicates
                node_changed = True
        elif node_b == node_c:
                del body_shape_nodes[i+1]
                i = i-1 # Reevaluate from the index before to remove duplicates
                node_changed = True
        elif node_a == node_c:
                warnings.warn(f"\nPiece of shape with zero thickness is removed: {body_shape_nodes[i]}, {body_shape_nodes[i+1]}, {body_shape_nodes[i+2]}.", Warning)
                del body_shape_nodes[i+1]
                i = i-1 # Reevaluate from the index before to remove duplicates
                node_changed = True
        elif point_is_on_segment(node_b, node_c, node_a):
                # If A between B and C
                del body_shape_nodes[i]
                node_changed = True
        elif point_is_on_segment(node_a, node_c, node_b):
                # If B between A and C
                del body_shape_nodes[i+1]
                node_changed = True
        elif point_is_on_segment(node_a, node_b, node_c):
                # If C between A and B
                del body_shape_nodes[i+2]
                node_changed = True
        if node_changed:
                i = i-1
                max_index = max_index-1
        i = i+1


def build_body_shape(body_spec: dict, *, fp_config: FPconfiguration):

    body_shapes = { }
    for side in ["left", "top", "right", "bottom"]:
        body_shapes[side] = parse_body_shape(body_spec, side=side, eval_expr=fp_config.expr_eval)
    ## create body shape as a polygon
    left = fp_config.body_edges['left']
    right = fp_config.body_edges['right']
    top = fp_config.body_edges['top']
    bot = fp_config.body_edges['bottom']
    body_shape_nodes = []
    # top left corner (eventually with pin 1 chamfer)
    if (fp_config.pin1_pos == "top" and fp_config.pin1_body_chamfer):
        body_shape_nodes.append(Vector2D(left, top + fp_config.pin1_body_chamfer))
        body_shape_nodes.append(Vector2D(left + fp_config.pin1_body_chamfer, top))
    else:
        body_shape_nodes.append(Vector2D(left, top))
    # top shape (eventually empty)
    body_shape_nodes += body_shapes["top"]
    # top right corner
    body_shape_nodes.append(Vector2D(right, top))
    # right shape (eventually empty)
    body_shape_nodes += body_shapes["right"]
    # bottom right corner
    body_shape_nodes.append(Vector2D(right, bot))
    # bottom shape (eventually empty)
    body_shape_nodes += body_shapes["bottom"]
    # bottom left corner (eventually with pin 1 chamfer)
    if (fp_config.pin1_pos == "bottom" and fp_config.pin1_body_chamfer):
        body_shape_nodes.append(Vector2D(left + fp_config.pin1_body_chamfer, bot))
        body_shape_nodes.append(Vector2D(left, bot - fp_config.pin1_body_chamfer))
    else:
        body_shape_nodes.append(Vector2D(left, bot))
    # left shape (eventually empty)
    body_shape_nodes += body_shapes["left"]

    clean_body_shape(body_shape_nodes)

    # close shape
    body_shape_nodes.append(body_shape_nodes[0])
    return body_shape_nodes


def add_mount_pad(kicad_mod, *, pad_pos_range, pad_spec, pad_center_offset, default_paste, row_x_offset):
    center_to_center = _get_dim("center", spec=pad_spec, dim="x", base=pad_pos_range.x, mult=2) + row_x_offset
    pad_pos_y = utils.as_list(_get_dim("center", spec=pad_spec, dim="y"))
    pad_props = PadProperties(pad_spec, default_paste=default_paste)
    pad_nums = utils.as_list(pad_spec.get('name', [""]))
    if isinstance(pad_nums, (str, int)):
        pad_nums = [pad_nums]
    if len(pad_nums) == 1:
        pad_nums = pad_nums * len(pad_pos_y)
    ends = pad_spec.get('ends', 'both')
    for end in ('left', 'right'):
        if (ends not in [end, 'both']):
            continue
        for num, y in zip(pad_nums, pad_pos_y):
            pad_pos = [{ 'left': -1, 'right': 1 }[end] * 0.5 * center_to_center + pad_center_offset.x, y + pad_center_offset.y]
            kicad_mod.append(Pad(at=pad_pos, number=num, **pad_props.as_args()))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../conn_config_KLCv3.yaml')
    parser.add_argument('--filter', type=str, nargs='?', default="*", help='filter footprints to generate (wildcard matching)')
    parser.add_argument('yaml_file', type=str, help='name of the configuration parameter file')
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.series_config, 'r') as config_stream:
        try:
            configuration.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.yaml_file, "r") as yaml_file:
        try:
            yaml_spec = yaml.safe_load(yaml_file)
        except yaml.YAMLError as exc:
            print(exc)

    dictInherit(yaml_spec)

    for variant, spec in yaml_spec.items():
        if variant == "defaults" or "fp_name" not in spec or not fnmatch(variant, args.filter):
            continue
        print("- %s:" % variant)
        list_of_positions = spec["positions"]
        if (isinstance(list_of_positions, str) and (match := re.match(r"^\s*\$\((.+)\)\s*$", list_of_positions))):
            list_of_positions = ASTexprEvaluator().eval(match[1])
        for idx, positions in enumerate(utils.as_list(list_of_positions)):
            generate_one_footprint(positions, idx=idx, spec=spec, configuration=configuration)
        print("")
