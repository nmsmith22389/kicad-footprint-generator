#!/usr/bin/env python3

import sys
import os
import argparse
import yaml
from math import sqrt
from typing import List

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree

from KicadModTree import Vector2D, Footprint, FootprintType, ExposedPad, Line, \
    PolygonLine, RectLine, Model, Pad, KicadFileHandler
from KicadModTree.nodes.specialized.PadArray import PadArray, get_pad_radius_from_arrays

from scripts.tools.footprint_text_fields import addTextFields
from scripts.tools.ipc_pad_size_calculators import TolerancedSize, \
        ipc_body_edge_inside_pull_back, ipc_pad_center_plus_size
from scripts.tools.quad_dual_pad_border import create_dual_or_quad_pad_border
from scripts.tools import drawing_tools
from scripts.tools.drawing_tools import courtyardFromBoundingBox, roundGDown
from scripts.tools.geometry.bounding_box import BoundingBox
from scripts.tools.declarative_def_tools import tags_properties

sys.path.append(os.path.join(sys.path[0], "..", "utils"))
from ep_handling_utils import getEpRoundRadiusParams

ipc_density = 'nominal'
ipc_doc_file = '../ipc_definitions.yaml'
category = 'NoLead'
default_library = 'Package_DFN_QFN'

DEFAULT_PASTE_COVERAGE = 0.65
DEFAULT_VIA_PASTE_CLEARANCE = 0.15
DEFAULT_MIN_ANNULAR_RING = 0.15

SILK_MIN_LEN = 0.1

DEBUG_LEVEL = 0


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


def get_pad_top_left_corner_midpoint(pad: Pad) -> Vector2D:
    """Get the midpoint of the top left corner of the pad

    When the pad has no radius, this _is_ the corner.
    """

    tl_corner = None

    if pad.shape == Pad.SHAPE_RECT:
        tl_corner = pad.at - (pad.size / 2)
    elif pad.shape == Pad.SHAPE_ROUNDRECT:
        tl_corner = pad.at - (pad.size / 2)

        # Move into the corner slightly down and right to account for the radius
        # being on the inside of the bounding box, not the corner.
        inset = (1 - (sqrt(2) / 2)) * pad.roundRadius
        tl_corner += [inset, inset]
    else:
        raise ValueError("Unsupported pad shape: {}".format(pad.shape))

    assert (tl_corner is not None)

    return tl_corner


def get_pad_bounding_box(pad: Pad) -> BoundingBox:

    if pad.shape in [Pad.SHAPE_RECT, Pad.SHAPE_ROUNDRECT, Pad.SHAPE_CIRCLE, Pad.SHAPE_OVAL]:

        # This code doesn't handle this yet
        if (pad.rotation % 180) > 1e-6:
            raise ValueError("Rotation of pad is not a multiple of 180 degrees")

        return BoundingBox(
            min_pt=pad.at - (pad.size / 2),
            max_pt=pad.at + (pad.size / 2)
        )
    else:
        raise ValueError("Unsupported pad shape: {}".format(pad.shape))


def get_bounding_box_of_pad_arrays(pad_arrays: List[PadArray]) -> BoundingBox:
    """Get the bounding box of a list of pad arrays"""

    bb = None
    for pad_array in pad_arrays:
        for pad in pad_array:
            pad_bb = get_pad_bounding_box(pad)

            if bb is None:
                bb = pad_bb
            else:
                bb.include_bbox(pad_bb)

    if bb is None:
        raise ValueError("No pad found in pad array")

    return bb


class NoLeadConfiguration:
    """
    A type that represents the configuration of a gullwing footprint
    (probably from a YAML config block).

    Over time, add more type-safe accessors to this class, and replace
    use of the raw dictionary.
    """
    _spec_dictionary: dict
    compatible_mpns: tags_properties.TagsProperties
    additional_tags: tags_properties.TagsProperties

    def __init__(self, spec: dict):
        self._spec_dictionary = spec

        self.compatible_mpns = tags_properties.TagsProperties(
                spec.get('compatible_mpns', [])
        )

        # Generic addtional tags
        self.additional_tags = tags_properties.TagsProperties(
            spec.get(tags_properties.ADDITIONAL_TAGS_KEY, [])
        )

    @property
    def spec_dictionary(self) -> dict:
        return self._spec_dictionary


