# This module is built on top of the kicad-footprint-generator framework
# by Thomas Pointhuber, https://github.com/pointhi/kicad-footprint-generator
#
# This module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.

#
# (C) 2020 Cedric de Wijs, <https://gitlab.com/Cedric5008>
#
#!/usr/bin/env python3

import sys
import os
#sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path

# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from math import floor
import argparse
import yaml
from helpers import *
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields
from footprint_keepout_area import addRectangularKeepout

pinrange = range(4, 22, 2) #4,22,2 produces 4,6,8,10,12,14,16,18,20. It does not include 22

series = "MICRO-MATCH SMD FTE"
series_long = ('TE Connectivity 1.27mm Pitch Micro-MaTch, ' +
               'Female-On-Board SMD')
manufacturer = 'TE Connectivity'
orientation = 'V'
number_of_rows = 2

conn_category = "MICROMATCH"

lib_by_conn_category = True

part_code = "{:01d}-188275-{:01d}"

pitch = 1.27
pad_size_x = 1.5
pad_size_y = 3.0
y_offset_between_rows = pad_size_y+1.5

y_centerline_offset_from_pin1 = y_offset_between_rows/2 #replace

y_total_pin_size = pad_size_y + y_offset_between_rows


b20_size_from_datasheet = 27.5  #B size in datasheet is rounded, this is the max value, taken from the 20 pin model
x_overhang_from_middle_of_pin = (b20_size_from_datasheet - 19 * pitch) / 2
y_body_size = 5.2

y_component_value_offset = 7.3

datasheet = 'https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Customer+Drawing%7F188275%7FS4%7Fpdf%7FEnglish%7FENG_CD_188275_S4.pdf%7F2-188275-0'

