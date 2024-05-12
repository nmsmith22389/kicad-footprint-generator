#!/usr/bin/env python

import argparse
import logging
import os
import sys
from copy import deepcopy
from typing import List, Union
from dataclasses import dataclass

# ensure that the kicad-footprint-generator directory is available
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))

from KicadModTree import Vector2D
from scripts.tools.declarative_def_tools import tags_properties
from scripts.tools.dict_tools import dictInherit
from scripts.tools.footprint_generator import FootprintGenerator
from scripts.tools.footprint_scripts_DIP import makeDIP
from scripts.tools.global_config_files.global_config import GlobalConfig


@dataclass
class DIPConfiguration:
    """
    Type-safe representation of a DIP footprint configuration
    """
    pins: List[int]
    pitch_x: float
    pitch_y: float
    body_size: Vector2D
    drill: float
    pad_size: Vector2D
    package_type: str
    package_tags: list
    standard: Union[str, None]
    description: str
    additional_tags: tags_properties.TagsProperties
    socket_size_outset: Union[Vector2D, None]

    def __init__(self, spec):
        self.pins = spec['pins']
        if not isinstance(self.pins, list): # Handle a single pincount
            assert isinstance(self.pins, int)
            self.pins = [self.pins]
        # Various plausibility checks
        assert all(isinstance(pincount, int) for pincount in self.pins)
        assert all(pincount > 0 for pincount in self.pins)
        assert all(pincount % 2 == 0 for pincount in self.pins)
        
        self.pitch_x = spec['pitch_x']
        self.pitch_y = spec['pitch_y']
        self.body_size = Vector2D(spec['body_size_x'], spec['body_size_y'])

        # Eventually, the pad size should be a parameter of a 'policy'
        # based on pin sizes
        self.pad_size = Vector2D(spec['pad_size'])
        self.drill = spec['drill']

        self.package_type = spec['package_type']
        self.package_tags = spec['package_tags']
        self.standard = spec.get('standard', None)
        self.description = spec['description']
        self.datasheet = spec.get('datasheet', None)
        self.additional_tags = tags_properties.TagsProperties(
            spec.get(tags_properties.ADDITIONAL_TAGS_KEY, []))
        self.compatible_mpns = tags_properties.TagsProperties(
            spec.get('compatible_mpns', [])
        )
        self.socket_size_outset = self._get_socket_size_outset(spec)

        # Validate the configuration

    def _get_socket_size_outset(self, spec) -> Union[Vector2D, None]:
        outset = spec.get('socket_size_outset', None)
        return None if outset is None else Vector2D(outset)


def adjust_config_for_longpads(config: DIPConfiguration, longpad_size_delta: Vector2D) -> None:
    """
    Amend a DIP configuration to make the pads longer

    Args:
        base_spec (dict): footprint spec of the "base" footprint
        longpad_size_delta (Vector2D): how much bigger longpads are than base pads
    """
    config.pad_size += longpad_size_delta
    config.additional_tags.tags.append('LongPads')


def adjust_config_for_socket(config: DIPConfiguration, socket_size_outset: Vector2D) -> None:
    """
    Amend a DIP configuration to add space for a socket

    Args:
        base_spec (dict): footprint spec of the "base" footprint
        socket_size_outset (Vector2D): how much bigger the socket is than the base footprint
    """
    config.socket_size_outset = socket_size_outset
    config.additional_tags.tags.append('Socket')

class DIPGenerator(FootprintGenerator):
    def __init__(self, configuration, **kwargs):
        super().__init__(**kwargs)

        # "standard" value for larger pads -> 1.6mm to 2.4mm
        # Eventually would be good to make this a parameter of a 'policy'
        # that drives the footprint generation (along with, say, IPA densities)
        # on top of the base spec values
        self.longpad_size_delta = Vector2D(0.8, 0)

        # Again, would be good to make this a parameter of a 'policy'
        self.socket_size_outset = Vector2D(2.54, 2.54)

    def make_from_config(self, pincount: int, config: DIPConfiguration):
        """
        Construct a footprint from a DIPConfiguration object.
        
        This functions operates on a SINGLE pincount.
        """

        # Munge the geometry into what makeDIP wants

        pin_row_length = (pincount / 2 - 1) * config.pitch_y
        overlen_total = config.body_size.y - pin_row_length

        if config.socket_size_outset is None:
            socket_width = 0
            socket_height = 0
        else:
            socket_width = config.pitch_x + config.socket_size_outset.x
            socket_height = (pincount / 2 - 1) * config.pitch_y + config.socket_size_outset.y

        args = {
            'pins': pincount,
            'rm': config.pitch_y,
            'pinrow_distance_in': config.pitch_x,  # not actuall in inches!
            'package_width': config.body_size.x,
            'overlen_top': overlen_total / 2,
            'overlen_bottom': overlen_total / 2,
            'ddrill': config.drill,
            'pad': config.pad_size,
            'smd_pads': False,
            'socket_width': socket_width,
            'socket_height': socket_height,
            'socket_pinrow_distance_offset': 0,
            'datasheet': config.datasheet,
            'tags_additional': config.additional_tags.tags,
            'DIPName': config.package_type,
            'DIPTags': ' '.join(config.package_tags),
        }

        desc = [config.description]

        if config.standard:
            desc.append(config.standard)

        args['DIPDescription'] = ', '.join(desc)
        
        # Compute output directory
        outdir = self.output_path / 'Package_DIP.pretty'
        os.makedirs(outdir, exist_ok=True)

        makeDIP(**args, outdir=outdir)

    def make_all_variants_from_device_params(self, device_params: dict):

        dip_config = DIPConfiguration(device_params)

        def longpad_mutator(config: DIPConfiguration):
            adjust_config_for_longpads(config, self.longpad_size_delta)

        def socket_mutator(config: DIPConfiguration):
            adjust_config_for_socket(config, self.socket_size_outset)

        # lists of config-mutators to apply in order
        variants = [
            [],
            [longpad_mutator],
            [socket_mutator],
            [longpad_mutator, socket_mutator],
        ]

        for variant in variants:
            # Create a fresh copy of the base config for each variant
            variant_config = deepcopy(dip_config)

            # Then mutate it according to the variant
            for mutator in variant:
                mutator(variant_config)

                # Generate all pincounts                
                for pincount in variant_config.pins:
                    self.make_from_config(pincount, variant_config)

    def generateFootprint(self, device_params: dict, pkg_id: str, header_info: dict = None):
        # Ignore defaults and base packages
        if pkg_id.startswith('base') or pkg_id.startswith('defaults'):
            return

        self.make_all_variants_from_device_params(device_params)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Use .yaml files to create DIP footprints.')
    parser.add_argument('files', metavar='file', type=str, nargs='*',
                        help='list of files holding information about what devices should be created.')
    parser.add_argument('--global_config', type=str, nargs='?',
                        help='the config file defining how the footprint will look like. (KLC)',
                        default='../../tools/global_config_files/config_KLCv3.0.yaml')
    args = FootprintGenerator.add_standard_arguments(parser)
    
    global_config = GlobalConfig.load_from_file(args.global_config)

    FootprintGenerator.run_on_files(
        DIPGenerator,
        args,
        file_autofind_dir='size_definitions',
        configuration=global_config,
    )