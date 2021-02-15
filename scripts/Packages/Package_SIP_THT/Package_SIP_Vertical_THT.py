#!/usr/bin/env python3

import sys
import os
import argparse
import math
import yaml

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools

from ipc_pad_size_calculators import *
from footprint_scripts_sip import makeSIPVertical
from footprint_global_properties import crt_offset


# TODO Move both ipc functions into a more generic file and rework both as they do not follow the REAL IPC standard
# Values are taken from
# https://www.pcb-3d.com/tutorials/how-to-calculate-pth-hole-and-pad-diameter-sizes-according-to-ipc-7251-ipc-2222-and-ipc-2221-standards/
def ipc_calc_min_drill_size(pin_diameter, ipc_density):
    if ipc_density == "A":
        return pin_diameter.maximum + 0.25
    elif ipc_density == "B":
        return pin_diameter.maximum + 0.20
    elif ipc_density == "C":
        return pin_diameter.maximum + 0.15
    else:
        sys.exit("ERROR: Invalid IPC density level: " + ipc_density)


def ipc_calc_pad_diameter(min_drill_diameter, ipc_density):
    if ipc_density == "A":
        return min_drill_diameter + 0.1 + 0.6
    elif ipc_density == "B":
        return min_drill_diameter + 0.1 + 0.5
    elif ipc_density == "C":
        return min_drill_diameter + 0.1 + 0.4
    else:
        sys.exit("ERROR: Invalid IPC density level: " + ipc_density)


def create_footprint(name, configuration, **kwargs):

    # read all yaml keys into local variables, all missing keys get 'None' assigned

    package = {
        'length': TolerancedSize.fromYaml(kwargs['package'], base_name='length'),
        'width':  TolerancedSize.fromYaml(kwargs['package'], base_name='width'),
        'height': TolerancedSize.fromYaml(kwargs['package'], base_name='height')
    }

    top_offset  = kwargs['top_offset']   # offset from pin 1 to the upper package edge
    left_offset = kwargs['left_offset']  # offset from pin 1 to the left package edge

    pitch = kwargs['pitch'] # pin pitch
    pins  = kwargs['pins']  # amount of pins in package (including hidden ones)

    # list of pin numbers that are physically abscent but pins are counted
    hidden_pins = kwargs['hidden_pins'] if 'hidden_pins' in kwargs else []

    pin = kwargs['pin'] if 'pin' in kwargs else None
    if pin:
        pin = {
            'length':   TolerancedSize.fromYaml(pin, base_name='length')   if 'length'   in pin else None,
            'width':    TolerancedSize.fromYaml(pin, base_name='width')    if 'width'    in pin else None,
            'diameter': TolerancedSize.fromYaml(pin, base_name='diameter') if 'diameter' in pin else None
        }

    ddrill = kwargs['ddrill'] if 'ddrill' in kwargs else None

    pad = kwargs['pad'] if 'pad' in kwargs else None
    if pad:
        pad = {
            'length': TolerancedSize.fromYaml(pad, base_name='length'),
            'width':  TolerancedSize.fromYaml(pad, base_name='width')
        }

    library     = kwargs['library']
    description = kwargs['description']
    datasheet   = kwargs['datasheet'] # link to datasheet
    revision    = kwargs['revision']  # revision of the datasheet
    tags        = kwargs['tags']

    # start actual data processing

    use_ipc_ddrill = True
    use_ipc_pads   = True

    if ddrill:
        use_ipc_ddrill = False

    if pad:
        use_ipc_pads = False
    else:
        pad = {
            'length': None,
            'width':  None
        }

    if pin:
        if bool(pin['length'] and pin['width']) ^ bool(pin['diameter']):
            if not pin['diameter']:
                # calculate diameter of rectangular pin
                min_dia = math.sqrt(pin['length'].minimum**2 + pin['width'].minimum**2)
                nom_dia = math.sqrt(pin['length'].nominal**2 + pin['width'].nominal**2)
                max_dia = math.sqrt(pin['length'].maximum**2 + pin['width'].maximum**2)
                pin['diameter'] = TolerancedSize(minimum=min_dia, nominal=nom_dia, maximum=max_dia)
        else:
            sys.exit("ERROR: Do only specify ('length' and 'width') or 'diameter' for pins but not all 3!")

    if use_ipc_ddrill:
        ddrill = ipc_calc_min_drill_size(pin['diameter'], configuration['ipc_density'])

    if use_ipc_pads:
        pad['length'] = TolerancedSize(nominal=ipc_calc_pad_diameter(ddrill, configuration['ipc_density']))
        pad['width']  = TolerancedSize(nominal=ipc_calc_pad_diameter(ddrill, configuration['ipc_density']))

    if tags:
        tags = "SIP-{0}".format(pins) + " " + tags
    else:
        tags = "SIP-{0}".format(pins)

    if datasheet:
        if not "#page=" in datasheet:
            print("WARNING: You should state the PDF page where the footprint is specified.")
            print("E.g. https://www.page.com/datasheet.pdf#page=3")
        if not datasheet.startswith("https"):
            print("WARNING: Datasheet links should use the HTTPS protocol.")
        description += ", " + datasheet
    if revision:
        description += " Rev. " + revision

    description += " (Generated with " + os.path.basename(__file__) + ")"

    # TODO Remove those print lines
    print(description)
    print(tags)

    # TODO: Move this check into makeSIPVertical and modify parameters to take a TolerancedSize
    if (package['length'].maximum - package['length'].nominal > 2 * crt_offset) or (package['width'].maximum - package['width'].nominal > 2 * crt_offset):
        print("ERROR: Your footprint has too high tolerances. This can't be handeld by makeSIPVertical!")

    makeSIPVertical(pins=pins, rm=pitch, ddrill=ddrill,
                    pad=[pad['length'].nominal, pad['width'].nominal],
                    package_size=[package['length'].nominal, package['width'].nominal, package['height'].nominal],
                    left_offset=left_offset, top_offset=top_offset,
                    footprint_name=name,
                    description=description,
                    tags=tags,
                    lib_name=library,
                    missing_pins=hidden_pins)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse *.kicad_mod.yml file(s) and create matching footprints')
    parser.add_argument('files', metavar='file', type=str, nargs='+', help='yml-files to parse')
    parser.add_argument('--ipc_density', type=str, nargs='?', help='the IPC density', default='nominal')

    args = parser.parse_args()

    # TODO Here I overwrite the configuration with B as the configuration passes "nominal"
    # and I don't know what this means...
    configuration = {
        # 'ipc_density': args.ipc_density
        'ipc_density': "B"
    }

    for filepath in args.files:
        with open(filepath, 'r') as stream:
            try:
                yaml_parsed = yaml.safe_load(stream)
                for footprint in yaml_parsed:
                    print("generate {name}.kicad_mod".format(name=footprint))
                    create_footprint(footprint, configuration, **yaml_parsed.get(footprint))

            except yaml.YAMLError as exc:
                print(exc)