def make_module(pin_count, configuration):

	mpn = part_code.format(int(floor(pin_count/10)),(pin_count%10))
		
	orientation_str = configuration['orientation_options'][orientation]
	footprint_name = configuration['fp_name_format_string'].format(
		man = manufacturer,
		series = series,
		mpn = mpn,
		num_rows = number_of_rows,
		pins = pin_count,
		pins_per_row = int(floor(pin_count/2)),
		mounting_pad = "",
		pitch = pitch,
		orientation = orientation_str)
	
	footprint_name = footprint_name.replace(" ",'_')
	footprint_name = footprint_name.replace("__",'_')

	kicad_mod = Footprint(footprint_name, FootprintType.SMD)
	kicad_mod.setAttribute('smd')
	kicad_mod.setDescription(
		("Molex {:s}, {:s}, {:d} Circuits ({:s}), " +
		 "generated with kicad-footprint-generator").format(
		series_long, mpn, pin_count, datasheet)) #todo adjust
	kicad_mod.setTags(configuration['keyword_fp_string'].format(
		man=manufacturer,
		series=series,
		orientation=orientation_str,
		entry=configuration['entry_direction'][orientation]))

	

	pad_silk_off = (configuration['silk_pad_clearance'] +
		(configuration['silk_line_width'] / 2))
	fab_silk_off = configuration['silk_fab_offset']
	silk_pad_clearance = configuration['silk_pad_clearance']
	silk_line_width = configuration['silk_line_width']

	x_centerline_offset_from_pin1 = (pin_count/2)*2.54 - pitch/2
	x_pin1_offset_from_center = -(pin_count/2-0.5)*pitch

	## Pads ##
			
	kicad_mod.append(
		PadArray(start = [x_pin1_offset_from_center, -y_offset_between_rows/2],
			initial = 1,
			increment = 2,
			pincount = int(floor(pin_count/2)),
			x_spacing = pitch*2,
			type = Pad.TYPE_SMT,
			shape = Pad.SHAPE_RECT,
			size = [pad_size_x,pad_size_y],
			#size = pad_size,
			layers = Pad.LAYERS_SMT))
			
	kicad_mod.append(
		PadArray(start = [x_pin1_offset_from_center+pitch, y_offset_between_rows/2],
			initial = 2,
			increment = 2,
			pincount = int(floor(pin_count/2)),
			x_spacing = pitch*2,
			type = Pad.TYPE_SMT,
			shape = Pad.SHAPE_RECT,
			size = [pad_size_x,pad_size_y],
			layers = Pad.LAYERS_SMT))

	## Fab ##
	
	fab_body_outline = [
		{'x': -x_overhang_from_middle_of_pin+x_pin1_offset_from_center,'y': (-y_body_size/2)}, #bot left
		{'x': -x_overhang_from_middle_of_pin+x_pin1_offset_from_center,'y': (y_body_size/2)}, #top left
		{'x': (pin_count-1)*pitch+x_overhang_from_middle_of_pin+x_pin1_offset_from_center,'y': (y_body_size/2)}, #top right
		{'x': (pin_count-1)*pitch+x_overhang_from_middle_of_pin+x_pin1_offset_from_center,'y': (-y_body_size/2)}, #bot right
		{'x': -x_overhang_from_middle_of_pin+x_pin1_offset_from_center,'y': (-y_body_size/2)}, #bot left again, close the rect
	]

	kicad_mod.append(PolygoneLine(
		polygone = fab_body_outline,
		layer = 'F.Fab',
		width = configuration['fab_line_width']))

	fab_pin1_mark = [
		{'x': - 0.5+x_pin1_offset_from_center, 'y': -y_body_size/2},
		{'x': x_pin1_offset_from_center, 'y': -y_body_size/2+0.75},
		{'x': 0.5+x_pin1_offset_from_center, 'y': -y_body_size/2}
	]

	kicad_mod.append(PolygoneLine(
		polygone = fab_pin1_mark,
		layer = 'F.Fab',
		width = configuration['fab_line_width']))




	## SilkS ##
		
	# pin1 designator and leftside outline
	silk_outline_pin1 = [
		{'x': -pad_size_x/2-silk_pad_clearance-silk_line_width/2+x_pin1_offset_from_center ,'y': -y_centerline_offset_from_pin1-pad_size_y/2}, #top of pin1 designator
		{'x': -pad_size_x/2-silk_pad_clearance-silk_line_width/2+x_pin1_offset_from_center ,'y': -y_body_size/2}, #top of body
		{'x': -x_overhang_from_middle_of_pin+x_pin1_offset_from_center ,'y': -y_body_size/2}, #left top edge of the body
		{'x': -x_overhang_from_middle_of_pin+x_pin1_offset_from_center ,'y': - y_body_size/4}, #one quarter bodysize down
		{'x': -x_overhang_from_middle_of_pin+y_body_size/8+x_pin1_offset_from_center ,'y': - y_body_size/4}, #1/8 of bodysize in
		{'x': -x_overhang_from_middle_of_pin+y_body_size/8+x_pin1_offset_from_center ,'y': + y_body_size/4}, #1/2 bodysize down
		{'x': -x_overhang_from_middle_of_pin+x_pin1_offset_from_center ,'y': y_body_size/4}, #1/8 of bodysize out
		{'x': -x_overhang_from_middle_of_pin+x_pin1_offset_from_center ,'y': y_body_size/2}, #left bot edge of the body
		{'x': pitch-pad_size_x/2-silk_pad_clearance-silk_line_width/2+x_pin1_offset_from_center  ,'y': y_body_size/2}, #pin 2
	]

	kicad_mod.append(PolygoneLine(
		polygone = silk_outline_pin1,
		layer = 'F.SilkS',
		width = configuration['silk_line_width']))
	
	# rightside outline
	silk_outline_right = [
		{'x': x_pin1_offset_from_center+(pin_count-2)*pitch+pad_size_x/2+silk_pad_clearance+silk_line_width/2  ,'y': (-y_body_size/2)}, #top last pin
		{'x': x_pin1_offset_from_center+(pin_count-1)*pitch+x_overhang_from_middle_of_pin,'y': (-y_body_size/2)}, #top right
		{'x': x_pin1_offset_from_center+(pin_count-1)*pitch+x_overhang_from_middle_of_pin,'y': (y_body_size/2)}, #bot right
		{'x': x_pin1_offset_from_center+(pin_count-1)*pitch+pad_size_x/2+silk_pad_clearance+silk_line_width/2 ,'y': (y_body_size/2)}, #bot last pin
	]
	
	kicad_mod.append(PolygoneLine(
		polygone = silk_outline_right,
		layer = 'F.SilkS',
		width = configuration['silk_line_width']))

	# set general values
	kicad_mod.append(Text(type='reference', text='REF**', at=[x_centerline_offset_from_pin1, -3], layer='F.SilkS'))


	## CrtYd ##

	bounding_box = {
		'top': (-y_total_pin_size/2),
		'left': x_pin1_offset_from_center-x_overhang_from_middle_of_pin,
		'bottom': (y_total_pin_size/2),
		'right': (x_pin1_offset_from_center+(pin_count-1)*pitch+x_overhang_from_middle_of_pin)}

	cx1 = roundToBase(bounding_box['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
	cy1 = roundToBase(bounding_box['top']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

	cx2 = roundToBase(bounding_box['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
	cy2 = roundToBase(bounding_box['bottom']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

	kicad_mod.append(RectLine(
		start=[cx1, cy1], end=[cx2, cy2],
		layer='F.CrtYd', width=configuration['courtyard_line_width']))

	## Text ##
	
	addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=bounding_box, courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center')


	##################### Output and 3d model ############################
	model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')

	if lib_by_conn_category:
		lib_name = configuration['lib_name_specific_function_format_string'].format(category=conn_category)
	else:
		lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)

	model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
		model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
	kicad_mod.append(Model(filename=model_name))

	output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
	if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
		os.makedirs(output_dir)
	filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

	file_handler = KicadFileHandler(kicad_mod)
	file_handler.writeFile(filename)
	


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../conn_config_KLCv3.yaml')
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.series_config, 'r') as config_stream:
        try:
            configuration.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    for pincount in pinrange:
        make_module(pincount, configuration)
