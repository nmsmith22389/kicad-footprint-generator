#!/usr/bin/env python3

import sys
import os
import argparse
import yaml
import math
from typing import List

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree

from KicadModTree import *  # NOQA
from KicadModTree.nodes.base.Pad import Pad
from KicadModTree.nodes.specialized.PadArray import PadArray, get_pad_radius_from_arrays
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields
from ipc_pad_size_calculators import *
from scripts.tools.geometry.bounding_box import BoundingBox
from scripts.tools.quad_dual_pad_border import create_dual_or_quad_pad_border
from scripts.tools.drawing_tools import nearestSilkPointOnOrthogonalLine, TriangleArrowPointingSouth, roundGDown, TriangleArrowPointingEast

sys.path.append(os.path.join(sys.path[0], "..", "utils"))
from ep_handling_utils import getEpRoundRadiusParams

from scripts.tools.dict_tools import dictInherit

ipc_density = 'nominal'
ipc_doc_file = '../ipc_definitions.yaml'

DEFAULT_PASTE_COVERAGE = 0.65
DEFAULT_VIA_PASTE_CLEARANCE = 0.15
DEFAULT_MIN_ANNULAR_RING = 0.15


def roundToBase(value, base):
    return round(value / base) * base

def find_top_left_pad(pad_arrays: List[PadArray]) -> Pad:
    """
    From a list of pad arrays, find the top-left pad.
    """

    def point_is_left_and_then_above(point: Vector2D, other_point: Vector2D) -> bool:

        # left-most wins if not the same
        if point.x == other_point.x:
            return point.y < other_point.y

        # in the same col, top wins
        return point.x < other_point.x

    tl_pad = None
    for pad_array in pad_arrays:
        for pad in pad_array:
            if tl_pad is None or point_is_left_and_then_above(pad.at, tl_pad.at):
                tl_pad = pad

    if tl_pad is None:
        raise ValueError("No pad found in pad array")

    return tl_pad

