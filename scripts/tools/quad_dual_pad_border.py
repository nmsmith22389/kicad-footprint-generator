from __future__ import division
from typing import List

from KicadModTree import copy, CornerSelection, Pad, PadArray

from .pad_number_generators import get_generator


def create_dual_or_quad_pad_border(configuration, pad_details, device_params) -> List[PadArray]:
    pad_shape_details = {}
    pad_shape_details['shape'] = Pad.SHAPE_ROUNDRECT
    pad_shape_details['radius_ratio'] = configuration.get('round_rect_radius_ratio', 0)
    if 'round_rect_max_radius' in configuration:
        pad_shape_details['maximum_radius'] = configuration['round_rect_max_radius']

    if 'hidden_pins' in device_params:
        pad_shape_details['hidden_pins'] = device_params['hidden_pins']
    if 'deleted_pins' in device_params:
        pad_shape_details['deleted_pins'] = device_params['deleted_pins']

    if device_params['num_pins_x'] == 0:
        pad_arrays = add_dual_pad_border_y(pad_details, device_params, pad_shape_details)
    elif device_params['num_pins_y'] == 0:
        pad_arrays = add_dual_pad_border_x(pad_details, device_params, pad_shape_details)
    else:
        pad_arrays = add_quad_pad_border(
            pad_details, device_params, pad_shape_details)

    return pad_arrays


def add_dual_pad_border_y(pad_details, device_params, pad_shape_details) -> List[PadArray]:
    init = 1
    increment = get_generator(device_params)

    _, pitch_y = get_pitches(device_params)

    pad_arrays = []
    pad_arrays.append(PadArray(
        initial= init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_params['num_pins_y'],
        x_spacing=0, y_spacing=pitch_y,
        increment=increment,
        **pad_details['left'], **pad_shape_details,
    ))
    init += device_params['num_pins_y']
    pad_arrays.append(PadArray(
        initial= init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_params['num_pins_y'],
        x_spacing=0, y_spacing=-pitch_y,
        increment=increment,
        **pad_details['right'], **pad_shape_details,
    ))

    return pad_arrays


def get_pitches(device_params):
    """
    Get the device lead pitch in x and y directions

    If only one pitch is specified, it is used for both x and y directions.
    """
    if 'pitch_x' in device_params and 'pitch_y' in device_params:
        pitch_x = device_params['pitch_x']
        pitch_y = device_params['pitch_y']
    else:
        pitch_x = device_params['pitch']
        pitch_y = pitch_x
    return pitch_x, pitch_y


def add_dual_pad_border_x(pad_details, device_params, pad_shape_details) -> List[PadArray]:
    #for devices with clockwise numbering
    init = 1
    increment = get_generator(device_params)

    pitch_x, _ = get_pitches(device_params)

    pad_arrays = []
    pad_arrays.append(PadArray(
        initial= init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_params['num_pins_x'],
        y_spacing=0, x_spacing=pitch_x,
        increment=increment,
        **pad_details['top'], **pad_shape_details,
    ))
    init += device_params['num_pins_x']
    pad_arrays.append(PadArray(
        initial= init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_params['num_pins_x'],
        y_spacing=0, x_spacing=-pitch_x,
        increment=increment,
        **pad_details['bottom'], **pad_shape_details,
    ))

    return pad_arrays


def add_quad_pad_border(pad_details, device_params, pad_shape_details) -> List[PadArray]:
    chamfer_size = device_params.get('chamfer_edge_pins', 0)

    pad_size_red = device_params.get('edge_heel_reduction', 0)

    pitch_x, pitch_y = get_pitches(device_params)

    init = 1
    corner_first = CornerSelection({CornerSelection.TOP_RIGHT: True})
    corner_last = CornerSelection({CornerSelection.BOTTOM_RIGHT: True})
    pad_size_reduction = {'x+': pad_size_red} if pad_size_red > 0 else None
    increment = get_generator(device_params)

    pad_arrays = []
    pad_arrays.append(PadArray(
        initial= init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_params['num_pins_y'],
        x_spacing=0, y_spacing=pitch_y,
        chamfer_size=chamfer_size,
        chamfer_corner_selection_first=corner_first,
        chamfer_corner_selection_last=corner_last,
        end_pads_size_reduction = pad_size_reduction,
        increment=increment,
        **pad_details['left'], **pad_shape_details,
        ))
    init += device_params['num_pins_y']
    corner_first = copy(corner_first).rotateCCW()
    corner_last = copy(corner_last).rotateCCW()
    pad_size_reduction = {'y-': pad_size_red} if pad_size_red > 0 else None

    pad_arrays.append(PadArray(
        initial= init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_params['num_pins_x'],
        y_spacing=0, x_spacing=pitch_x,
        chamfer_size=chamfer_size,
        chamfer_corner_selection_first=corner_first,
        chamfer_corner_selection_last=corner_last,
        end_pads_size_reduction = pad_size_reduction,
        increment=increment,
        **pad_details['bottom'], **pad_shape_details,
    ))

    init += device_params['num_pins_x']
    corner_first = copy(corner_first).rotateCCW()
    corner_last = copy(corner_last).rotateCCW()
    pad_size_reduction = {'x-': pad_size_red} if pad_size_red > 0 else None

    pad_arrays.append(PadArray(
        initial= init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_params['num_pins_y'],
        x_spacing=0, y_spacing=-pitch_y,
        chamfer_size=chamfer_size,
        chamfer_corner_selection_first=corner_first,
        chamfer_corner_selection_last=corner_last,
        end_pads_size_reduction = pad_size_reduction,
        increment=increment,
        **pad_details['right'], **pad_shape_details,
    ))

    init += device_params['num_pins_y']
    corner_first = copy(corner_first).rotateCCW()
    corner_last = copy(corner_last).rotateCCW()
    pad_size_reduction = {'y+': pad_size_red} if pad_size_red > 0 else None

    pad_arrays.append(PadArray(
        initial= init,
        type=Pad.TYPE_SMT,
        layers=Pad.LAYERS_SMT,
        pincount=device_params['num_pins_x'],
        y_spacing=0, x_spacing=-pitch_x,
        chamfer_size=chamfer_size,
        chamfer_corner_selection_first=corner_first,
        chamfer_corner_selection_last=corner_last,
        end_pads_size_reduction = pad_size_reduction,
        increment=increment,
        **pad_details['top'], **pad_shape_details,
    ))

    return pad_arrays
