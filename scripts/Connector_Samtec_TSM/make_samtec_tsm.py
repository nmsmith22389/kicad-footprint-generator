#!/usr/bin/env python
#
# Generator for horizontal SMD variants of Samtec's TSM range.
#
# (Horizontal THT variants as well as all vertical variants are already covered by
# Connector_PinHeader_#.##mm.)
#
# Single-row variant:
#   technical drawing: https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sh-xx-xxx-x-xx-mkt.pdf
#   solder footprint:  https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sh-xx-xxx-x-xx-footprint.pdf
# Two-row variant:
#   technical drawing: https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-xx-xx-xxx-xx-mkt1.pdf
#   solder footprint:  https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-dh-xx-xxx-xx-footprint.pdf
#
import math
import os
import sys
from typing import List, Optional, Tuple

# find our way to the KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", ".."))

from KicadModTree import FilledRect, Footprint, FootprintType, KicadFileHandler, Line, Model, Node
from KicadModTree import Pad, PolygonLine, RectFill, RectLine, Text, Translation


FAB_MID_TO_SILK_MID = 0.06
COPPER_EDGE_TO_SILK_MID = 0.26
FAB_MID_TO_COURTYARD_MID = 0.25
COPPER_EDGE_TO_COURTYARD_MID = 0.25


#             <--> pad_offset
#                 <-------> pack_width
#                          <------------------------------> pin_length_front
#    <col_dist>
# +---            +-------+
# | OOO      OOO  |       +-------------------------------+            ^
# | OOO ==== OOO  |       |                               |    ^       pin_width
#   OOO      OOO  |       +-------------------------------+    |       v
#                 +-------+                                    pitch
#   OOO      OOO  |       +-------------------------------+    |
#   OOO ==== OOO  |       |                               |    v
#   OOO      OOO  |       +-------------------------------+
#                 +-------+
#    <-----------> pin_length_rear


def court_round(value: float, translation: float, up: bool = False) -> float:
    rounder = math.ceil if up else math.floor
    return rounder((value - translation) * 100.0) / 100.0 + translation


def add_rectangle_sides(
    parent: Node,
    top_left: Tuple[float, float],
    bottom_right: Tuple[float, float],
    left: bool = True,
    right: bool = True,
    top: bool = True,
    bottom: bool = True,
    **kwargs
):
    (x_left, y_top) = top_left
    (x_right, y_bottom) = bottom_right
    if left:
        parent.append(Line(
            start=[x_left, y_top],
            end=[x_left, y_bottom],
            **kwargs,
        ))
    if right:
        parent.append(Line(
            start=[x_right, y_top],
            end=[x_right, y_bottom],
            **kwargs,
        ))
    if top:
        parent.append(Line(
            start=[x_left, y_top],
            end=[x_right, y_top],
            **kwargs,
        ))
    if bottom:
        parent.append(Line(
            start=[x_left, y_bottom],
            end=[x_right, y_bottom],
            **kwargs,
        ))


