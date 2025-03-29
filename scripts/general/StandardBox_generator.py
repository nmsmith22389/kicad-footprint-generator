#!/usr/bin/env python3

import sys
import os
from pathlib import Path

from KicadModTree import Footprint, FootprintType, KicadPrettyLibrary, ModArgparser
from kilibs.geom import Vector2D
from scripts.general.StandardBox import StandardBox
from scripts.tools.global_config_files import global_config
from scripts.tools.declarative_def_tools import common_metadata


def converter(args):

    metadata = common_metadata.CommonMetadata(args)
    footprint_name = args["name"]
    fptag = args["tags"]
    SmdTht = args["smd_tht"]
    at = args["at"]
    size = args["size"]
    pins = args["pins"]
    extratexts = args["extratexts"]
    body_position_tolerance = Vector2D(args["body_position_tolerance"])
    body_size_tolerance = Vector2D(args["body_size_tolerance"])
    courtyard = args["courtyard"]
    automatic_pin1_mark = bool(args["automatic_pin1_mark"])

    # Until this can be passed in properly, use the default global config
    global_cfg = global_config.DefaultGlobalConfig()

    # This a very naive way of calculating the total tolerance referenced to the
    # origin, but it's a start
    total_body_tolerance = body_position_tolerance + body_size_tolerance

    # Clearance from the _nominal_ body to the courtyard _centreline_
    courtyard_clearance = total_body_tolerance + Vector2D(courtyard, courtyard)
    # Clearance from the _nominal_ body to the _inside_ of the silk line
    fab_to_silk_clearance = total_body_tolerance

    dir3D = metadata.library_name + '.3dshapes'

    footprint_type = FootprintType.SMD if SmdTht == "smd" else FootprintType.THT
    f = Footprint(footprint_name, footprint_type)

    file3Dname = global_cfg.model_3d_prefix + dir3D + "/" + footprint_name + global_cfg.model_3d_suffix

    words = footprint_name.split("_")

    if words[-1].lower().startswith('handsolder'):
        words[-1] = ''
        ff = '_'.join(words)
        file3Dname = global_cfg.model_3d_prefix + dir3D + "/" + ff + global_cfg.model_3d_suffix

    f.append(StandardBox(global_config=global_cfg,
                         footprint=f,
                         description=metadata.description,
                         datasheet=metadata.datasheet,
                         at=at,
                         size=size,
                         tags=fptag,
                         compatible_mpns=metadata.compatible_mpns,
                         extratexts=extratexts, pins=pins,
                         file3Dname=file3Dname, courtyard_clearance=courtyard_clearance,
                         fab_to_silk_clearance=fab_to_silk_clearance,
                         automatic_pin1_mark=automatic_pin1_mark))

    lib = KicadPrettyLibrary(metadata.library_name, None)
    lib.save(f)


def main(args):
    ipc_default_courtyard_clearance = 0.25

    # parse arguments using optparse or argparse or what have you
    parser = ModArgparser(converter)
    # the root node of .yml files is parsed as name
    parser.add_parameter("library_name", type=str, required=True)
    parser.add_parameter("name", type=str, required=True)
    parser.add_parameter("description", type=str, required=True)
    parser.add_parameter("datasheet", type=str, required=True)
    parser.add_parameter("tags", type=str, required=True)
    parser.add_parameter("compatible_mpns", type=list, required=False)
    parser.add_parameter("smd_tht", type=str, required=False, default='tht')
    parser.add_parameter("at", type=list, required=True)
    parser.add_parameter("size", type=list, required=False)
    parser.add_parameter("pins", type=list, required=True)
    # Maximum body position deviation in each axis
    parser.add_parameter("body_position_tolerance", type=list, required=False, default=[0, 0])
    # Maximum body size deviation in each axis from the given nominal size
    parser.add_parameter("body_size_tolerance", type=list, required=False, default=[0, 0])
    # Courtyard outside the maximum body extent (i.e. not including the body tolerance)
    parser.add_parameter("courtyard", type=float, required=False, default=ipc_default_courtyard_clearance)
    parser.add_parameter("extratexts", type=list, required=False, default=[])
    parser.add_parameter("automatic_pin1_mark", type=bool, required=False, default=True)

    # now run our script which handles the whole part of parsing the files
    parser.run()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])

