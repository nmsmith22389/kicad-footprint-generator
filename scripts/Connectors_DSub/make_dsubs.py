#!/usr/bin/env python

import sys
import os
import math

# ensure that the kicad-footprint-generator directory is available
# sys.path.append(os.environ.get('KIFOOTPRINTGENERATOR'))  # enable package import from parent directory
# sys.path.append("D:\hardware\KiCAD\kicad-footprint-generator")  # enable package import from parent directory
sys.path.append(
    os.path.join(sys.path[0], "..", "..", "kicad_mod")
)  # load kicad_mod path
sys.path.append(os.path.join(sys.path[0], "..", ".."))  # load kicad_mod path
sys.path.append(os.path.join(sys.path[0], "..", "tools"))  # load kicad_mod path

from KicadModTree import *  # NOQA
from footprint_scripts_dsub import *  # NOQA


if __name__ == "__main__":
    HighDensity = False
    rmx = 2.77
    rmy = 2.84
    rmy_hd = 1.98
    rmy_unboxed2 = 2.54
    pindrill = 1.0
    pad = 1.6
    mountingdrill = 3.2
    mountingpad = 4
    side_angle_degree = 10
    conn_cornerradius = 1.6
    outline_cornerradius = 1
    can_height_male = 6
    can_height_female = 6.17
    shieldthickness = 0.4
    backcan_height = 4.5
    smaller_backcan_height = 2.8
    soldercup_length = 2.9
    soldercup_diameter = 1.2
    soldercup_padsize = [2 * rmx / 3, soldercup_length * 1.2]
    soldercup_pad_edge_offset = 0.25
    smaller_backcan_offset = 1
    nut_diameter = 5
    nut_length = 5
    tags_additional = []
    lib_name = "${KICAD8_3DMODEL_DIR}/Connector_Dsub"
    classname = "DSUB"
    classname_description = "D-Sub connector"
    webpage = "https://disti-assets.s3.amazonaws.com/tonar/files/datasheets/16730.pdf"
    # unboxed connectors
    webpage_unboxed = "https://docs.rs-online.com/02d6/0900766b81585df2.pdf"
    backcan_height_unboxed = 4.1
    pin_pcb_distance_unboxed = 9.4

    # fmt: off
    #                  0,             1,             2,             3,         4,                5,                  6
    #               pins, mounting_dist, outline_sizex, outlinesize_y, connwidth,  connheight_male,  connheight_female
    sizes_table=[
                [      9,            25,         30.85,         12.50,      16.3,              8.3,              7.9 ],
                [     15,         33.30,         39.20,         12.50,      24.6,              8.3,              7.9 ],
                [     25,         47.10,         53.10,         12.50,      38.3,              8.3,              7.9 ],
                [     37,         63.50,         69.40,         12.50,      54.8,              8.3,              7.9 ],
    ]

    # boxed angled
    #                   mounting_pcb_distance,   pin_pcb_distance
    angled_distances=[
                        [                5.34,               5.34 ],
                        [                9.52,               8.10 ],
                        [               11.72,              10.30 ],
                        [               16.38,              14.96 ],
                        [                8.60,              14.96 ],
                    ]

    subvariant_straight = [
        # has_pins, connheight, mountingdrill, can_height
        [True,      8.3,        mountingdrill, can_height_male],
        [False,     7.9,        mountingdrill, can_height_female],
        [True,      8.3,        0,             can_height_male],
        [False,     7.9,        0,             can_height_female]
    ]
    # fmt: on

    #
    # Make regular density connectors
    for (
        pins,
        mounting_dist,
        outline_sizex,
        outline_sizey,
        connwidth,
        connheight_male,
        connheight_female,
    ) in sizes_table:
        for has_pins, connheight, mountingdrill_v, can_height_v in subvariant_straight:
            # Straight, Pins&Socket, with and without mountingholes
            makeDSubStraight(
                pins=pins,
                isMale=has_pins,
                HighDensity=HighDensity,
                rmx=rmx,
                rmy=rmy,
                pindrill=pindrill,
                pad=pad,
                mountingdrill=mountingdrill_v,
                mountingpad=mountingpad,
                mountingdistance=mounting_dist,
                outline_size=[outline_sizex, outline_sizey],
                outline_cornerradius=outline_cornerradius,
                connwidth=connwidth,
                side_angle_degree=side_angle_degree,
                connheight=connheight,
                conn_cornerradius=conn_cornerradius,
                tags_additional=tags_additional,
                lib_name=lib_name,
                classname=classname,
                classname_description=classname_description,
                webpage=webpage,
            )

            # Edge-mount variant, Pins&Socket
            makeDSubEdge(
                pins=pins,
                isMale=has_pins,
                rmx=rmx,
                pad=soldercup_padsize,
                mountingdrill=mountingdrill,
                mountingdistance=mounting_dist,
                shield_width=outline_sizex,
                shieldthickness=shieldthickness,
                connwidth=connwidth,
                can_height=can_height_v,
                backcan_width=connwidth + 2 * shieldthickness,
                backcan_height=backcan_height,
                smaller_backcan_offset=smaller_backcan_offset,
                smaller_backcan_height=smaller_backcan_height,
                soldercup_length=soldercup_length,
                soldercup_diameter=soldercup_diameter,
                soldercup_pad_edge_offset=soldercup_pad_edge_offset,
                tags_additional=tags_additional,
                lib_name=lib_name,
                classname=classname,
                classname_description=classname_description,
                webpage=webpage,
            )

        # Horizontal connectors, Pins&Socket, 5 different 'distances'
        for mounting_pcb_distance_v, pin_pcb_distance_v in angled_distances:
            mounting_pcb_distance = mounting_pcb_distance_v - shieldthickness
            pin_pcb_distance = pin_pcb_distance_v - shieldthickness

            # backbox_height is the y-size of the plastic part that encloses the pins.
            # If we don't know how big the backbox_height should be, so we estimate its size by finding the copper part which is furthest
            # from the front of the connector. And then adding 1mm as magic value.
            backbox_height = (
                max(
                    pin_pcb_distance + rmy + pad / 2,
                    mounting_pcb_distance + mountingpad / 2,
                )
                + 1
            )
            # reuse the subvariant_straight to get the mapping of variant and can_height
            for (
                has_pins,
                connheight,
                mountingdrill_v,
                can_height_v,
            ) in subvariant_straight:
                makeDSubAngled(
                    pins=pins,
                    isMale=has_pins,
                    HighDensity=HighDensity,
                    rmx=rmx,
                    rmy=rmy,
                    pindrill=pindrill,
                    pad=pad,
                    pin_pcb_distance=pin_pcb_distance,
                    mountingdrill=mountingdrill,
                    mountingpad=mountingpad,
                    mountingdistance=mounting_dist,
                    mounting_pcb_distance=mounting_pcb_distance,
                    shield_width=outline_sizex,
                    shield_thickness=shieldthickness,
                    can_width=connwidth,
                    can_height=can_height_v,
                    backbox_width=outline_sizex,
                    backbox_height=backbox_height,
                    nut_diameter=nut_diameter,
                    nut_length=nut_length,
                    tags_additional=tags_additional,
                    lib_name=lib_name,
                    classname=classname,
                    classname_description=classname_description,
                    webpage=webpage,
                )

    #
    # unboxed angled
    #
    pin_pcb_distance = 9.4
    mounting_pcb_distance = 0
    for (
        pins,
        mounting_dist,
        outline_sizex,
        outline_sizey,
        connwidth,
        connheight_male,
        connheight_female,
    ) in sizes_table:
        for has_pins, connheight, mountingdrill_v, can_height_v in subvariant_straight:
            # two y-pin-pitch variants
            for rmy_v in [rmy, rmy_unboxed2]:
                makeDSubAngled(
                    pins=pins,
                    isMale=has_pins,
                    HighDensity=HighDensity,
                    rmx=rmx,
                    rmy=rmy_v,
                    pindrill=pindrill,
                    pad=pad,
                    pin_pcb_distance=pin_pcb_distance,
                    mountingdrill=0,
                    mountingpad=mountingpad,
                    mountingdistance=mounting_dist,
                    mounting_pcb_distance=pin_pcb_distance,
                    shield_width=outline_sizex,
                    shield_thickness=shieldthickness,
                    backbox_width=0,
                    backbox_height=0,
                    can_width=connwidth,
                    can_height=can_height_v,
                    backcan_width=connwidth + 2 * shieldthickness,
                    backcan_height=backcan_height_unboxed,
                    nut_diameter=0,
                    nut_length=0,
                    tags_additional=tags_additional,
                    lib_name=lib_name,
                    classname=classname,
                    classname_description=classname_description,
                    webpage=webpage_unboxed,
                )

    # fmt: off


    #
    # build HighDensity connectors
    #
    HighDensity=True
    #               pins, mounting_dist, outline_sizex, outlinesize_y, connwidth,  connheight_male,  connheight_female, rmx,  HighDensityOffsetMidLeft
    hd_sizes_table=[
                [     15,            25,         30.85,         12.50,      16.3,              8.3,              7.9,    2.29, 7.04 ],
                [     26,         33.30,         39.20,         12.50,      24.6,              8.3,              7.9,    2.29, 6.88 ],
                [     44,         47.10,         53.10,         12.50,      38.3,              8.3,              7.9,    2.29, 6.88 ],
                [     62,         63.50,         69.40,         12.50,      54.8,              8.3,              7.9,    2.41, 7.00 ],
                ]
    #                     mounting_pcb_distance,   pin_pcb_distance,  backbox_height
    angled_distances=[
                        [                5.34,               3.43,             8.6 ],
                        [               11.29,               8.75,             0.0 ],
                    ]
    # fmt: on
    for (
        pins,
        mounting_dist,
        outline_sizex,
        outlinesize_y,
        connwidth,
        connheight_male,
        connheight_female,
        rmx,
        HighDensityOffsetMidLeft,
    ) in hd_sizes_table:
        # Build Pins- and Socket variants
        for has_pins in [True, False]:
            connheight = connheight_male if has_pins else connheight_female
            can_height = can_height_male if has_pins else can_height_female

            # regular straight HD (kicad calls this vertical)
            makeDSubStraight(
                pins=pins,
                isMale=has_pins,
                HighDensity=HighDensity,
                rmx=rmx,
                rmy=rmy_hd,
                pindrill=pindrill,
                pad=pad,
                mountingdrill=mountingdrill,
                mountingpad=mountingpad,
                mountingdistance=mounting_dist,
                outline_size=[outline_sizex, outlinesize_y],
                outline_cornerradius=outline_cornerradius,
                connwidth=connwidth,
                side_angle_degree=side_angle_degree,
                connheight=connheight,
                conn_cornerradius=conn_cornerradius,
                tags_additional=tags_additional,
                lib_name=lib_name,
                classname=classname,
                classname_description=classname_description,
                webpage=webpage,
                HighDensityOffsetMidLeft=HighDensityOffsetMidLeft,
            )

            # HD angled, with different distances
            for angled_distance in angled_distances:
                mounting_pcb_distance = angled_distance[0] - shieldthickness
                pin_pcb_distance = angled_distance[1] - shieldthickness
                if angled_distance[2] > 0:
                    backbox_height = angled_distance[2]
                else:
                    backbox_height = (
                        max(
                            pin_pcb_distance + rmy + pad / 2,
                            mounting_pcb_distance + mountingpad / 2,
                        )
                        + 1
                    )
                # regular angled (kicad calles this horizontal)
                makeDSubAngled(
                    pins=pins,
                    isMale=has_pins,
                    HighDensity=HighDensity,
                    rmx=rmx,
                    rmy=rmy,
                    pindrill=pindrill,
                    pad=pad,
                    pin_pcb_distance=pin_pcb_distance,
                    mountingdrill=mountingdrill,
                    mountingpad=mountingpad,
                    mountingdistance=mounting_dist,
                    mounting_pcb_distance=mounting_pcb_distance,
                    shield_width=outline_sizex,
                    shield_thickness=shieldthickness,
                    can_width=connwidth,
                    can_height=can_height_male,  # this might be a bug!
                    backbox_width=outline_sizex,
                    backbox_height=backbox_height,
                    nut_diameter=nut_diameter,
                    nut_length=nut_length,
                    tags_additional=tags_additional,
                    lib_name=lib_name,
                    classname=classname,
                    classname_description=classname_description,
                    webpage=webpage,
                    HighDensityOffsetMidLeft=HighDensityOffsetMidLeft,
                )