def generate_samtec_tsm(
    columns: int, rows: int, col_dist: float, pitch: float, pack_width: float, pin_width: float,
    pin_length_front: float, pin_length_rear: float, pad_width: float, pad_height: float,
    pad_offset: float, pad_corner_radius: Optional[float] = None, text_offset: float = 1.0,
    pin_rear_bends: Optional[List[float]] = None, lib_name: str = "Connector_Samtec_TSM",
    class_name: str = "Samtec_TSM", class_description: str = "pin header",
    offset3d: List[float] = [0.0, 0.0, 0.0], scale3d: List[float] = [1.0, 1.0, 1.0],
    rotate3d: List[float] = [0.0, 0.0, 0.0], model3d_path_prefix: str = "${KICAD8_3DMODEL_DIR}",
    datasheet_url: Optional[str] = None,
):
    if pin_rear_bends is None:
        pin_rear_bends = []
    if pad_corner_radius is None:
        # IPC-7351C recommendation
        pad_corner_radius = min(0.25 * min(pad_width, pad_height), 0.25)

    # set up some names
    footprint_name = "{3}_{0}x{1:02}_Pitch{2:03.2f}mm_SMD".format(columns, rows, pitch, class_name)
    description = "surface-mounted angled {3}, {0}x{1:02}, {2:03.2f}mm pitch".format(columns, rows, pitch, class_description)
    tags = "Surface mounted {3} SMD {0}x{1:02} {2:03.2f}mm".format(columns, rows, pitch, class_description)
    if columns == 1:
        description += ", single row"
        tags += " single row"
    elif columns == 2:
        description += ", double row"
        tags += " double row"
    if datasheet_url is not None:
        description += " ({0})".format(datasheet_url)

    # make some preliminary calculations

    pad_1_center_h = -pad_offset - (columns-1) * col_dist
    pad_1_center_v = pitch/2.0
    pad_1_left = pad_1_center_h - pad_width/2.0
    pad_1_top = pitch/2.0 - pad_height/2.0
    pad_1_right = pad_1_center_h + pad_width/2.0
    pad_1_bottom = pitch/2.0 + pad_height/2.0

    kicad_mod_raw = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod_raw.setDescription(description)
    kicad_mod_raw.setTags(tags)

    # center on pads
    x_offset = pad_1_center_h + (columns - 1) * col_dist / 2.0
    y_offset = pad_1_center_v + (rows - 1) * pitch / 2.0
    kicad_mod = Translation(
        -x_offset,
        -y_offset,
    )
    kicad_mod_raw.append(kicad_mod)

    court_left = court_round(pad_1_left - COPPER_EDGE_TO_COURTYARD_MID, x_offset, False)
    court_top = court_round(-FAB_MID_TO_COURTYARD_MID, y_offset, False)
    court_right = court_round(pack_width + pin_length_front + FAB_MID_TO_COURTYARD_MID, x_offset, True)
    court_bottom = court_round(rows * pitch + FAB_MID_TO_COURTYARD_MID, y_offset, True)

    # 1. paint the fab layer
    # 1.1. paint the packs
    # 1.1.1. a frame around them all
    kicad_mod.append(PolygonLine(
        nodes=[
            # top bar (right by 1mm)
            (1.0, 0.0),
            (pack_width, 0.0),

            # downward
            (pack_width, rows * pitch),

            # left
            (0.0, rows * pitch),

            # up (down by 1mm)
            (0.0, 1.0),

            # diagonally (chamfer to signify pin 1)
            (1.0, 0.0),
        ],
        layer="F.Fab",
    ))

    # 1.1.2. division lines for each pin
    for r in range(1, rows):
        kicad_mod.append(Line(
            start=[0.0, r * pitch],
            end=[pack_width, r * pitch],
            layer="F.Fab",
        ))

    # 1.2. paint the forward pins
    pin_offset = (pitch - pin_width) / 2.0
    for r in range(rows):
        add_rectangle_sides(
            kicad_mod,
            (pack_width, r * pitch + pin_offset),
            (pack_width + pin_length_front, r * pitch + pin_offset + pin_width),
            left=False,
            layer="F.Fab",
        )

    # 1.3. paint the rear pins
    for r in range(rows):
        add_rectangle_sides(
            kicad_mod,
            (-pin_length_rear, r * pitch + pin_offset),
            (0, r * pitch + pin_offset + pin_width),
            right=False,
            layer="F.Fab",
        )
        # add the bend indications
        for bend in pin_rear_bends:
            kicad_mod.append(Line(
                start=[-bend, r * pitch + pin_offset],
                end=[-bend, r * pitch + pin_offset + pin_width],
                layer="F.Fab",
            ))

    # 1.4. add pads
    pad_n = 1
    for r in range(rows):
        for c in range(columns):
            col_pad_offset = (columns - (c + 1)) * col_dist
            kicad_mod.append(Pad(
                number=pad_n,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_ROUNDRECT,
                layers=Pad.LAYERS_SMT,
                at=[-(pad_offset + col_pad_offset), r * pitch + pitch / 2.0],
                size=[pad_width, pad_height],
                round_radius_exact=pad_corner_radius,
            ))
            pad_n += 1

    # 1.5. add silkscreen
    # 1.5.1. a frame around them all
    kicad_mod.append(PolygonLine(
        nodes=[
            # top bar
            (-FAB_MID_TO_SILK_MID, -FAB_MID_TO_SILK_MID),
            (pack_width + FAB_MID_TO_SILK_MID, -FAB_MID_TO_SILK_MID),

            # downward
            (pack_width + FAB_MID_TO_SILK_MID, rows * pitch + FAB_MID_TO_SILK_MID),

            # left
            (-FAB_MID_TO_SILK_MID, rows * pitch + FAB_MID_TO_SILK_MID),

            # up
            (-FAB_MID_TO_SILK_MID, -FAB_MID_TO_SILK_MID),
        ],
        layer="F.SilkS",
    ))
    # 1.5.2. division lines for each pin
    for r in range(1, rows):
        kicad_mod.append(Line(
            start=[-FAB_MID_TO_SILK_MID, r * pitch],
            end=[pack_width + FAB_MID_TO_SILK_MID, r * pitch],
            layer="F.SilkS",
        ))
    # 1.5.3. each pin
    for r in range(rows):
        add_rectangle_sides(
            kicad_mod,
            (pack_width + FAB_MID_TO_SILK_MID, r * pitch + pin_offset - FAB_MID_TO_SILK_MID),
            (pack_width + pin_length_front + FAB_MID_TO_SILK_MID, r * pitch + pin_offset + pin_width + FAB_MID_TO_SILK_MID),
            left=False,
            layer="F.SilkS",
        )
        if r == 0:
            kicad_mod.append(RectFill(
                start=[pack_width + FAB_MID_TO_SILK_MID, r * pitch + pin_offset - FAB_MID_TO_SILK_MID],
                end=[pack_width + pin_length_front + FAB_MID_TO_SILK_MID, r * pitch + pin_offset + pin_width + FAB_MID_TO_SILK_MID],
                layer="F.SilkS",
            ))
    # 1.5.4. pin-1 corner
    pad_1_corner_left = pad_1_left - COPPER_EDGE_TO_SILK_MID
    pad_1_corner_top = pad_1_top - COPPER_EDGE_TO_SILK_MID
    kicad_mod.append(PolygonLine(
        nodes=[
            # left bar
            (pad_1_corner_left, pad_1_bottom),
            (pad_1_corner_left, pad_1_corner_top),

            # rightward
            (pad_1_right, pad_1_corner_top),
        ],
        layer="F.SilkS",
    ))

    # 1.6. add courtyard
    kicad_mod.append(PolygonLine(
        nodes=[
            # top
            (court_left, court_top),
            (court_right, court_top),

            # down
            (court_right, court_bottom),

            # left
            (court_left, court_bottom),

            # up
            (court_left, court_top),
        ],
        layer="F.CrtYd",
    ))

    # 1.7. add the standard text
    x_center = (court_left + court_right) / 2.0
    y_max = rows * pitch
    y_center = y_max / 2.0
    kicad_mod.append(Text(
        type='reference', text='REF**', at=[x_center, -text_offset],
        layer='F.SilkS',
    ))
    kicad_mod.append(Text(
        type='user', text='${REFERENCE}', at=[pack_width/2.0, y_center], rotation=90,
        layer='F.Fab',
    ))
    kicad_mod.append(Text(
        type='value', text=footprint_name,
        at=[x_center, y_max + text_offset], layer='F.Fab',
    ))

    # add 3D model
    kicad_mod.append(Model(
        filename="{0}/{1}.3dshapes/{2}.wrl".format(model3d_path_prefix, lib_name, footprint_name),
        at=offset3d, scale=scale3d, rotate=rotate3d,
    ))

    # spit it out
    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    file_handler = KicadFileHandler(kicad_mod_raw)
    file_handler.writeFile('{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name))


def main():
    LEAD_STYLES_1COL = {
        1: {
            "pin_length_front": 5.84,
            "pin_length_rear": 4.57,
        },
        2: {
            "pin_length_front": 8.13,
            "pin_length_rear": 4.83,
        },
        3: {
            "pin_length_front": 10.67,
            "pin_length_rear": 4.83,
        },
        4: {
            "pin_length_front": 3.05,
            "pin_length_rear": 4.83,
        },
    }
    for rows in range(2, 37):
        for (lead_style_number, style_args) in LEAD_STYLES_1COL.items():
            class_name = "Samtec_TSM-1{r:02}-{l:02}-xxx-SH".format(r=rows, l=lead_style_number)
            # add a bend indicator halfway
            pin_rear_bend = style_args["pin_length_rear"] / 2.0
            pack_width = 2.54
            print(class_name)
            generate_samtec_tsm(
                columns=1, rows=rows, col_dist=0.0, pack_width=pack_width, pitch=2.54,
                pin_width=0.64, pad_width=3.18, pad_height=1.27, pad_offset=5.283-(pack_width/2.0),
                pin_rear_bends=[pin_rear_bend], class_name=class_name,
                datasheet_url="https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sh-xx-xxx-x-xx-mkt.pdf, https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sh-xx-xxx-x-xx-footprint.pdf",
                **style_args
            )

    LEAD_STYLES_2COL = {
        # this is always the longer pin (since it covers the shorter pin)
        1: {
            "pin_length_front": 5.84,
        },
        2: {
            "pin_length_front": 8.13,
        },
        3: {
            "pin_length_front": 10.67,
        },
        4: {
            "pin_length_front": 3.05,
        },
    }
    for rows in range(2, 37):
        for (lead_style_number, style_args) in LEAD_STYLES_2COL.items():
            class_name = "Samtec_TSM-1{r:02}-{l:02}-xxx-DH".format(r=rows, l=lead_style_number)
            # add a bend indicator halfway
            pin_length_rear = 7.87
            pin_rear_bend = pin_length_rear / 2.0
            pack_width = 2.54
            print(class_name)
            generate_samtec_tsm(
                columns=2, rows=rows, col_dist=4.19, pack_width=pack_width, pitch=2.54,
                pin_width=0.64, pin_length_rear=pin_length_rear, pad_width=3.18, pad_height=1.27,
                pad_offset=4.305-(pack_width/2.0), pin_rear_bends=[pin_rear_bend],
                class_name=class_name,
                datasheet_url="https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-xx-xx-xxx-xx-mkt1.pdf, https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-dh-xx-xxx-xx-footprint.pdf",
                **style_args
            )


if __name__ == "__main__":
    main()