class NoLead():
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

    def calcPadDetails(self, device_dimensions, EP_size, ipc_data, ipc_round_base):
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

        pull_back_0 = TolerancedSize(nominal=0)
        pull_back = device_dimensions.get('lead_to_edge', pull_back_0)

        if 'lead_center_pos_x' in device_dimensions or 'lead_center_pos_y' in device_dimensions:
            Gmin_x, Zmax_x, Xmax_x = ipc_pad_center_plus_size(ipc_data, ipc_round_base, manf_tol,
                                                              center_position=device_dimensions.get(
                                                                'lead_center_pos_x', TolerancedSize(nominal=0)),
                                                              lead_length=device_dimensions.get('lead_len_H'),
                                                              lead_width=device_dimensions['lead_width_H'])

            Gmin_y, Zmax_y, Xmax_y = ipc_pad_center_plus_size(ipc_data, ipc_round_base, manf_tol,
                                                              center_position=device_dimensions.get(
                                                                'lead_center_pos_y', TolerancedSize(nominal=0)),
                                                              lead_length=device_dimensions.get('lead_len_V'),
                                                              lead_width=device_dimensions['lead_width_V'])
        else:
            Gmin_x, Zmax_x, Xmax_x = ipc_body_edge_inside_pull_back(
                ipc_data, ipc_round_base, manf_tol,
                body_size=device_dimensions['body_size_x'],
                lead_width=device_dimensions['lead_width_H'],
                lead_len=device_dimensions.get('lead_len_H'),
                body_to_inside_lead_edge=device_dimensions.get('body_to_inside_lead_edge'),
                heel_reduction=device_dimensions.get('heel_reduction', 0),
                pull_back=pull_back
            )

            Gmin_y, Zmax_y, Xmax_y = ipc_body_edge_inside_pull_back(
                ipc_data, ipc_round_base, manf_tol,
                body_size=device_dimensions['body_size_y'],
                lead_width=device_dimensions['lead_width_V'],
                lead_len=device_dimensions.get('lead_len_V'),
                body_to_inside_lead_edge=device_dimensions.get('body_to_inside_lead_edge'),
                heel_reduction=device_dimensions.get('heel_reduction', 0),
                pull_back=pull_back
            )

        min_ep_to_pad_clearance = self.configuration['min_ep_to_pad_clearance']

        heel_reduction_max = 0

        if Gmin_x - 2 * min_ep_to_pad_clearance < EP_size['x']:
            heel_reduction_max = ((EP_size['x'] + 2 * min_ep_to_pad_clearance - Gmin_x) / 2)
            # print('{}, {}, {}'.format(Gmin_x, EP_size['x'], min_ep_to_pad_clearance))
            Gmin_x = EP_size['x'] + 2 * min_ep_to_pad_clearance
        if Gmin_y - 2 * min_ep_to_pad_clearance < EP_size['y']:
            heel_reduction = ((EP_size['y'] + 2 * min_ep_to_pad_clearance - Gmin_y) / 2)
            if heel_reduction > heel_reduction_max:
                heel_reduction_max = heel_reduction
            Gmin_y = EP_size['y'] + 2 * min_ep_to_pad_clearance

        heel_reduction_max += device_dimensions.get('heel_reduction', 0)  # include legacy stuff
        if heel_reduction_max > 0 and DEBUG_LEVEL >= 1:
            print('Heel reduced by {:.4f} to reach minimum EP to pad clearances'.format(heel_reduction_max))

        Pad = {}
        Pad['left'] = {'center': [-(Zmax_x + Gmin_x) / 4, 0], 'size': [(Zmax_x - Gmin_x) / 2, Xmax_x]}
        Pad['right'] = {'center': [(Zmax_x + Gmin_x) / 4, 0], 'size': [(Zmax_x - Gmin_x) / 2, Xmax_x]}
        Pad['top'] = {'center': [0, -(Zmax_y + Gmin_y) / 4], 'size': [Xmax_y, (Zmax_y - Gmin_y) / 2]}
        Pad['bottom'] = {'center': [0, (Zmax_y + Gmin_y) / 4], 'size': [Xmax_y, (Zmax_y - Gmin_y) / 2]}

        return Pad

    @staticmethod
    def deviceDimensions(device_config: NoLeadConfiguration, fp_id: str) -> dict:
        # Pull out the old-style raw data
        device_size_data = device_config.spec_dictionary

        unit = device_size_data.get('unit')
        dimensions = {
            'body_size_x': TolerancedSize.fromYaml(device_size_data, base_name='body_size_x', unit=unit),
            'body_size_y': TolerancedSize.fromYaml(device_size_data, base_name='body_size_y', unit=unit)
        }

        if 'pitch_x' in device_size_data and 'pitch_y' in device_size_data:
            dimensions['pitch_x'] = TolerancedSize.fromYaml(device_size_data, base_name='pitch_x', unit=unit).nominal
            dimensions['pitch_y'] = TolerancedSize.fromYaml(device_size_data, base_name='pitch_y', unit=unit).nominal
        else:
            dimensions['pitch_x'] = TolerancedSize.fromYaml(device_size_data, base_name='pitch', unit=unit).nominal
            dimensions['pitch_y'] = dimensions['pitch_x']

        dimensions['has_EP'] = False
        if ('EP_size_x_min' in device_size_data and 'EP_size_x_max' in device_size_data
                or 'EP_size_x' in device_size_data):
            dimensions['EP_size_x'] = TolerancedSize.fromYaml(device_size_data, base_name='EP_size_x', unit=unit)
            dimensions['EP_size_y'] = TolerancedSize.fromYaml(device_size_data, base_name='EP_size_y', unit=unit)
            dimensions['has_EP'] = True
            dimensions['EP_center_x'] = TolerancedSize(nominal=0)
            dimensions['EP_center_y'] = TolerancedSize(nominal=0)
            if 'EP_center_x' in device_size_data and 'EP_center_y' in device_size_data:
                dimensions['EP_center_x'] = TolerancedSize.fromYaml(
                    device_size_data, base_name='EP_center_x', unit=unit)
                dimensions['EP_center_y'] = TolerancedSize.fromYaml(
                    device_size_data, base_name='EP_center_y', unit=unit)

        if 'heel_reduction' in device_size_data:
            print(
                "\033[1;35mThe use of manual heel reduction is deprecated. " +
                "It is automatically calculated from the minimum EP to pad clearance (ipc config file)\033[0m"
            )
            dimensions['heel_reduction'] = device_size_data.get('heel_reduction', 0)

        if 'lead_to_edge' in device_size_data:
            dimensions['lead_to_edge'] = TolerancedSize.fromYaml(device_size_data, base_name='lead_to_edge', unit=unit)

        if 'lead_center_pos_x' in device_size_data:
            dimensions['lead_center_pos_x'] = TolerancedSize.fromYaml(
                device_size_data, base_name='lead_center_pos_x', unit=unit)
        if 'lead_center_to_center_x' in device_size_data:
            dimensions['lead_center_pos_x'] = TolerancedSize.fromYaml(
                device_size_data, base_name='lead_center_to_center_x', unit=unit) / 2

        if 'lead_center_pos_y' in device_size_data:
            dimensions['lead_center_pos_y'] = TolerancedSize.fromYaml(
                device_size_data, base_name='lead_center_pos_y', unit=unit)
        if 'lead_center_to_center_y' in device_size_data:
            dimensions['lead_center_pos_y'] = TolerancedSize.fromYaml(
                device_size_data, base_name='lead_center_to_center_y', unit=unit) / 2

        if 'lead_width_H' in device_size_data and 'lead_width_V' in device_size_data:
            # Different lead widths on H and V sides
            dimensions['lead_width_H'] = TolerancedSize.fromYaml(device_size_data, base_name='lead_width_H', unit=unit)
            dimensions['lead_width_V'] = TolerancedSize.fromYaml(device_size_data, base_name='lead_width_V', unit=unit)
        else:
            # Same on all sizes (i.e. normal)
            dimensions['lead_width_H'] = TolerancedSize.fromYaml(device_size_data, base_name='lead_width', unit=unit)
            dimensions['lead_width_V'] = dimensions['lead_width_H']

        dimensions['lead_len_H'] = None
        dimensions['lead_len_V'] = None
        if 'lead_len_H' in device_size_data and 'lead_len_V' in device_size_data:
            # Different lead lengths on H and V sides
            dimensions['lead_len_H'] = TolerancedSize.fromYaml(device_size_data, base_name='lead_len_H', unit=unit)
            dimensions['lead_len_V'] = TolerancedSize.fromYaml(device_size_data, base_name='lead_len_V', unit=unit)
        elif 'lead_len' in device_size_data or (
                'lead_len_min' in device_size_data and 'lead_len_max' in device_size_data):
            dimensions['lead_len_H'] = TolerancedSize.fromYaml(device_size_data, base_name='lead_len', unit=unit)
            dimensions['lead_len_V'] = dimensions['lead_len_H']

        if 'body_to_inside_lead_edge' in device_size_data:
            dimensions['body_to_inside_lead_edge'] = TolerancedSize.fromYaml(
                device_size_data, base_name='body_to_inside_lead_edge', unit=unit)
        elif dimensions['lead_len_H'] is None:
            raise KeyError('{}: Either lead length or inside lead to edge dimension must be given.'.format(fp_id))

        return dimensions

    def generateFootprint(self, device_params, fp_id):
        print('Building footprint for parameter set: {}'.format(fp_id))

        nolead_config = NoLeadConfiguration(device_params)

        device_dimensions = NoLead.deviceDimensions(nolead_config, fp_id)

        if device_dimensions['has_EP'] and 'thermal_vias' in device_params:
            self.__createFootprintVariant(nolead_config, device_dimensions, True)

        self.__createFootprintVariant(nolead_config, device_dimensions, False)

    def __createFootprintVariant(self, device_config: NoLeadConfiguration,
                                 device_dimensions, with_thermal_vias):
        # Pull out the old-style raw data
        device_params = device_config.spec_dictionary

        lib_name = device_params.get('library', default_library)

        pincount = device_params['num_pins_x'] * 2 + device_params['num_pins_y'] * 2

        is_pull_back = 'lead_to_edge' in device_params

        default_ipc_config = 'qfn_pull_back' if is_pull_back else 'qfn'
        if device_params.get('ipc_class', default_ipc_config) == 'qfn_pull_back':
            ipc_reference = 'ipc_spec_flat_no_lead_pull_back'
        else:
            ipc_reference = 'ipc_spec_flat_no_lead'

        used_density = device_params.get('ipc_density', ipc_density)
        ipc_data_set = self.ipc_defintions[ipc_reference][used_density]
        ipc_round_base = self.ipc_defintions[ipc_reference]['round_base']

        layout = ''
        if device_dimensions['has_EP']:
            name_format = self.configuration['fp_name_EP_format_string_no_trailing_zero']
            if 'EP_size_x_overwrite' in device_params:
                EP_size = Vector2D(
                    device_params['EP_size_x_overwrite'],
                    device_params['EP_size_y_overwrite']
                )
            else:
                EP_size = Vector2D(
                    device_dimensions['EP_size_x'].nominal,
                    device_dimensions['EP_size_y'].nominal
                )
            EP_center = Vector2D(
                device_dimensions['EP_center_x'].nominal,
                device_dimensions['EP_center_y'].nominal
            )
        else:
            name_format = self.configuration['fp_name_format_string_no_trailing_zero']
            if device_params.get('use_name_format', 'QFN') == 'LGA':
                name_format = self.configuration['fp_name_lga_format_string_no_trailing_zero']
                if device_params['num_pins_x'] > 0 and device_params['num_pins_y'] > 0:
                    layout = self.configuration['lga_layout_border'].format(
                        nx=device_params['num_pins_x'], ny=device_params['num_pins_y'])

            EP_size = Vector2D(0, 0)

        if 'custom_name_format' in device_params:
            name_format = device_params['custom_name_format']

        pad_details = self.calcPadDetails(device_dimensions, EP_size, ipc_data_set, ipc_round_base)

        pad_suffix = '_Pad{pad_x:.2f}x{pad_y:.2f}mm'.format(pad_x=pad_details['left']['size'][0],
                                                            pad_y=pad_details['left']['size'][1])
        pad_suffix = '' if device_params.get('include_pad_size', 'none') not in ('fp_name_only', 'both') else pad_suffix
        pad_suffix_3d = '' if device_params.get('include_pad_size', 'none') not in ('both') else pad_suffix

        suffix = device_params.get('suffix', '')
        suffix_3d = suffix if device_params.get('include_suffix_in_3dpath', 'True') == 'True' else ""

        model3d_path_prefix = self.configuration.get('3d_model_prefix', '${KICAD8_3DMODEL_DIR}')

        size_x = device_dimensions['body_size_x'].nominal
        size_y = device_dimensions['body_size_y'].nominal

        fp_name = name_format.format(
            man=device_params.get('manufacturer', ''),
            mpn=device_params.get('part_number', ''),
            pkg=device_params['device_type'],
            pincount=pincount,
            size_y=size_y,
            size_x=size_x,
            pitch=device_dimensions['pitch_x'],
            layout=layout,
            ep_size_x=EP_size.x,
            ep_size_y=EP_size.y,
            suffix=pad_suffix,
            suffix2=suffix,
            vias=self.configuration.get('thermal_via_suffix', '_ThermalVias') if with_thermal_vias else ''
        ).replace('__', '_').lstrip('_')

        fp_name_2 = name_format.format(
            man=device_params.get('manufacturer', ''),
            mpn=device_params.get('part_number', ''),
            pkg=device_params['device_type'],
            pincount=pincount,
            size_y=size_y,
            size_x=size_x,
            pitch=device_dimensions['pitch_x'],
            layout=layout,
            ep_size_x=EP_size.x,
            ep_size_y=EP_size.y,
            suffix=pad_suffix_3d,
            suffix2=suffix_3d,
            vias=''
        ).replace('__', '_').lstrip('_')

        if 'fp_name_prefix' in device_params:
            prefix = device_params['fp_name_prefix']
            if not prefix.endswith('_'):
                prefix += '_'
            fp_name = prefix + fp_name
            fp_name_2 = prefix + fp_name_2

        model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'\
            .format(
                model3d_path_prefix=model3d_path_prefix, lib_name=lib_name,
                fp_name=fp_name_2)
        # print(fp_name)
        # print(pad_details)

        kicad_mod = Footprint(fp_name, FootprintType.SMD)

        # init kicad footprint
        kicad_mod.setDescription(
            "{manufacturer} {mpn} {package}, {pincount} Pin ({datasheet}), "
            "generated with kicad-footprint-generator {scriptname}"
            .format(
                manufacturer=device_params.get('manufacturer', ''),
                package=device_params['device_type'],
                mpn=device_params.get('part_number', ''),
                pincount=pincount,
                datasheet=device_params['size_source'],
                scriptname=os.path.basename(__file__).replace("  ", " ")
            ).lstrip())

        kicad_mod.tags = self.configuration['keyword_fp_string'].format(
            man=device_params.get('manufacturer', ''),
            package=device_params['device_type'],
            category=category
        ).lstrip().split()

        kicad_mod.tags += device_config.compatible_mpns.tags
        kicad_mod.tags += device_config.additional_tags.tags

        pad_arrays = create_dual_or_quad_pad_border(self.configuration, pad_details, device_params)
        pad_radius = get_pad_radius_from_arrays(pad_arrays)

        for pad_array in pad_arrays:
            kicad_mod.append(pad_array)

        if device_dimensions['has_EP']:
            pad_shape_details = getEpRoundRadiusParams(device_params, self.configuration, pad_radius)
            ep_pad_number = device_params.get('EP_pin_number', pincount + 1)
            if with_thermal_vias:
                thermals = device_params['thermal_vias']
                paste_coverage = thermals.get('EP_paste_coverage',
                                              device_params.get('EP_paste_coverage', DEFAULT_PASTE_COVERAGE))

                kicad_mod.append(ExposedPad(
                    number=ep_pad_number, size=EP_size,
                    at=EP_center,
                    paste_layout=thermals.get('EP_num_paste_pads', device_params.get('EP_num_paste_pads', 1)),
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
                ))
            else:
                kicad_mod.append(ExposedPad(
                    number=ep_pad_number, size=EP_size,
                    at=EP_center,
                    paste_layout=device_params.get('EP_num_paste_pads', 1),
                    paste_coverage=device_params.get('EP_paste_coverage', DEFAULT_PASTE_COVERAGE),
                    **pad_shape_details
                ))

        body_edge = {
            'left': -size_x / 2,
            'right': size_x / 2,
            'top': -size_y / 2,
            'bottom': size_y / 2
        }

        bounding_box = BoundingBox(
            min_pt=Vector2D(body_edge['left'], body_edge['top']),
            max_pt=Vector2D(body_edge['right'], body_edge['bottom'])
        )

        if device_dimensions['has_EP']:
            bounding_box.include_point(EP_center - EP_size / 2)
            bounding_box.include_point(EP_center + EP_size / 2)

        if device_params['num_pins_y'] > 0:
            bounding_box.include_point(
                Vector2D(pad_details['left']['center'][0] - pad_details['left']['size'][0] / 2,
                         0)
            )
            bounding_box.include_point(
                Vector2D(pad_details['right']['center'][0] + pad_details['right']['size'][0] / 2,
                         0)
            )

        if device_params['num_pins_x'] > 0:
            bounding_box.include_point(
                Vector2D(0,
                         pad_details['top']['center'][1] - pad_details['top']['size'][1] / 2)
            )
            bounding_box.include_point(
                Vector2D(0,
                         pad_details['bottom']['center'][1] + pad_details['bottom']['size'][1] / 2)
            )

        # ############################ SilkS ##################################

        silk_line_width_mm = configuration['silk_line_width']
        silk_pad_offset = configuration['silk_pad_clearance'] + silk_line_width_mm / 2
        silk_offset = configuration['silk_fab_offset']

        def create_silk_line(start, end):
            return Line(start=start, end=end, width=silk_line_width_mm, layer="F.SilkS")

        body_size_min = min(
            device_dimensions['body_size_x'].nominal,
            device_dimensions['body_size_y'].nominal
        )

        is_dfn = device_params['num_pins_x'] == 0 or device_params['num_pins_y'] == 0

        if is_pull_back:
            # pull-back parts have very small/no corner areas
            arrow_size_enum = drawing_tools.SilkArrowSize.SMALL
        elif is_dfn:
            if body_size_min <= 2.0:
                # for really small packages, use a smaller silk arrow
                arrow_size_enum = drawing_tools.SilkArrowSize.SMALL
            else:
                # Everything else gets medium
                arrow_size_enum = drawing_tools.SilkArrowSize.MEDIUM
        else:
            # QFNs with normal pads virtually always have space for medium
            # in the corners
            arrow_size_enum = drawing_tools.SilkArrowSize.MEDIUM

        arrow_size, arrow_length = drawing_tools.getStandardSilkArrowSize(
            arrow_size_enum, silk_line_width_mm
        )

        if is_dfn:

            # DFN-style - 45-degree arrow in corner

            #     For num_pins_x == 0, the lines are horizontal:

            #      +
            #     /|
            #    +-+  -------------  <- silk
            #        +------------+  <- body
            #       ====        ==== <- pad
            #        |            |
            #       ====        ====
            #        +------------+
            #        -------------- <- silk

            #     For num_pins_y == 0, the lines are vertical

            vertical_lines = device_params['num_pins_y'] == 0

            pads_bbox = get_bounding_box_of_pad_arrays(pad_arrays)
            top_left_pad = find_top_left_pad(pad_arrays)

            # Top corner of the top-left pad (inset to be exactly on rounded corners)
            top_left_pad_top_left_corner = get_pad_top_left_corner_midpoint(top_left_pad)
            arrow_apex = top_left_pad_top_left_corner - (silk_pad_offset * (sqrt(2) / 2))

            # round off away from the pad edge
            arrow_apex.x = roundGDown(arrow_apex.x, 0.01)
            arrow_apex.y = roundGDown(arrow_apex.y, 0.01)

            drawing_tools.TriangleArrowPointingSouthEast(
                    kicad_mod, arrow_apex, arrow_size,
                    "F.SilkS", silk_line_width_mm)

            if vertical_lines:
                # stay outside the body _and_ the pad clearance
                silk_left_x = min(pads_bbox.left - silk_pad_offset, body_edge['left'] - silk_offset)
                silk_right_x = max(pads_bbox.right + silk_pad_offset, body_edge['right'] + silk_offset)

                # avoid crashing the top line left edge into the arrow
                silk_top_y = max(body_edge['top'], arrow_apex.y + 2 * silk_line_width_mm)

                left_line = create_silk_line(
                    start=Vector2D(silk_left_x, silk_top_y),
                    end=Vector2D(silk_left_x, body_edge['bottom']))

                right_line = create_silk_line(
                    start=Vector2D(silk_right_x, silk_top_y),
                    end=Vector2D(silk_right_x, body_edge['bottom']))

                kicad_mod.append(left_line)
                kicad_mod.append(right_line)

            else:

                # stay outside the body _and_ the pad clearance
                silk_top_y = min(pads_bbox.top - silk_pad_offset, body_edge['top'] - silk_offset)
                silk_bottom_y = max(pads_bbox.bottom + silk_pad_offset, body_edge['bottom'] + silk_offset)

                # avoid crashing the top line left edge into the arrow
                silk_left_x = max(body_edge['left'], arrow_apex.x + 2 * silk_line_width_mm)

                top_line = create_silk_line(
                    start=Vector2D(silk_left_x, silk_top_y),
                    end=Vector2D(body_edge['right'], silk_top_y))

                bottom_line = create_silk_line(
                    start=Vector2D(body_edge['left'], silk_bottom_y),
                    end=Vector2D(body_edge['right'], silk_bottom_y))

                kicad_mod.append(top_line)
                kicad_mod.append(bottom_line)
        else:
            # this is a QFN

            #          -- silk
            #  +---+  /
            #   \ /   v    x   x
            #    + ------ n  n-1
            #    |        x   x
            #    |
            #   x1x
            #
            #   x2x  <- pad

            # where the lines have to end to avoid crashing into the pad
            sx1 = -(device_dimensions['pitch_x'] * (device_params['num_pins_x'] - 1) / 2.0 +
                    pad_details['top']['size'][0] / 2.0 + silk_pad_offset)

            sy1 = -(device_dimensions['pitch_y'] * (device_params['num_pins_y'] - 1) / 2.0 +
                    pad_details['left']['size'][1] / 2.0 + silk_pad_offset)

            # arrow always in top-left of body
            arrow_apex = Vector2D(
                body_edge['left'] - silk_offset,
                body_edge['top'] - silk_offset
            )

            drawing_tools.CornerBracketWithArrowPointingSouth(
                kicad_mod, arrow_apex, arrow_size, arrow_length,
                sx1, sy1, "F.SilkS", silk_line_width_mm, SILK_MIN_LEN)

            poly_silk = [
                {'x': sx1, 'y': body_edge['top'] - silk_offset},
                {'x': body_edge['left'] - silk_offset, 'y': body_edge['top'] - silk_offset},
                {'x': body_edge['left'] - silk_offset, 'y': sy1}
            ]

            if sx1 - SILK_MIN_LEN < body_edge['left'] - silk_offset:
                poly_silk = poly_silk[1:]
            if sy1 - SILK_MIN_LEN < body_edge['top'] - silk_offset:
                poly_silk = poly_silk[:-1]

            if len(poly_silk) > 1:
                # top right
                kicad_mod.append(PolygonLine(
                    polygon=poly_silk,
                    width=configuration['silk_line_width'],
                    layer="F.SilkS", x_mirror=0))
                # bottom left
                kicad_mod.append(PolygonLine(
                    polygon=poly_silk,
                    width=configuration['silk_line_width'],
                    layer="F.SilkS", y_mirror=0))
                # bottom right
                kicad_mod.append(PolygonLine(
                    polygon=poly_silk,
                    width=configuration['silk_line_width'],
                    layer="F.SilkS", x_mirror=0, y_mirror=0))

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

        # # ############################ CrtYd ##################################

        off = ipc_data_set['courtyard']
        grid = configuration['courtyard_grid']

        cy_box = courtyardFromBoundingBox(bounding_box, off, grid)

        kicad_mod.append(RectLine(
            start={
                'x': cy_box['left'],
                'y': cy_box['top']
            },
            end={
                'x': cy_box['right'],
                'y': cy_box['bottom']
            },
            width=configuration['courtyard_line_width'],
            layer='F.CrtYd'))

        # ######################### Text Fields ###############################

        addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
                      courtyard={'top': cy_box['top'], 'bottom': cy_box['bottom']},
                      fp_name=fp_name, text_y_inside_position='center', allow_rotation=True)

        # #################### Output and 3d model ############################

        kicad_mod.append(Model(filename=model_name))

        output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
        if not os.path.isdir(output_dir):  # returns false if path does not yet exist!! (Does not check path validity)
            os.makedirs(output_dir)
        filename = '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=fp_name)

        file_handler = KicadFileHandler(kicad_mod)
        file_handler.writeFile(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of files holding information about what devices should be created.')
    parser.add_argument('--global_config', type=str, nargs='?',
                        help='the config file defining how the footprint will look like. (KLC)',
                        default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?',
                        help='the config file defining series parameters.', default='../package_config_KLCv3.yaml')
    parser.add_argument('--density', type=str, nargs='?', help='IPC density level (L,N,M)', default='N')
    parser.add_argument('--ipc_doc', type=str, nargs='?', help='IPC definition document',
                        default='../ipc_definitions.yaml')
    parser.add_argument('--force_rectangle_pads', action='store_true',
                        help='Force the generation of rectangle pads instead of rounded rectangle')
    parser.add_argument('-v', '--verbose', action='count', help='set debug level')
    args = parser.parse_args()

    if args.density == 'L':
        ipc_density = 'least'
    elif args.density == 'M':
        ipc_density = 'most'

    if args.verbose:
        DEBUG_LEVEL = args.verbose

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

    if args.force_rectangle_pads:
        configuration['round_rect_max_radius'] = None
        configuration['round_rect_radius_ratio'] = 0

    for filepath in args.files:
        no_lead = NoLead(configuration)

        with open(filepath, 'r') as command_stream:
            try:
                cmd_file = yaml.safe_load(command_stream)
            except yaml.YAMLError as exc:
                print(exc)
        for pkg in cmd_file:
            no_lead.generateFootprint(cmd_file[pkg], pkg)
