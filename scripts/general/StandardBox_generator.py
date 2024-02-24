#!/usr/bin/env python3

import sys
import os

# load parent path of KicadModTree
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))

# load scripts
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

from KicadModTree import Footprint, FootprintType, KicadFileHandler, ModArgparser, Vector2D
from general.StandardBox import StandardBox

def converter(args):

    library_name = args["library_name"]
    footprint_name = args["name"]
    description = args["description"]
    datasheet = args["datasheet"]
    fptag = args["tags"]
    SmdTht = args["smd_tht"]
    at = args["at"]
    size = args["size"]
    pins = args["pins"]
    extratexts = args["extratexts"]
    body_position_tolerance = Vector2D(args["body_position_tolerance"])
    body_size_tolerance = Vector2D(args["body_size_tolerance"])
    courtyard = args["courtyard"]

    # This a very naive way of calculating the total tolerance referenced to the
    # origin, but it's a start
    total_body_tolerance = body_position_tolerance + body_size_tolerance

    # Clearance from the _nominal_ body to the courtyard _centreline_
    courtyard_clearance = total_body_tolerance + Vector2D(courtyard, courtyard)
    # Clearance from the _nominal_ body to the _inside_ of the silk line
    fab_to_silk_clearance = total_body_tolerance

    dir3D = library_name + '.3dshapes'

    footprint_type = FootprintType.SMD if SmdTht == "smd" else FootprintType.THT
    f = Footprint(footprint_name, footprint_type)

    file3Dname = "${KICAD8_3DMODEL_DIR}/" + dir3D + "/" + footprint_name + ".wrl"

    words = footprint_name.split("_")

    if words[-1].lower().startswith('handsolder'):
        words[-1] = ''
        ff = '_'.join(words)
        file3Dname = "${KICAD8_3DMODEL_DIR}/" + dir3D + "/" + ff + ".wrl"

    f.append(StandardBox(footprint=f, description=description, datasheet=datasheet,
                         at=at, size=size, tags=fptag, extratexts=extratexts, pins=pins,
                         file3Dname=file3Dname, courtyard_clearance=courtyard_clearance,
                         fab_to_silk_clearance=fab_to_silk_clearance))

    target_library_dir = f"{library_name}.pretty"
    target_filename = os.path.join(target_library_dir, f"{footprint_name}.kicad_mod")

    os.makedirs(target_library_dir, exist_ok=True)

    file_handler = KicadFileHandler(f)
    file_handler.writeFile(target_filename)

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

    # now run our script which handles the whole part of parsing the files
    parser.run()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])

