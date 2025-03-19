#!/usr/bin/env python3

import argparse
import yaml

from KicadModTree import *  # NOQA
from KicadModTree.nodes.base.Pad import Pad  # NOQA
from scripts.tools.drawing_tools import round_to_grid
from scripts.tools.global_config_files import global_config as GC


def calculate_pad_spacer(pad_spacer, mirror_spacer):
    pad_spacer_pos = []

    if mirror_spacer:
        for spacer in reversed(pad_spacer):
            pad_spacer_pos.append(spacer * -1)

    pad_spacer_pos += pad_spacer

    return pad_spacer_pos


def create_smd_shielding(global_config: GC.GlobalConfig, name, **kwargs):
    lib_name = "RF_Shielding"
    kicad_mod = Footprint(name, FootprintType.SMD)

    # init kicad footprint
    kicad_mod.description = kwargs['description']
    kicad_mod.tags = 'Shielding Cabinet'

    # do some pre calculations
    # TODO: when mirror=False, array has to have even number of array elements
    x_pad_positions = calculate_pad_spacer(kwargs['x_pad_spacer'], kwargs.get('x_pad_mirror', True))
    y_pad_positions = calculate_pad_spacer(kwargs['y_pad_spacer'], kwargs.get('y_pad_mirror', True))

    x_pad_min = min(x_pad_positions)
    x_pad_max = max(x_pad_positions)
    y_pad_min = min(y_pad_positions)
    y_pad_max = max(y_pad_positions)

    x_pad_min_center = x_pad_min + kwargs['pads_width'] / 2.0
    x_pad_max_center = x_pad_max - kwargs['pads_width'] / 2.0
    y_pad_min_center = y_pad_min + kwargs['pads_width'] / 2.0
    y_pad_max_center = y_pad_max - kwargs['pads_width'] / 2.0

    x_part_min = -kwargs['x_part_size'] / 2.0
    x_part_max = kwargs['x_part_size'] / 2.0
    y_part_min = -kwargs['y_part_size'] / 2.0
    y_part_max = kwargs['y_part_size'] / 2.0

    # set general values
    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0, y_pad_min - kwargs['courtjard'] - 0.75], layer='F.SilkS'))
    kicad_mod.append(Property(name=Property.VALUE, text=name, at=[0, y_pad_max + kwargs['courtjard'] + 0.75], layer='F.Fab'))
    kicad_mod.append(Text(text='${REFERENCE}', at=[0, 0], layer='F.Fab'))

    # create courtyard
    x_courtjard_min = round_to_grid(x_pad_min - kwargs['courtjard'], 0.05)
    x_courtjard_max = round_to_grid(x_pad_max + kwargs['courtjard'], 0.05)
    y_courtjard_min = round_to_grid(y_pad_min - kwargs['courtjard'], 0.05)
    y_courtjard_max = round_to_grid(y_pad_max + kwargs['courtjard'], 0.05)

    kicad_mod.append(RectLine(start=[x_courtjard_min, y_courtjard_min],
                              end=[x_courtjard_max, y_courtjard_max],
                              layer='F.CrtYd',
                              width=global_config.courtyard_line_width))

    # create inner courtyard
    pad_width = kwargs['pads_width']
    x_courtjard_min = round_to_grid(x_pad_min + pad_width + kwargs['courtjard'], 0.05)
    x_courtjard_max = round_to_grid(x_pad_max - pad_width - kwargs['courtjard'], 0.05)
    y_courtjard_min = round_to_grid(y_pad_min + pad_width + kwargs['courtjard'], 0.05)
    y_courtjard_max = round_to_grid(y_pad_max - pad_width - kwargs['courtjard'], 0.05)
    kicad_mod.append(RectLine(start=[x_courtjard_min, y_courtjard_min],
                              end=[x_courtjard_max, y_courtjard_max],
                              layer='F.CrtYd',
                              width=global_config.courtyard_line_width))

    # create Fabrication Layer
    kicad_mod.append(RectLine(start=[x_part_min, y_part_min],
                              end=[x_part_max, y_part_max],
                              layer='F.Fab',
                              width=global_config.fab_line_width))

    # all pads have this kwargs, so we only write them one
    general_kwargs = {'number': 1,
                      'type': Pad.TYPE_SMT,
                      'shape': Pad.SHAPE_RECT,
                      'layers': Pad.LAYERS_SMT,
    }

    # create edge pads
    kicad_mod.append(Pad(at=[x_pad_min_center, y_pad_min_center],
                         size=[kwargs['pads_width'], kwargs['pads_width']], **general_kwargs))
    kicad_mod.append(Pad(at=[x_pad_max_center, y_pad_min_center],
                         size=[kwargs['pads_width'], kwargs['pads_width']], **general_kwargs))
    kicad_mod.append(Pad(at=[x_pad_max_center, y_pad_max_center],
                         size=[kwargs['pads_width'], kwargs['pads_width']], **general_kwargs))
    kicad_mod.append(Pad(at=[x_pad_min_center, y_pad_max_center],
                         size=[kwargs['pads_width'], kwargs['pads_width']], **general_kwargs))

    # iterate pairwise over pads
    for pad_start, pad_end in zip(x_pad_positions[0::2], x_pad_positions[1::2]):
        if pad_start == x_pad_min:
            pad_start += kwargs['pads_width']
        if pad_end == x_pad_max:
            pad_end -= kwargs['pads_width']

        kicad_mod.append(Pad(at=[(pad_start+pad_end)/2., y_pad_min_center],
                         size=[abs(pad_start-pad_end), kwargs['pads_width']], **general_kwargs))
        kicad_mod.append(Pad(at=[(pad_start+pad_end)/2., y_pad_max_center],
                         size=[abs(pad_start-pad_end), kwargs['pads_width']], **general_kwargs))

    for pad_start, pad_end in zip(y_pad_positions[0::2], y_pad_positions[1::2]):
        if pad_start == y_pad_min:
            pad_start += kwargs['pads_width']
        if pad_end == y_pad_max:
            pad_end -= kwargs['pads_width']

        kicad_mod.append(Pad(at=[x_pad_min_center, (pad_start+pad_end)/2.],
                         size=[kwargs['pads_width'], abs(pad_start-pad_end)], **general_kwargs))
        kicad_mod.append(Pad(at=[x_pad_max_center, (pad_start+pad_end)/2.],
                         size=[kwargs['pads_width'], abs(pad_start-pad_end)], **general_kwargs))

    # iterate pairwise over pads for silk screen
    for pad_start, pad_end in zip(x_pad_positions[1::2], x_pad_positions[2::2]):
        pad_start += 0.3
        pad_end -= 0.3

        kicad_mod.append(Line(start=[pad_start, y_part_min - 0.15],
                                  end=[pad_end, y_part_min - 0.15], layer='F.SilkS',
                                  width=global_config.silk_line_width))
        kicad_mod.append(Line(start=[pad_start, y_part_max + 0.15],
                                  end=[pad_end, y_part_max + 0.15], layer='F.SilkS',
                                  width=global_config.silk_line_width))

    for pad_start, pad_end in zip(y_pad_positions[1::2], y_pad_positions[2::2]):
        pad_start += 0.3
        pad_end -= 0.3

        # check if line has relevant length
        if pad_end - pad_start < 0.5:
            continue

        kicad_mod.append(Line(start=[x_part_min - 0.15, pad_start],
                                  end=[x_part_min - 0.15, pad_end], layer='F.SilkS',
                                  width=global_config.silk_line_width))
        kicad_mod.append(Line(start=[x_part_max + 0.15, pad_start],
                                  end=[x_part_max + 0.15, pad_end], layer='F.SilkS',
                                  width=global_config.silk_line_width))

    kicad_mod.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + name + ".wrl"))

    # write file
    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(kicad_mod)


def parse_and_execute_yml_file(global_config, filepath):
    with open(filepath, 'r') as stream:
        try:
            yaml_parsed = yaml.safe_load(stream)
            for footprint in yaml_parsed:
                print("generate {name}.kicad_mod".format(name=footprint))
                create_smd_shielding(global_config, footprint, **yaml_parsed.get(footprint))
        except yaml.YAMLError as exc:
            print(exc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse *.kicad_mod.yml file(s) and create matching footprints')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='yml-files to parse')

    global_config = GC.DefaultGlobalConfig()

    args = parser.parse_args()
    for filepath in args.files:
        parse_and_execute_yml_file(global_config, filepath)
