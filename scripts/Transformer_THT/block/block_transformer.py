#!/usr/bin/env python

# the values in this library are taken from the full Block catalogue. It
# contains listings per series and the corresponding dimensions. The THT
# transformers start at page 250.
# https://www.block.eu/fileadmin/Blaetterkatalog_und_ebook/eBook.pdf

import csv
import sys
import os
from math import ceil, sqrt

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree

from KicadModTree import *  # NOQA
from KicadModTree.nodes.base.Pad import Pad  # NOQA

drill_extra = 1 # mm extra hole diameter
size_extra = 2 # mm copper
mounting_drill_extra = .2 # mm extra hole diameter
library = "Transformer_THT.pretty"

def setup_kicad_mod(name, url):
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(url)
    kicad_mod.setTags("transformer tht")

    kicad_mod.append(Model(filename=f"${{KISYS3DMOD}}/Transformer_THT.3dshapes/{name}.wrl"))

    return kicad_mod

def build_outline(kicad_mod, name, x, y, pad1height):
    kicad_mod.append(Text(type='reference', text='REF**', at=[0, -y/2-1],
        layer="F.SilkS"))

    kicad_mod.append(RectLine(start=[-x/2, -y/2], end=[x/2, y/2],
        layer="F.Fab"))
    kicad_mod.append(PolygoneLine(layer="F.Fab", polygone=[
        (-x/2, pad1height - 1),
        (-x/2+1.5, pad1height),
        (-x/2, pad1height + 1)
    ]))
    kicad_mod.append(RectLine(start=[-x/2, -y/2], end=[x/2, y/2],
        layer="F.SilkS", offset=.1))
    kicad_mod.append(RectLine(start=[-x/2, -y/2], end=[x/2, y/2],
        layer="F.CrtYd", offset=.25))
    kicad_mod.append(Text(type="user", text="%R", at=[0, 0], layer="F.Fab"))
    kicad_mod.append(Text(type='value', text=name, at=[0, y/2+1], layer="F.Fab"))

def add_pads(kicad_mod, size, drill, x_sep, pris_sep, secs_sep, pri_sep=None,
        sec_sep=None, shift=(0, 0)):
    if pri_sep:
        # dual input coils
        pads = [(-x_sep/2, y) for y in [-pris_sep/2 - pri_sep, -pris_sep/2,
            pris_sep/2, pris_sep/2 + pri_sep]]
    else:
        # single input coil
        pads = [(-x_sep/2, y) for y in [-pris_sep/2, pris_sep/2]]

    if sec_sep:
        # dual output coils
        pads += [(x_sep/2, -y) for y in [-secs_sep/2 - sec_sep, -secs_sep/2,
            secs_sep/2, secs_sep/2 + sec_sep]]
    else:
        # single output coil
        pads += [(x_sep/2, -y) for y in [-secs_sep/2, secs_sep/2]]

    pads = [(x + shift[0], y + shift[1]) for x, y in pads]

    trans = Translation(-pads[0][0], -pads[0][1])
    kicad_mod.append(trans)
    for i, pos in enumerate(pads):
        shape = Pad.SHAPE_ROUNDRECT if i == 0 else Pad.SHAPE_CIRCLE
        trans.append(Pad(number=i+1, type=Pad.TYPE_THT, shape=shape,
            at=pos, size=size, drill=drill, layers=Pad.LAYERS_THT,
            radius_ratio=.25, maximum_radius=.5))

    kicad_mod.append(PolygoneLine(
        polygone=[(-2, 0), (-3, .75), (-3, -.75), (-2, 0)],
        layer="F.SilkS"
    ))

    return trans, pads[0][1]

def add_mounting(kicad_mod, drill, x, y):
    for pos in ((-x/2, -y/2), (-x/2, y/2), (x/2, -y/2), (x/2, y/2)):
        kicad_mod.append(Pad(at=pos,
            type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=drill, drill=drill,
            layers=Pad.LAYERS_NPTH))

def format_number(num):
    if int(num) == num:
        return int(num)
    else:
        return num

def build_regular_transformer(series, url, A, B, C, D, E, F, G, H, Pin):
    # names are based on the listing in the catalogue on pages 281 and
    # following
    name = f"Transformer_Block_{series}_{format_number(A)}x{format_number(B)}x{format_number(C)}mm"
    print(f"Building {name}")
    kicad_mod = setup_kicad_mod(name, url)

    drill = Pin + drill_extra
    size = drill + size_extra

    trans, pad1height = add_pads(kicad_mod, size=size, drill=drill,
            x_sep=E, pris_sep=D, secs_sep=F, sec_sep=G)

    build_outline(trans, name, B, A, pad1height)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(f"{library}/{name}.kicad_mod")

def build_flat_transformer(series, url, A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P):
    # names are based on the listing in the catalogue on pages 281 and
    # following
    name = f"Transformer_Block_{series}_{format_number(A)}x{format_number(B)}x{format_number(C)}mm"
    print(f"Building {name}")
    kicad_mod = setup_kicad_mod(name, url)

    if M:
        drill = M + drill_extra
    else:
        drill = ceil(sqrt(N**2 + O**2) * 10) / 10 + drill_extra
    size = drill + size_extra

    trans, pad1height = add_pads(kicad_mod, size=size, drill=drill,
            x_sep=F, pri_sep=I, pris_sep=J, secs_sep=K, sec_sep=L,
            shift=((A-F-2*G)/2, (B-2*I-J-2*H)/2))

    build_outline(trans, name, A, B, pad1height)
    add_mounting(trans, drill=P+mounting_drill_extra, x=D, y=E)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(f"{library}/{name}.kicad_mod")


def load_csvs():
    flat_series = ["fl", "fld", "fle"]
    regular_series = ["vb", "vc"]
    for series in flat_series:
        with open(f"./series_information/{series}.csv", "r") as f:
            for row in csv.reader(f,delimiter=";"):
                args = [float(arg) for arg in row[2:]]
                build_flat_transformer(row[0], row[1], *args)
    for series in regular_series:
        with open(f"./series_information/{series}.csv", "r") as f:
            for row in csv.reader(f,delimiter=";"):
                args = [float(arg) for arg in row[2:]]
                build_regular_transformer(row[0], row[1], *args)


if __name__ == "__main__":
    try:
        os.mkdir(library)
    except FileExistsError:
        pass
    load_csvs()