class Gullwing():
    def __init__(self, configuration):
        self.configuration = configuration
        with open(ipc_doc_file, 'r') as ipc_stream:
            try:
                self.ipc_defintions = yaml.safe_load(ipc_stream)

                self.configuration['min_ep_to_pad_clearance'] = 0.2

                # ToDo: find a settings file that can contain these.
                self.configuration['paste_radius_ratio'] = 0.25
                self.configuration['paste_maximum_radius'] = 0.25

                if 'ipc_generic_rules' in self.ipc_defintions:
                    self.configuration['min_ep_to_pad_clearance'] = self.ipc_defintions['ipc_generic_rules'].get(
                        'min_ep_to_pad_clearance', 0.2)

            except yaml.YAMLError as exc:
                print(exc)

    def calcPadDetails(self, device_dimensions, overrides, ipc_data, ipc_round_base):
        # Z - Length (overall) of the land pattern
        # G - Inside length distance between lands of the pattern
        # L - Component Length (edge to edge of the gullwings)
        # S - Distance between the inside edges of the gullwings
        # JT - Solder fillet at toe
        # JH - Solder fillet at heel
        # JS - Solder fillet at side
        # CL - Component Length tolerance
        # F - Fabrication tolerance
        # P - Placement tolerance
        # X - Width (overall) of the land pattern
        # W - Width of a lead

        # Zmax = Lmin + 2JT + √(CL^2 + F^2 + P^2)
        # Gmin = Smax − 2JH − √(CS^2 + F^2 + P^2)
        # Xmax = Wmin + 2JS + √(CW^2 + F^2 + P^2)

        # Some manufacturers do not list the terminal spacing (S) in their datasheet but list the terminal length (T)
        # Then one can calculate
        # Stol(RMS) = √(Ltol^2 + 2*^2)
        # Smin = Lmin - 2*Tmax
        # Smax(RMS) = Smin + Stol(RMS)

        manf_tol = {
            'F': self.configuration.get('manufacturing_tolerance', 0.1),
            'P': self.configuration.get('placement_tolerance', 0.05)
        }

        Gmin_x, Zmax_x, Xmax = ipc_gull_wing(
            ipc_data, ipc_round_base, manf_tol,
            device_dimensions['lead_width'],
            device_dimensions['overall_size_x'],
            lead_len=device_dimensions.get('lead_len'),
            heel_reduction=device_dimensions.get('heel_reduction', 0)
        )

        Gmin_y, Zmax_y, Xmax_y_ignored = ipc_gull_wing(
            ipc_data, ipc_round_base, manf_tol,
            device_dimensions['lead_width'],
            device_dimensions['overall_size_y'],
            lead_len=device_dimensions.get('lead_len'),
            heel_reduction=device_dimensions.get('heel_reduction', 0)
        )

        min_ep_to_pad_clearance = configuration['min_ep_to_pad_clearance']

        heel_reduction_max = 0

        if Gmin_x - 2 * min_ep_to_pad_clearance < overrides['EP_x']:
            heel_reduction_max = ((overrides['EP_x'] + 2 * min_ep_to_pad_clearance - Gmin_x) / 2)
            #print('{}, {}, {}'.format(Gmin_x, overrides['EP_x'], min_ep_to_pad_clearance))
            Gmin_x = overrides['EP_x'] + 2 * min_ep_to_pad_clearance
        if Gmin_y - 2 * min_ep_to_pad_clearance < overrides['EP_y']:
            heel_reduction = ((overrides['EP_y'] + 2 * min_ep_to_pad_clearance - Gmin_y) / 2)
            if heel_reduction > heel_reduction_max:
                heel_reduction_max = heel_reduction
            Gmin_y = overrides['EP_y'] + 2 * min_ep_to_pad_clearance

        if overrides['pad_to_pad_min_x'] > 0:
            Gmin_x = overrides['pad_to_pad_min_x']
            Zmax_x = overrides['pad_to_pad_max_x']

        if overrides['pad_to_pad_min_y'] > 0:
            Gmin_y = overrides['pad_to_pad_min_y']
            Zmax_y = overrides['pad_to_pad_max_y']

        if overrides['pad_size_y'] > 0:
            Xmax = overrides['pad_size_y']

        Pad = {}
        Pad['left'] = {'center': [-(Zmax_x + Gmin_x) / 4.0, 0], 'size': [(Zmax_x - Gmin_x) / 2.0, Xmax]}
        Pad['right'] = {'center': [(Zmax_x + Gmin_x) / 4.0, 0], 'size': [(Zmax_x - Gmin_x) / 2.0, Xmax]}
        Pad['top'] = {'center': [0, -(Zmax_y + Gmin_y) / 4.0], 'size': [Xmax, (Zmax_y - Gmin_y) / 2.0]}
        Pad['bottom'] = {'center': [0, (Zmax_y + Gmin_y) / 4.0], 'size': [Xmax, (Zmax_y - Gmin_y) / 2.0]}

        return Pad

    @staticmethod
    def deviceDimensions(device_size_data):
        dimensions = {
            'body_size_x': TolerancedSize.fromYaml(device_size_data, base_name='body_size_x'),
            'body_size_y': TolerancedSize.fromYaml(device_size_data, base_name='body_size_y'),
            'lead_width': TolerancedSize.fromYaml(device_size_data, base_name='lead_width'),
            'lead_len': TolerancedSize.fromYaml(device_size_data, base_name='lead_len')
        }
        dimensions['has_EP'] = False
        if 'EP_size_x_min' in device_size_data and 'EP_size_x_max' in device_size_data or 'EP_size_x' in device_size_data:
            dimensions['EP_size_x'] = TolerancedSize.fromYaml(device_size_data, base_name='EP_size_x')
            dimensions['EP_size_y'] = TolerancedSize.fromYaml(device_size_data, base_name='EP_size_y')
            dimensions['has_EP'] = True

        if 'EP_mask_x' in device_size_data:
            dimensions['EP_mask_x'] = TolerancedSize.fromYaml(device_size_data, base_name='EP_mask_x')
            dimensions['EP_mask_y'] = TolerancedSize.fromYaml(device_size_data, base_name='EP_mask_y')

        dimensions['heel_reduction'] = device_size_data.get('heel_reduction', 0)

        if 'overall_size_x' in device_size_data or 'overall_size_y' in device_size_data:
            if 'overall_size_x' in device_size_data:
                dimensions['overall_size_x'] = TolerancedSize.fromYaml(device_size_data, base_name='overall_size_x')
            else:
                dimensions['overall_size_x'] = TolerancedSize.fromYaml(device_size_data, base_name='overall_size_y')

            if 'overall_size_y' in device_size_data:
                dimensions['overall_size_y'] = TolerancedSize.fromYaml(device_size_data, base_name='overall_size_y')
            else:
                dimensions['overall_size_y'] = TolerancedSize.fromYaml(device_size_data, base_name='overall_size_x')
        else:
            raise KeyError("Either overall size x or overall size y must be given (Outside to outside lead dimensions)")

        return dimensions

    def generateFootprint(self, device_params, header):
        dimensions = Gullwing.deviceDimensions(device_params)

        if 'deleted_pins' in device_params:
            if type(device_params['deleted_pins']) is int:
                device_params['deleted_pins'] = [device_params['deleted_pins']]

        if 'hidden_pins' in device_params:
            if type(device_params['hidden_pins']) is int:
                device_params['hidden_pins'] = [device_params['hidden_pins']]

        if 'deleted_pins' in device_params and 'hidden_pins' in device_params:
            print("A footprint may not have deleted pins and hidden pins.")
        else:
            if dimensions['has_EP'] and 'thermal_vias' in device_params:
                self.__createFootprintVariant(device_params, header, dimensions, True)

            self.__createFootprintVariant(device_params, header, dimensions, False)

    def __createFootprintVariant(self, device_params, header, dimensions, with_thermal_vias):
        fab_line_width = self.configuration.get('fab_line_width', 0.1)
        silk_line_width = self.configuration.get('silk_line_width', 0.12)

        if 'override_lib_name' in header:
            lib_name = header['override_lib_name']
        else:
            lib_name = self.configuration['lib_name_format_string'].format(category=header['library_Suffix'])

        device_type = device_params.get('device_type', header['device_type'])

        size_x = dimensions['body_size_x'].nominal
        size_y = dimensions['body_size_y'].nominal

        pincount_full = device_params['num_pins_x'] * 2 + device_params['num_pins_y'] * 2

        if 'pin_count' in device_params:
            # If the pin count is explicitly given, we use that and don't adjust for hidden/deleted pins
            pincount_full = device_params['pin_count']
            pincount_text = '{}'.format(pincount_full)
            pincount = pincount_full
        elif 'hidden_pins' in device_params:
            pincount_text = '{}-{}'.format(pincount_full - len(device_params['hidden_pins']), pincount_full)
            pincount = pincount_full - len(device_params['hidden_pins'])
        elif 'deleted_pins' in device_params:
            pincount_text = '{}-{}'.format(pincount_full, pincount_full - len(device_params['deleted_pins']))
            pincount = pincount_full - len(device_params['deleted_pins'])
        else:
            pincount_text = '{}'.format(pincount_full)
            pincount = pincount_full

        ipc_reference = 'ipc_spec_gw_large_pitch' if device_params['pitch'] >= 0.625 else 'ipc_spec_gw_small_pitch'
        if device_params.get('force_small_pitch_ipc_definition', False):
            ipc_reference = 'ipc_spec_gw_small_pitch'

        used_density = device_params.get('ipc_density', ipc_density)
        ipc_data_set = self.ipc_defintions[ipc_reference][used_density]
        ipc_round_base = self.ipc_defintions[ipc_reference]['round_base']

        pitch = device_params['pitch']

        name_format = self.configuration['fp_name_format_string_no_trailing_zero_pincount_text']
        EP_size = {'x': 0, 'y': 0}
        EP_mask_size = {'x': 0, 'y': 0}

        if dimensions['has_EP']:
            name_format = self.configuration['fp_name_EP_format_string_no_trailing_zero_pincount_text']
            if 'EP_size_x_overwrite' in device_params:
                EP_size = {
                    'x': device_params['EP_size_x_overwrite'],
                    'y': device_params['EP_size_y_overwrite']
                }
            else:
                EP_size = {
                    'x': dimensions['EP_size_x'].nominal,
                    'y': dimensions['EP_size_y'].nominal
                }
            if 'EP_mask_x' in dimensions:
                name_format = self.configuration['fp_name_EP_custom_mask_format_string_no_trailing_zero_pincount_text']
                EP_mask_size = {'x': dimensions['EP_mask_x'].nominal, 'y': dimensions['EP_mask_y'].nominal}

        overrides = {
            'EP_x' : 0,
            'EP_y' : 0,
            'pad_to_pad_min_x' : 0,
            'pad_to_pad_max_x' : 0,
            'pad_to_pad_min_y' : 0,
            'pad_to_pad_max_y' : 0,
            'pad_size_y' : 0
        }

        if 'pad_size_y_overwrite' in device_params:
            overrides['pad_size_y'] = device_params['pad_size_y_overwrite']

        if 'pad_to_pad_min_x_overwrite' in device_params:
            overrides['pad_to_pad_min_x'] = device_params['pad_to_pad_min_x_overwrite']
            overrides['pad_to_pad_max_x'] = device_params['pad_to_pad_max_x_overwrite']

        if 'pad_to_pad_min_y_overwrite' in device_params:
            overrides['pad_to_pad_min_y'] = device_params['pad_to_pad_min_y_overwrite']
            overrides['pad_to_pad_max_y'] = device_params['pad_to_pad_max_y_overwrite']

        overrides['EP_x'] = EP_size['x']
        overrides['EP_y'] = EP_size['y']

        EP_size = Vector2D(EP_size)

        pad_details = self.calcPadDetails(dimensions, overrides, ipc_data_set, ipc_round_base)

        if 'custom_name_format' in device_params:
            name_format = device_params['custom_name_format']

        suffix = device_params.get('suffix', '').format(pad_x=pad_details['left']['size'][0],
                                                        pad_y=pad_details['left']['size'][1])
        suffix_3d = suffix if device_params.get('include_suffix_in_3dpath', 'True') == 'True' else ""
        model3d_path_prefix = self.configuration.get('3d_model_prefix', '${KICAD7_3DMODEL_DIR}')

        fp_name = name_format.format(
            man=device_params.get('manufacturer', ''),
            mpn=device_params.get('part_number', ''),
            pkg=device_type,
            pincount=pincount_text,
            size_y=size_y,
            size_x=size_x,
            pitch=device_params['pitch'],
            ep_size_x=EP_size['x'],
            ep_size_y=EP_size['y'],
            mask_size_x=EP_mask_size['x'],
            mask_size_y=EP_mask_size['y'],
            suffix=suffix,
            suffix2="",
            vias=self.configuration.get('thermal_via_suffix', '_ThermalVias') if with_thermal_vias else ''
        ).replace('__', '_').lstrip('_')

        fp_name_2 = name_format.format(
            man=device_params.get('manufacturer', ''),
            mpn=device_params.get('part_number', ''),
            pkg=device_type,
            pincount=pincount_text,
            size_y=size_y,
            size_x=size_x,
            pitch=device_params['pitch'],
            ep_size_x=EP_size['x'],
            ep_size_y=EP_size['y'],
            mask_size_x=EP_mask_size['x'],
            mask_size_y=EP_mask_size['y'],
            suffix=suffix_3d,
            suffix2="",
            vias=''
        ).replace('__', '_').lstrip('_')

        model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'\
            .format(
                model3d_path_prefix=model3d_path_prefix, lib_name=lib_name,
                fp_name=fp_name_2)
        # print(fp_name)
        # print(pad_details)

        kicad_mod = Footprint(fp_name, FootprintType.SMD)

        # init kicad footprint
        kicad_mod.setDescription(
            "{manufacturer} {mpn} {package}, {pincount} Pin ({datasheet}), generated with kicad-footprint-generator {scriptname}"
            .format(
                manufacturer=device_params.get('manufacturer', ''),
                package=device_type,
                mpn=device_params.get('part_number', ''),
                pincount=pincount,
                datasheet=device_params['size_source'],
                scriptname=os.path.basename(__file__).replace("  ", " ")
            ).lstrip())

        kicad_mod.setTags(self.configuration['keyword_fp_string']
                          .format(
            man=device_params.get('manufacturer', ''),
            package=device_type,
            category=header['override_lib_name'] if 'override_lib_name' in header else header['library_Suffix']
        ).lstrip())

        if 'custom_pad_layout' in device_params:
            pad_arrays = create_custom_pad_layout(configuration, pad_details, device_params)
        else:
            pad_arrays = create_dual_or_quad_pad_border(configuration, pad_details, device_params)

        for pad_array in pad_arrays:
            kicad_mod.append(pad_array)

        tl_pad = find_top_left_pad(pad_arrays)
        pad_radius = get_pad_radius_from_arrays(pad_arrays)

        EP_round_radius = 0
        if dimensions['has_EP']:
            pad_shape_details = getEpRoundRadiusParams(device_params, self.configuration, pad_radius)
            EP_mask_size = EP_mask_size if EP_mask_size['x'] > 0 else None

            if with_thermal_vias:
                thermals = device_params['thermal_vias']
                paste_coverage = thermals.get('EP_paste_coverage',
                                              device_params.get('EP_paste_coverage', DEFAULT_PASTE_COVERAGE))

                EP = ExposedPad(
                    number=pincount + 1, size=EP_size, mask_size=EP_mask_size,
                    paste_layout=thermals.get('EP_num_paste_pads'),
                    paste_coverage=paste_coverage,
                    via_layout=thermals.get('count', 0),
                    paste_between_vias=thermals.get('paste_between_vias'),
                    paste_rings_outside=thermals.get('paste_rings_outside'),
                    via_drill=thermals.get('drill', 0.3),
                    via_grid=thermals.get('grid'),
                    paste_avoid_via=thermals.get('paste_avoid_via', True),
                    via_paste_clarance=thermals.get('paste_via_clearance', DEFAULT_VIA_PASTE_CLEARANCE),
                    min_annular_ring=thermals.get('min_annular_ring', DEFAULT_MIN_ANNULAR_RING),
                    bottom_pad_min_size=thermals.get('bottom_min_size', 0),
                    **pad_shape_details
                )
            else:
                EP = ExposedPad(
                    number=pincount + 1, size=EP_size, mask_size=EP_mask_size,
                    paste_layout=device_params.get('EP_num_paste_pads', 1),
                    paste_coverage=device_params.get('EP_paste_coverage', DEFAULT_PASTE_COVERAGE),
                    **pad_shape_details
                )

            kicad_mod.append(EP)
            EP_round_radius = EP.getRoundRadius()

        body_edge = {
            'left': -dimensions['body_size_x'].nominal / 2,
            'right': dimensions['body_size_x'].nominal / 2,
            'top': -dimensions['body_size_y'].nominal / 2,
            'bottom': dimensions['body_size_y'].nominal / 2
        }

        bounding_box = {
            'left': pad_details['left']['center'][0] - pad_details['left']['size'][0] / 2,
            'right': pad_details['right']['center'][0] + pad_details['right']['size'][0] / 2,
            'top': pad_details['top']['center'][1] - pad_details['top']['size'][1] / 2,
            'bottom': pad_details['bottom']['center'][1] + pad_details['bottom']['size'][1] / 2
        }

        if device_params['num_pins_x'] == 0:
            bounding_box['top'] = body_edge['top']
            bounding_box['bottom'] = body_edge['bottom']
            if EP_size['y'] > dimensions['body_size_y'].nominal:
                bounding_box['top'] = -EP_size['y'] / 2
                bounding_box['bottom'] = EP_size['y'] / 2

        if device_params['num_pins_y'] == 0:
            bounding_box['left'] = body_edge['left']
            bounding_box['right'] = body_edge['right']
            if EP_size['x'] > dimensions['body_size_x'].nominal:
                bounding_box['left'] = -EP_size['x'] / 2
                bounding_box['right'] = EP_size['x'] / 2

        pad_width = pad_details['top']['size'][0]

        # # ############################ CrtYd ##################################

        courtyard_offset = ipc_data_set['courtyard']
        courtyard_grid = configuration['courtyard_grid']

        def make_courtyard_bbox():
            cy_t = roundToBase(bounding_box['top'] - courtyard_offset, courtyard_grid)
            cy_l = roundToBase(bounding_box['left'] - courtyard_offset, courtyard_grid)
            cy_r = roundToBase(bounding_box['right'] + courtyard_offset, courtyard_grid)
            cy_b = roundToBase(bounding_box['bottom'] + courtyard_offset, courtyard_grid)

            return BoundingBox(
                min_pt=Vector2D(cy_l, cy_t),
                max_pt=Vector2D(cy_r, cy_b)
            )

        courtyard_bbox = make_courtyard_bbox()

        if device_params['num_pins_y'] == 0 or device_params['num_pins_x'] == 0:
            # Dual pin-row devices - simple rectangle at the bounding box

            kicad_mod.append(RectLine(
                start=courtyard_bbox.min,
                end=courtyard_bbox.max,
                width=configuration['courtyard_line_width'],
                layer='F.CrtYd'))
        else:
            # QFP
            cy1 = courtyard_bbox.top
            cy2 = roundToBase(body_edge['top'] - courtyard_offset, courtyard_grid)
            cy3 = -roundToBase(
                device_params['pitch'] * (device_params['num_pins_y'] - 1) / 2.0 +
                pad_width / 2.0 + courtyard_offset, courtyard_grid)

            cx1 = -roundToBase(
                device_params['pitch'] * (device_params['num_pins_x'] - 1) / 2.0 +
                pad_width / 2.0 + courtyard_offset, courtyard_grid)
            cx2 = roundToBase(body_edge['left'] - courtyard_offset, courtyard_grid)
            cx3 = courtyard_bbox.left

            crty_poly_tl = [
                {'x': 0, 'y': cy1},
                {'x': cx1, 'y': cy1},
                {'x': cx1, 'y': cy2},
                {'x': cx2, 'y': cy2},
                {'x': cx2, 'y': cy3},
                {'x': cx3, 'y': cy3},
                {'x': cx3, 'y': 0}
            ]
            kicad_mod.append(PolygonLine(polygon=crty_poly_tl,
                                         layer='F.CrtYd', width=configuration['courtyard_line_width']))
            kicad_mod.append(PolygonLine(polygon=crty_poly_tl,
                                         layer='F.CrtYd', width=configuration['courtyard_line_width'],
                                         x_mirror=0))
            kicad_mod.append(PolygonLine(polygon=crty_poly_tl,
                                         layer='F.CrtYd', width=configuration['courtyard_line_width'],
                                         y_mirror=0))
            kicad_mod.append(PolygonLine(polygon=crty_poly_tl,
                                         layer='F.CrtYd', width=configuration['courtyard_line_width'],
                                         x_mirror=0, y_mirror=0))

        # ############################ SilkS ##################################
        silk_pad_clearance = configuration['silk_pad_clearance']
        silk_line_width = configuration['silk_line_width']
        silk_pad_offset = silk_pad_clearance + (silk_line_width / 2)
        silk_offset = configuration['silk_fab_offset']

        right_pads_silk_bottom = (device_params['num_pins_y'] - 1) * device_params['pitch'] / 2\
            + pad_details['right']['size'][1] / 2 + silk_pad_offset
        silk_bottom = body_edge['bottom'] + silk_offset
        if EP_size['y'] / 2 <= body_edge['bottom'] and right_pads_silk_bottom >= silk_bottom:
            silk_bottom = max(silk_bottom, EP_size['y'] / 2 + silk_pad_offset)

        silk_bottom = max(silk_bottom, right_pads_silk_bottom)
        silk_bottom = min(body_edge['bottom'] + silk_pad_offset, silk_bottom)

        bottom_pads_silk_right = (device_params['num_pins_x'] - 1) * device_params['pitch'] / 2\
            + pad_details['bottom']['size'][0] / 2 + silk_pad_offset
        silk_right = body_edge['right'] + silk_offset
        if EP_size['x'] / 2 <= body_edge['right'] and bottom_pads_silk_right >= silk_right:
            silk_right = max(silk_right, EP_size['x'] / 2 + silk_pad_offset)
        silk_right = max(silk_right, bottom_pads_silk_right)
        silk_right = min(body_edge['right'] + silk_pad_offset, silk_right)

        min_length = configuration.get('silk_line_length_min', 0)
        silk_corner_bottom_right = Vector2D(silk_right, silk_bottom)

        silk_point_bottom_inside = nearestSilkPointOnOrthogonalLine(
            pad_size=EP_size,
            pad_position=[0, 0],
            pad_radius=EP_round_radius,
            fixed_point=silk_corner_bottom_right,
            moving_point=Vector2D(0, silk_bottom),
            silk_pad_offset=silk_pad_offset,
            min_length=min_length)

        if silk_point_bottom_inside is not None and device_params['num_pins_x'] > 0:
            silk_point_bottom_inside = nearestSilkPointOnOrthogonalLine(
                pad_size=pad_details['bottom']['size'],
                pad_position=[
                    pad_details['bottom']['center'][0] + (device_params['num_pins_x'] - 1) / 2 * pitch,
                    pad_details['bottom']['center'][1]],
                pad_radius=pad_radius,
                fixed_point=silk_corner_bottom_right,
                moving_point=silk_point_bottom_inside,
                silk_pad_offset=silk_pad_offset,
                min_length=min_length)

        silk_point_right_inside = nearestSilkPointOnOrthogonalLine(
            pad_size=EP_size,
            pad_position=[0, 0],
            pad_radius=EP_round_radius,
            fixed_point=silk_corner_bottom_right,
            moving_point=Vector2D(silk_right, 0),
            silk_pad_offset=silk_pad_offset,
            min_length=min_length)
        if silk_point_right_inside is not None and device_params['num_pins_y'] > 0:
            silk_point_right_inside = nearestSilkPointOnOrthogonalLine(
                pad_size=pad_details['right']['size'],
                pad_position=[
                    pad_details['right']['center'][0],
                    pad_details['right']['center'][1] + (device_params['num_pins_y'] - 1) / 2 * pitch],
                pad_radius=pad_radius,
                fixed_point=silk_corner_bottom_right,
                moving_point=silk_point_right_inside,
                silk_pad_offset=silk_pad_offset,
                min_length=min_length)

        if silk_point_bottom_inside is None and silk_point_right_inside is not None:
            silk_corner_bottom_right['y'] = body_edge['bottom']
            silk_corner_bottom_right = nearestSilkPointOnOrthogonalLine(
                pad_size=pad_details['bottom']['size'],
                pad_position=[
                    pad_details['bottom']['center'][0] + (device_params['num_pins_x'] - 1) / 2 * pitch,
                    pad_details['bottom']['center'][1]],
                pad_radius=pad_radius,
                fixed_point=silk_point_right_inside,
                moving_point=silk_corner_bottom_right,
                silk_pad_offset=silk_pad_offset,
                min_length=min_length)

        elif silk_point_right_inside is None and silk_point_bottom_inside is not None:
            silk_corner_bottom_right['x'] = body_edge['right']
            silk_corner_bottom_right = nearestSilkPointOnOrthogonalLine(
                pad_size=pad_details['right']['size'],
                pad_position=[
                    pad_details['right']['center'][0],
                    pad_details['right']['center'][1] + (device_params['num_pins_y'] - 1) / 2 * pitch],
                pad_radius=pad_radius,
                fixed_point=silk_point_bottom_inside,
                moving_point=silk_corner_bottom_right,
                silk_pad_offset=silk_pad_offset,
                min_length=min_length)

        poly_bottom_right = []
        if silk_point_bottom_inside is not None:
            poly_bottom_right.append(silk_point_bottom_inside)
        poly_bottom_right.append(silk_corner_bottom_right)
        if silk_point_right_inside is not None:
            poly_bottom_right.append(silk_point_right_inside)

        is_qfp = device_params['num_pins_x'] > 0 and device_params['num_pins_y'] > 0

        min_pad_dimension = min(tl_pad.size.x, tl_pad.size.y)

        #  default to half the pitch, but not less than min_arrow_size
        min_arrow_size = silk_line_width * 3
        max_arrow_size = 1.0 - silk_line_width
        arrow_size = min(max_arrow_size,
                         max(min_pad_dimension - silk_line_width, min_arrow_size))

        # QFPs have more space in the corners - make the arrow bigger
        if is_qfp:
            arrow_size *= 1.3

        arrow_aspect_ratio = 0.7
        arrow_length = arrow_size * arrow_aspect_ratio

        # poly_bottom_right is used 4 times in all mirror configurations
        if len(poly_bottom_right) > 1 and silk_corner_bottom_right is not None:
            kicad_mod.append(PolygonLine(
                polygon=poly_bottom_right,
                width=silk_line_width,
                layer="F.SilkS"))
            kicad_mod.append(PolygonLine(
                polygon=poly_bottom_right,
                width=silk_line_width,
                layer="F.SilkS", x_mirror=0))
            kicad_mod.append(PolygonLine(
                polygon=poly_bottom_right,
                width=silk_line_width,
                layer="F.SilkS", y_mirror=0))
            kicad_mod.append(PolygonLine(
                polygon=poly_bottom_right,
                width=silk_line_width,
                layer="F.SilkS", y_mirror=0, x_mirror=0))

            # The edges of the pad clearance area
            tl_pad_with_clearance_top = tl_pad.at.y - tl_pad.size.y / 2 - silk_pad_clearance
            tl_pad_with_clearance_left = tl_pad.at.x - tl_pad.size.x / 2 - silk_pad_clearance

            # Allow a top-down arrow if there is enough space between the top pad and the courtyard
            # (it is allowed to overlap the courtyard by the courtyard offset, as a neigbouring part
            # with touching courtyards will nearly always have the same offset for itself, giving
            # our arrow a place. And the arrow is directional, so it's clear which part it belongs
            # to.)
            arrow_permitted_spill_over_top_courtyard = courtyard_offset
            minimum_space_to_fit_arrow = arrow_length + silk_line_width - arrow_permitted_spill_over_top_courtyard

            # we need a different arrow depending on the device orientation
            if device_params['num_pins_y'] > 0:
                # Pins on the left and right side

                pad_to_courtyard_corner_gap = tl_pad_with_clearance_top - courtyard_bbox.top
                tl_pad_left = tl_pad.at.x - tl_pad.size.x / 2

                # For parts like J-lead/SOJ, there may be no pad extending out past the body
                # so no left-right space to fit an arrow
                left_right_space = body_edge['left'] - tl_pad_left
                south_arrow_fits = left_right_space >= arrow_size

                if (south_arrow_fits and
                        (is_qfp or (pad_to_courtyard_corner_gap >= minimum_space_to_fit_arrow))):
                    # We can fit an arrow in the courtyard, or it's a QFN

                    pad_left_body_left_midpoint = (tl_pad_left + body_edge['left']) / 2

                    # put a down arrow top of pin1
                    arrow_apex = Vector2D(pad_left_body_left_midpoint,
                                          tl_pad_with_clearance_top - silk_line_width / 2)
                    TriangleArrowPointingSouth(kicad_mod, arrow_apex, arrow_size, arrow_length,
                                               "F.SilkS", silk_line_width)
                else:
                    # put a East arrow left of pin1
                    arrow_apex = Vector2D(tl_pad_with_clearance_left - silk_line_width / 2,
                                          tl_pad.at.y)
                    TriangleArrowPointingEast(kicad_mod, arrow_apex, arrow_size, arrow_length,
                                              "F.SilkS", silk_line_width)

            else:
                # Pins on the top and bottom side

                pad_to_courtyard_corner_gap = tl_pad_with_clearance_left - courtyard_bbox.left

                # J-lead type parts
                tl_pad_top = tl_pad.at.y - tl_pad.size.y / 2
                top_bottom_space = body_edge['top'] - tl_pad_top
                east_arrow_fits = top_bottom_space >= arrow_size

                if east_arrow_fits and pad_to_courtyard_corner_gap >= minimum_space_to_fit_arrow:
                    pad_top_body_top_midpoint = (tl_pad_top + body_edge['top']) / 2

                    arrow_apex = Vector2D(tl_pad_with_clearance_left - silk_line_width / 2,
                                          pad_top_body_top_midpoint)
                    TriangleArrowPointingEast(kicad_mod, arrow_apex, arrow_size, arrow_length,
                                              "F.SilkS", silk_line_width)
                else:
                    # put a down arrow top of pin1
                    arrow_apex = Vector2D(tl_pad.at.x,
                                          tl_pad_with_clearance_top - silk_line_width / 2)
                    TriangleArrowPointingSouth(kicad_mod, arrow_apex, arrow_size, arrow_length,
                                               "F.SilkS", silk_line_width)

        # # ######################## Fabrication Layer ###########################

        fab_bevel_size = min(configuration['fab_bevel_size_absolute'],
                             configuration['fab_bevel_size_relative'] * min(size_x, size_y))

        poly_fab = [
            {'x': body_edge['left'] + fab_bevel_size, 'y': body_edge['top']},
            {'x': body_edge['right'], 'y': body_edge['top']},
            {'x': body_edge['right'], 'y': body_edge['bottom']},
            {'x': body_edge['left'], 'y': body_edge['bottom']},
            {'x': body_edge['left'], 'y': body_edge['top'] + fab_bevel_size},
            {'x': body_edge['left'] + fab_bevel_size, 'y': body_edge['top']},
        ]

        kicad_mod.append(PolygonLine(
            polygon=poly_fab,
            width=configuration['fab_line_width'],
            layer="F.Fab"))

        # ######################### Text Fields ###############################

        addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
                      courtyard={'top': courtyard_bbox.top, 'bottom': courtyard_bbox.bottom},
                      fp_name=fp_name, text_y_inside_position='center')

        ##################### Output and 3d model ############################

        kicad_mod.append(Model(filename=model_name))

        output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
        if not os.path.isdir(output_dir):  # returns false if path does not yet exist!! (Does not check path validity)
            os.makedirs(output_dir)
        filename = '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=fp_name)

        file_handler = KicadFileHandler(kicad_mod)
        file_handler.writeFile(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='use confing .yaml files to create footprints. See readme.md for details about the parameter file format.')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of files holding information about what devices should be created.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)',
                        default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?',
                        help='the config file defining series parameters.', default='../package_config_KLCv3.yaml')
    parser.add_argument('--density', type=str, nargs='?', help='IPC density level (L,N,M)', default='N')
    parser.add_argument('--ipc_doc', type=str, nargs='?', help='IPC definition document',
                        default='../ipc_definitions.yaml')
    parser.add_argument('--force_rectangle_pads', action='store_true',
                        help='Force the generation of rectangle pads instead of rounded rectangle')
    parser.add_argument('--kicad4_compatible', action='store_true',
                        help='Create footprints compatible with version 4 (avoids round-rect and custom pads).')
    args = parser.parse_args()

    if args.density == 'L':
        ipc_density = 'least'
    elif args.density == 'M':
        ipc_density = 'most'

    ipc_doc_file = args.ipc_doc

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

    if args.force_rectangle_pads or args.kicad4_compatible:
        configuration['round_rect_max_radius'] = None
        configuration['round_rect_radius_ratio'] = 0

    configuration['kicad4_compatible'] = args.kicad4_compatible

    for filepath in args.files:
        gw = Gullwing(configuration)

        with open(filepath, 'r') as command_stream:
            try:
                cmd_file = yaml.safe_load(command_stream)
            except yaml.YAMLError as exc:
                print(exc)

        dictInherit(cmd_file)

        header = cmd_file.pop('FileHeader')

        for pkg in cmd_file:
            print("generating part for parameter set {}".format(pkg))
            gw.generateFootprint(cmd_file[pkg], header)
