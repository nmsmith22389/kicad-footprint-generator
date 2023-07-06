#!/usr/bin/env python3

import os
import sys
import math
import argparse
from dataclasses import dataclass
from pathlib import Path

import yaml

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

series = "WR-WST"
orientation = 'V'
number_of_rows = 2

pitch = 2.54

# (pin hole dia, large locator hole dia, small locator hole dia, large locator offset, small locator offset)
dimensions_permanent = (1.4, 2.5, 2.1, 1.33, 2.6)
dimensions_debug = (1.5, 2.6, 2.2, 1.23, 2.5)

@dataclass
class WR_WST:
    tolerance_type: str # Tolerance type (permanent or debug, debug being a bit looser and easier to remove)
    d_pin: float # Inside diameter of pin holes
    d_loc_l: float # Inside diameter of large (pin 1) locator hole
    d_loc_s: float # Inside diameter of small (pin n) locator hole
    offx_loc_l: float # X Offset of large locator hole w.r.t. pin 1
    offx_loc_s: float # X Offset of small locator hole w.r.t. pin n
    annular_ring: float = 0.35/2
    pitch: float = 2.54

    def generate_fp(self, npins, config, lib_name):
        x0, y0 = -(npins-1)*self.pitch/4, self.pitch/2
        w = 8.86 + (npins-1) * self.pitch/2
        h = 5.6

        xn, yn = x0 + (npins-1)*pitch/2, y0 - (npins%2)*pitch

        mpn = f'49010767{npins:02d}12'
        series = f'WR-WST_{self.tolerance_type}'
        or_str = config['orientation_options']['V']
        datasheet = f'https://www.we-online.com/components/products/datasheet/{mpn}.pdf'
        name = config['fp_name_format_string'].format(
                man='Würth',
                series=series,
                mpn=mpn,
                num_rows=2,
                pins_per_row=npins//2,
                mounting_pad='',
                pitch=self.pitch,
                orientation=or_str)

        fp = Footprint(name)
        fp.setDescription(f'Würth WR-WST series direct-to-board connector footprint, {self.tolerance_type} application tolerances, MPN {mpn} {datasheet} Generated with kicad-footprint-generator.')
        fp.setTags(config['keyword_fp_string'].format(
            series=series, orientation=or_str, man='Würth', entry=config['entry_direction']['V']))
        fp.setAttribute('exclude_from_pos_files')
        fp.setAttribute('exclude_from_bom')

        tr_h = 1.5
        sq_h = 0.4
        ## Fabrication layer
        # Outline
        fp.append(RectLine(start=[-w/2, -h/2], end=[w/2, h/2], layer='F.Fab', width=config['fab_line_width']))
        # Pin 1 marker
        fp.append(PolygoneLine(layer='F.Fab', width=config['fab_line_width'], polygone=[
            {'x': x0-tr_h/2, 'y': h/2},
            {'x': x0,        'y': h/2 - tr_h},
            {'x': x0+tr_h/2, 'y': h/2}]))

        ## Silkscreen layer
        # Outline
        fp.append(RectLine(start=[-w/2, -h/2], end=[w/2, h/2], layer='F.SilkS', width=config['silk_line_width']))
        # Pin 1 marker
        fp.append(PolygoneLine(layer='F.SilkS', width=config['silk_line_width'], polygone=[
            {'x': x0-self.d_loc_l-tr_h/2, 'y': h/2},
            {'x': x0-self.d_loc_l,        'y': h/2 - tr_h},
            {'x': x0-self.d_loc_l+tr_h/2, 'y': h/2}]))
        fp.append(PolygoneLine(layer='F.SilkS', width=config['silk_line_width'], polygone=[
            {'x': x0-self.d_loc_l-tr_h/2, 'y': -h/2},
            {'x': x0-self.d_loc_l-tr_h/2, 'y': -h/2 + sq_h},
            {'x': x0-self.d_loc_l+tr_h/2, 'y': -h/2 + sq_h},
            {'x': x0-self.d_loc_l+tr_h/2, 'y': -h/2}]))
        fp.append(PolygoneLine(layer='F.SilkS', width=config['silk_line_width'], polygone=[
            {'x': xn+self.d_loc_s-tr_h/2, 'y': h/2},
            {'x': xn+self.d_loc_s-tr_h/2, 'y': h/2 - sq_h},
            {'x': xn+self.d_loc_s+tr_h/2, 'y': h/2 - sq_h},
            {'x': xn+self.d_loc_s+tr_h/2, 'y': h/2}]))
        
        ## Courtyard
        c_off = config['courtyard_offset']['connector']
        fp.append(RectLine(
            start=[-w/2 - c_off, -h/2 - c_off], end=[w/2 + c_off, h/2 + c_off],
            layer='F.CrtYd', width=config['courtyard_line_width']))

        ## Pins
        for i in range(npins):
            fp.append(Pad(number=f'{i+1}', type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT,
                                 at=[x0 + i*pitch/2, y0 - (i%2)*pitch],
                                 size=self.d_pin + 2*self.annular_ring,
                                 drill=self.d_pin))

        ## Locator holes
        fp.append(Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH,
                             at=[x0-self.offx_loc_l, -pitch/2],
                             size=self.d_loc_l, drill=self.d_loc_l))

        fp.append(Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH,
                             at=[xn+self.offx_loc_s-self.pitch/2, pitch/2 - pitch*(npins%2)],
                             size=self.d_loc_s, drill=self.d_loc_s))

        ## Text fields
        text_center_y = 1.5
        addTextFields(kicad_mod=fp, configuration=config, fp_name=fp.name, text_y_inside_position=text_center_y,
            courtyard={'top': -h/2-c_off, 'bottom': h/2+c_off},
                      body_edges={'left': -w/2, 'right': w/2, 'top': -h/2, 'bottom': h/2})

        # We have no 3D model because this is a PCB-only footprint, and there is nothing soldered to it.

        outdir = Path(f'{lib_name}.pretty')
        outdir.mkdir(exist_ok=True)
        KicadFileHandler(fp).writeFile(str(outdir / f'{fp.name}.kicad_mod'))


wr_wst_perm = WR_WST('permanent',
       d_pin=1.4,
       d_loc_l=2.5,
       d_loc_s=2.1,
       offx_loc_l=1.33,
       offx_loc_s=2.6)

wr_wst_dbg = WR_WST('debug',
       d_pin=1.5,
       d_loc_l=2.6,
       d_loc_s=2.2,
       offx_loc_l=1.23,
       offx_loc_s=2.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../conn_config_KLCv3.yaml')

    args = parser.parse_args()
    config = yaml.safe_load(Path(args.global_config).read_bytes())
    config.update(yaml.safe_load(Path(args.series_config).read_bytes()))

    for npins in range(4, 20, 2):
        wr_wst_perm.generate_fp(npins, config, 'Connector_Wuerth')
        wr_wst_dbg.generate_fp(npins, config, 'Connector_Wuerth')

