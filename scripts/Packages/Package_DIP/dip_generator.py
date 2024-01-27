#!/usr/bin/env python

import sys
import os
from copy import deepcopy
import argparse
import yaml
import logging
from typing import Union, List

# ensure that the kicad-footprint-generator directory is available
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))

from KicadModTree import Vector2D
from scripts.tools.dict_tools import dictInherit
from scripts.tools.footprint_scripts_DIP import makeDIP


class DIPConfiguration:
    """
    Type-safe representation of a DIP footprint configuration
    """
    pins: int
    pitch_x: float
    pitch_y: float
    body_size: Vector2D
    drill: float
    pad_size: Vector2D
    package_type: str
    package_tags: list
    standard: Union[str, None]
    description: str
    additional_tags: List[str]
    socket_size_outset: Union[Vector2D, None]

    def __init__(self, spec):
        self.pins = spec['pins']
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
        self.additional_tags = spec.get('additional_tags', [])
        self.socket_size_outset = self._get_socket_size_outset(spec)

        assert self.pins % 2 == 0
        assert self.drill > 0

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
    config.additional_tags.append('LongPads')


def adjust_config_for_socket(config: DIPConfiguration, socket_size_outset: Vector2D) -> None:
    """
    Amend a DIP configuration to add space for a socket

    Args:
        base_spec (dict): footprint spec of the "base" footprint
        socket_size_outset (Vector2D): how much bigger the socket is than the base footprint
    """
    config.socket_size_outset = socket_size_outset
    config.additional_tags.append('Socket')


class DipGenerator:

    def __init__(self):

        # "standard" value for larger pads -> 1.6mm to 2.4mm
        # Eventually would be good to make this a parameter of a 'policy'
        # that drives the footprint generation (along with, say, IPA densities)
        # on top of the base spec values
        self.longpad_size_delta = Vector2D(0.8, 0)

        # Again, would be good to make this a parameter of a 'policy'
        self.socket_size_outset = Vector2D(2.54, 2.54)

    def make_from_config(self, config: DIPConfiguration):
        """
        Construct a footprint from a DIPConfiguration object
        """

        # Munge the geometry into what makeDIP wants

        pin_row_length = (config.pins / 2 - 1) * config.pitch_y
        overlen_total = config.body_size.y - pin_row_length

        if config.socket_size_outset is None:
            socket_width = 0
            socket_height = 0
        else:
            socket_width = config.pitch_x + config.socket_size_outset.x
            socket_height = (config.pins / 2 - 1) * config.pitch_y + config.socket_size_outset.y

        args = {
            'pins': config.pins,
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
            'tags_additional': config.additional_tags,
            'DIPName': config.package_type,
            'DIPTags': ' '.join(config.package_tags),
        }

        desc = [config.description]

        if config.standard:
            desc.append(config.standard)

        args['DIPDescription'] = ', '.join(desc)

        makeDIP(**args)

    def make_all_variants_from_spec(self, spec: dict):

        dip_config = DIPConfiguration(spec)

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

            self.make_from_config(variant_config)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Use .yaml files to create DIP footprints.')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of files holding information about what devices should be created.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase output verbosity')

    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    dip_generator = DipGenerator()

    for filepath in args.files:
        with open(filepath, 'r') as command_stream:
            try:
                cmd_file = yaml.safe_load(command_stream)
            except yaml.YAMLError as exc:
                print(exc)

        dictInherit(cmd_file)

        for pkg_key, spec in cmd_file.items():

            if pkg_key.startswith('base') or pkg_key.startswith('defaults'):
                continue

            logging.info("Generating part for parameter set {}".format(pkg_key))
            dip_generator.make_all_variants_from_spec(spec)
