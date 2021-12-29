import sys
import os

sys.path.append(os.path.join(sys.path[0], "../.."))  # enable package import from parent directory

from KicadModTree import *  # NOQA
from scripts.Capacitors_SMD.chamfers import add_rect_chamfer

classname="Converter_ACDC"

def make_converter(
    footprint_name='',
    description='',
    tags='',
    size=(20, 20),
    chamfers=[],  # Try [{'size': 2, 'corner': 'all'}]
    pin1_offset=(1, 1),
    pins = [
        (0, 0),  # Pin 1
        (0, 1),  # Pin 2
        (2, 2),  # etc
        { 'pos': (2, 0), 'drill': 1.5, 'pad': 2 },
    ],
    drill=1,
    pad=1.5,
):
    print(footprint_name)
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription(description)
    kicad_mod.setTags(tags)

    x1 = -pin1_offset[0]
    x2 = x1 + size[0]
    xc = (x1 + x2) / 2
    y1 = -pin1_offset[1]
    y2 = y1 + size[1]
    yc = (y1 + y2) / 2

    # create pads
    shape = Pad.SHAPE_RECT
    number = 1 
    for pin in pins:
        if type(pin) is dict:
            (x,y) = pin['pos']
            pin_drill = pin['drill']
            pin_pad = pin['pad']
        else:
            (x,y) = pin
            pin_drill = drill
            pin_pad = pad

        kicad_mod.append(Pad(number=number, type=Pad.TYPE_THT, shape=shape,
                                at=[x, y], size=pin_pad, drill=pin_drill, layers=Pad.LAYERS_THT))
        shape = Pad.SHAPE_CIRCLE
        number = number + 1

    #
    # Silkscreen
    #
    kicad_mod.append(Text(type='reference', text='REF**', at=[xc, y1-1.5], layer='F.SilkS'))
    kicad_mod = add_rect_chamfer(kicad_mod, [x1, y1], [x2, y2], 'F.SilkS', width=0.12, offset=(0,0), chamfers=chamfers)
    # Pin-1 designator
    kicad_mod.append(Line(start=[x1-0.5, y1-0.5], end=[x1+2.5, y1-0.5], layer='F.SilkS'))
    kicad_mod.append(Line(start=[x1-0.5, y1-0.5], end=[x1-0.5, y1+2.5], layer='F.SilkS'))

    #
    # Fabrication
    #
    kicad_mod.append(Text(type='value', text=footprint_name, at=[xc, yc-2], layer='F.Fab'))
    kicad_mod.append(Text(type='user', text='%R', at=[xc, yc], layer='F.Fab'))
    # Simplified outline
    kicad_mod = add_rect_chamfer(kicad_mod, [x1, y1], [x2, y2], 'F.Fab', width=0.10, offset=(0,0), chamfers=chamfers)
    # Pin-1 designator
    kicad_mod.append(Line(start=[x1-0.3, y1-0.3], end=[x1+2.7, y1-0.3], layer='F.Fab'))
    kicad_mod.append(Line(start=[x1-0.3, y1-0.3], end=[x1-0.3, y1+2.7], layer='F.Fab'))

    #
    # Courtyard
    #
    kicad_mod = add_rect_chamfer(kicad_mod, [x1, y1], [x2, y2], 'F.CrtYd', width=0.05, offset=(0.25, 0.25), chamfers=chamfers)
    
    # add model
    kicad_mod.append(Model(
        filename="${KISYS3DMOD}" + "/{}.3dshapes/{}.wrl".format(classname, footprint_name),
        at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    # output kicad model
    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile('{}.kicad_mod'.format(footprint_name))


def make_meanwell_irm_30():
    """Meanwell IRM-30 - http://www.meanwell.com/Upload/PDF/IRM-30/IRM-30-SPEC.PDF"""
    make_converter(
        footprint_name="{}_MeanWell_IRM-30-xx_THT".format(classname),
        description='http://www.meanwell.com/Upload/PDF/IRM-30/IRM-30-SPEC.PDF',
        tags='ACDC-Converter 30W Meanwell IRM-30 THT',
        size=(69.5, 39.0),
        chamfers=[{'size': 2, 'corner': 'all'}],
        pin1_offset=(4, 4.5),
        pins = [
            ( 0.0, 0.0),
            ( 0.0, 5.5),
            (61.5, 9.0),
            (61.5, 0.0),
        ],
        drill=1.3,
        pad=3,
    )


def make_meanwell_irm_45():
    """Meanwell IRM-45 - https://www.meanwell-web.com/content/files/pdfs/productPdfs/MW/IRM-45/IRM-45-spec.pdf"""
    make_converter(
        footprint_name="{}_MeanWell_IRM-45-xx_THT".format(classname),
        description='https://www.meanwell-web.com/content/files/pdfs/productPdfs/MW/IRM-45/IRM-45-spec.pdf',
        tags='ACDC-Converter 45W Meanwell IRM-45 THT',
        size=(87, 52),
        chamfers=[{'size': 2, 'corner': 'all'}],
        pin1_offset=(5.3, 5),
        pins = [
            ( 0.0, 0.0),
            ( 0.0, 6.75),
            { 'pos': (76.0, 41.25), 'drill': 2.3, 'pad': 4.5 },
            { 'pos': (76.0, 35.75), 'drill': 2.3, 'pad': 4.5 },
        ],
        drill=1.3,  # datasheet says diameter: 1ψ and 2ψ. Mail from distributor confirms that they mean 1mm and 2mm.
        pad=3,
    )


def make_meanwell_irm_60():
    """Meanwell IRM-60 - https://www.meanwell-web.com/content/files/pdfs/productPdfs/MW/IRM-60/IRM-60-spec.pdf"""
    make_converter(
        footprint_name="{}_MeanWell_IRM-60-xx_THT".format(classname),
        description='https://www.meanwell-web.com/content/files/pdfs/productPdfs/MW/IRM-60/IRM-60-spec.pdf',
        tags='ACDC-Converter 60W Meanwell IRM-60 THT',
        size=(87, 52),
        chamfers=[{'size': 2, 'corner': 'all'}],
        pin1_offset=(5.3, 5),
        pins = [
            ( 0.0, 0.0),
            ( 0.0, 6.75),
            { 'pos': (76.0, 41.25), 'drill': 2.3, 'pad': 4.5 },
            { 'pos': (76.0, 35.75), 'drill': 2.3, 'pad': 4.5 },
        ],
        drill=1.3,  # datasheet says diameter: 1ψ and 2ψ. Mail from distributor confirms that they mean 1mm and 2mm.
        pad=3,
    )


def make_hilink_hlk_pm01():
    """Hi-Link HLK-PMXX - http://www.hlktech.net/product.php?CateId=10"""
    make_converter(
        footprint_name="{}_Hi-Link_HLK-PMXX_THT".format(classname),
        description='http://www.hlktech.net/product_detail.php?ProId=54',
        tags='ACDC-Converter 3W Hi-Link HLK-PMXX THT',
        size=(34, 20.2),
        pin1_offset=(2.3, 7.6),
        pins = [
            ( 0.0, 0.0),
            ( 0.0, 5.0),
            ( 29.4, -5.2),
            ( 29.4, 10.4),
        ],
        drill=0.9,
        pad=3,
    )


def make_hilink_hlk_5m01():
    """Hi-Link HLK-5MXX - http://www.hlktech.net/product.php?CateId=9"""
    make_converter(
        footprint_name="{}_Hi-Link_HLK-5MXX_THT".format(classname),
        description='http://www.hlktech.net/product_detail.php?ProId=60',
        tags='ACDC-Converter 5W Hi-Link HLK-5MXX THT',
        size=(38, 23),
        pin1_offset=(2.2, 8.5),
        pins = [
            ( 0.0, 0.0),
            ( 0.0, 6.0),
            ( 33.6, -6.0),
            ( 33.6, 12.0),
        ],
        drill=1.1,
        pad=3,
    )


if __name__ == '__main__':
    make_meanwell_irm_30()
    make_meanwell_irm_45()
    make_meanwell_irm_60()
    make_hilink_hlk_pm01()
    make_hilink_hlk_5m01()

