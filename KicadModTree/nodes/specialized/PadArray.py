#!/usr/bin/env python

# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2017 by @SchrodingersGat
# (C) 2017 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

from collections import namedtuple
from types import GeneratorType
from typing import Generator

from KicadModTree.nodes.base.Pad import *
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.specialized.ChamferedPad import *

ApplyOverrideResult = namedtuple('ApplyOverrideResult', ['number', 'position', 'parameters'])


class PadArray(Node):
    r"""Add a row of Pads

    Simplifies the handling of pads which are rendered in a specific form

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *start* (``Vector2D``) --
          start edge of the pad array
        * *center* (``Vector2D``) --
          center pad array around specific point
        * *pincount* (``int``) --
          number of pads to render
        * *spacing* (``Vector2D``, ``float``) --
          offset between rendered pads
        * *x_spacing* (``float``) --
          x offset between rendered pads
        * *y_spacing* (``float``) --
          y offset between rendered pads
        * *initial* (``int``) --
          name of the first pad
        * *increment* (``int, function(previous_number)``) --
          declare how the name of the follow up is calculated
        * *type* (``Pad.TYPE_THT``, ``Pad.TYPE_SMT``, ``Pad.TYPE_CONNECT``, ``Pad.TYPE_NPTH``) --
          type of the pad
        * *shape* (``Pad.SHAPE_CIRCLE``, ``Pad.SHAPE_OVAL``, ``Pad.SHAPE_RECT``, ``Pad.SHAPE_TRAPEZE``, ...) --
          shape of the pad
        * *rotation* (``float``) --
          rotation of the pad
        * *size* (``float``, ``Vector2D``) --
          size of the pad
        * *offset* (``Vector2D``) --
          offset of the pad
        * *drill* (``float``, ``Vector2D``) --
          drill-size of the pad
        * *solder_paste_margin_ratio* (``float``) --
          solder paste margin ratio of the pad
        * *layers* (``Pad.LAYERS_SMT``, ``Pad.LAYERS_THT``, ``Pad.LAYERS_NPTH``) --
          layers on which are used for the pad
        * *chamfer_corner_selection_first* (``[bool, bool, bool, bool]``)
          Select which corner should be chamfered for the first pad. (default: None)
        * *chamfer_corner_selection_last* (``[bool, bool, bool, bool]``)
          Select which corner should be chamfered for the last pad. (default: None)
        * *chamfer_size* (``float``, ``Vector2D``) --
          size for the chamfer used for the end pads. (default: None)

        * *end_pads_size_reduction* (``dict with keys x-,x+,y-,y+``) --
          size is reduced on the given side. (size reduced plus center moved.)
        * *tht_pad1_shape* (``Pad.SHAPE_RECT``, ``Pad.SHAPE_ROUNDRECT``, ...) --
          shape for marking pad 1 for through hole components. (default: ``Pad.SHAPE_ROUNDRECT``)
        * *tht_pad1_id* (``int, string``) --
          pad number used for "pin 1" (default: 1)
        * *hidden_pins* (``Iterable[int]``) --
          pin number(s) to be skipped; a footprint with hidden pins has missing pads and matching pin numbers
        * *deleted_pins* (``int, Vector1D``) --
          pin locations(s) to be skipped; a footprint with deleted pins has pads missing but no missing pin numbers"


    :Example:

    >>> from KicadModTree import *
    >>> PadArray(pincount=10, spacing=[1,-1], center=[0,0], initial=5, increment=2,
    ...          type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=[1,2], layers=Pad.LAYERS_SMT)
    """

    startingPosition: Vector2D
    spacing: Vector2D

    def __init__(self, **kwargs):
        Node.__init__(self)
        self._initPincount(**kwargs)
        self._initIncrement(**kwargs)
        self._initInitialNumber(**kwargs)
        self._initSpacing(**kwargs)
        self._initStartingPosition(**kwargs)
        self.virtual_childs = self._createPads(**kwargs)

    # How many pads in the array
    def _initPincount(self, **kwargs):
        if not kwargs.get('pincount'):
            raise KeyError('pincount not declared (like "pincount=10")')
        self.pincount = kwargs.get('pincount')
        if type(self.pincount) is not int or self.pincount <= 0:
            raise ValueError('{pc} is an invalid value for pincount'.format(pc=self.pincount))

        if kwargs.get('hidden_pins') and kwargs.get('deleted_pins'):
            raise KeyError('hidden pins and deleted pins cannot be used together')

        self.exclude_pin_list = []
        if kwargs.get('hidden_pins'):
            # exclude_pin_list is for pads being removed based on pad number
            # deleted pins are filtered out later by pad location (not number)
            self.exclude_pin_list = kwargs.get('hidden_pins')

            if type(self.exclude_pin_list) not in [list, tuple]:
                raise TypeError('hidden pin list must be specified like "hidden_pins=[0,1]"')
            elif any([type(i) not in [int] for i in self.exclude_pin_list]):
                raise ValueError('hidden pin list must contain integer values')

    # Where to start the array
    def _initStartingPosition(self, **kwargs):
        """
        can use the 'start' argument to start a pad array at a given position
        OR
        can use the 'center' argument to center the array around the given position
        """
        self.startingPosition = Vector2D(0, 0)

        # Start takes priority
        if kwargs.get('start'):
            self.startingPosition = Vector2D(kwargs.get('start'))
        elif kwargs.get('center'):
            center = Vector2D(kwargs.get('center'))

            # Now calculate the desired starting position of the array
            self.startingPosition.x = center.x - (self.pincount - 1) * self.spacing.x / 2.
            self.startingPosition.y = center.y - (self.pincount - 1) * self.spacing.y / 2.

    # What number to start with?
    def _initInitialNumber(self, **kwargs):
        self.initialPin = kwargs.get('initial', 1)
        if self.initialPin == "":
            self.increment = 0
        elif type(self.initialPin) is not int or self.initialPin < 1:
            if not callable(self.increment):
                raise ValueError('{pn} is not a valid starting pin number if increment is not a function'
                                 .format(pn=self.initialPin))

    # Pin incrementing
    def _initIncrement(self, **kwargs):
        self.increment = kwargs.get('increment', 1)

    # Pad spacing
    def _initSpacing(self, **kwargs):
        """
        spacing can be given as:
        spacing = [1,2] # high priority
        x_spacing = 1
        y_spacing = 2
        """
        self.spacing = Vector2D(0, 0)

        if kwargs.get('spacing'):
            self.spacing = Vector2D(kwargs.get('spacing'))
            return

        if kwargs.get('x_spacing'):
            self.spacing.x = kwargs.get('x_spacing')

        if kwargs.get('y_spacing'):
            self.spacing.y = kwargs.get('y_spacing')

        if self.spacing.x == 0 and self.spacing.y == 0:
            raise ValueError('pad spacing ({self.spacing}) must be non-zero')

    def _applyOverrides(self,
                        pad_number: int,
                        pad_position,
                        pad_parameters,
                        pad_overrides) -> ApplyOverrideResult:
        """
        Apply pad overrides to the current pad position and parameters.
        """
        # No overrides? Just return input
        if pad_overrides is None:
            return ApplyOverrideResult(pad_number, pad_position, pad_parameters)

        # Check if pad number is in dictionary
        this_pad_override = pad_overrides.overrides.get(pad_number)

        # No overrides for this pad? Just return input
        if this_pad_override is None:
            return ApplyOverrideResult(pad_number, pad_position, pad_parameters)

        #
        # Copy input variables
        # (to avoid changing the outer state)
        #
        pad_position = list(pad_position)  # copy
        pad_parameters = dict(pad_parameters)
        # Not all parameters are deep copyable,
        # so we only copy what might change
        if isinstance(pad_parameters["size"], list):
            pad_parameters["size"] = \
                list(pad_parameters["size"])

        # Apply relative move:
        # {'pad_override': {1: {"move": [0.1, 0.0]}}}
        if this_pad_override.move:
            if this_pad_override.move[0] is not None:
                pad_position[0] += this_pad_override.move[0]
            if this_pad_override.move[1] is not None:
                pad_position[1] += this_pad_override.move[1]

        # Apply "absolute" position transformation ("set position")
        # {'pad_override': {1: {"at": [0.1, 0.0]}}}
        # Any of the coordinates can be set to None to ignore that coordinate.
        if this_pad_override.at:
            if this_pad_override.at[0] is not None:
                pad_position[0] = this_pad_override.at[0]
            if this_pad_override.at[1] is not None:
                pad_position[1] = this_pad_override.at[1]

        # Apply "size_increase" relative size change
        # {'pad_override': {1: {"size_increase": [0.1, -0.5]}}}
        if this_pad_override.size_increase:
            if this_pad_override.size_increase[0] is not None:
                pad_parameters['size'][0] += this_pad_override.size_increase[0]
            if this_pad_override.size_increase[1] is not None:
                pad_parameters['size'][1] += this_pad_override.size_increase[1]

        # Apply "size" absolute override
        # {'pad_override': {1: {"size": [1.5, 0.7]}}}
        # Any of the coordinates can be set to None to ignore that coordinate.
        if this_pad_override.size:
            if this_pad_override.size[0] is not None:
                pad_parameters['size'][0] = this_pad_override.size[0]
            if this_pad_override.size[1] is not None:
                pad_parameters['size'][1] = this_pad_override.size[1]

        # Apply "number" override
        # {'pad_override': {1: {"override_numbers": "B6"}}}
        # Pleeease use this only as a way of last resort :-)
        pad_number = this_pad_override.override_number or pad_number

        return ApplyOverrideResult(pad_number, pad_position, pad_parameters)

    def _createPads(self, **kwargs):

        pads = []
        padShape = kwargs.get('shape')

        end_pad_params = copy(kwargs)
        if kwargs.get('end_pads_size_reduction'):
            size_reduction = kwargs['end_pads_size_reduction']
            end_pad_params['size'] = toVectorUseCopyIfNumber(kwargs.get('size'), low_limit=0)

            delta_size = Vector2D(
                size_reduction.get('x+', 0) + size_reduction.get('x-', 0),
                size_reduction.get('y+', 0) + size_reduction.get('y-', 0)
                )

            end_pad_params['size'] -= delta_size

            delta_pos = Vector2D(
                -size_reduction.get('x+', 0) + size_reduction.get('x-', 0),
                -size_reduction.get('y+', 0) + size_reduction.get('y-', 0)
                )/2
        else:
            delta_pos = Vector2D(0, 0)

        # Special case, increment = 0
        # this can be used for creating an array with all the same pad number
        if self.increment == 0:
            pad_numbers = [self.initialPin] * self.pincount
        elif isinstance(self.increment, int):
            pad_numbers = range(self.initialPin, self.initialPin + (self.pincount * self.increment), self.increment)
        elif callable(self.increment):
            pad_numbers = [self.initialPin]
            for idx in range(1, self.pincount):
                pad_numbers.append(self.increment(pad_numbers[-1]))
        elif isinstance(self.increment, GeneratorType):
            pad_numbers = [next(self.increment) for i in range(self.pincount)]
        else:
            raise TypeError("Wrong type for increment. It must be either an int, callable or generator.")

        for i, number in enumerate(pad_numbers):
            includePad = True

            # deleted pins are filtered by pad/pin position (they are 'None' in pad_numbers list)
            if not isinstance(number, (int, str)):
                includePad = False

            # hidden pins are filtered out by pad number (index of pad_numbers list)
            if kwargs.get('hidden_pins'):
                includePad = number is not None and number not in self.exclude_pin_list

            if includePad:
                current_pad_pos = Vector2D(
                    self.startingPosition.x + i * self.spacing.x,
                    self.startingPosition.y + i * self.spacing.y,
                    )
                current_pad_params = copy(kwargs)
                if i == 0 or i == len(pad_numbers)-1:
                    current_pad_pos += delta_pos
                    current_pad_params = end_pad_params
                if kwargs.get('type') == Pad.TYPE_THT and number == kwargs.get('tht_pad1_id', 1):
                    current_pad_params['shape'] = kwargs.get('tht_pad1_shape', Pad.SHAPE_ROUNDRECT)
                    if 'radius_ratio' not in current_pad_params:
                        current_pad_params['radius_ratio'] = 0.25
                    if 'maximum_radius' not in current_pad_params:
                        current_pad_params['maximum_radius'] = 0.25
                else:
                    current_pad_params['shape'] = padShape

                pad_params_with_override = self._applyOverrides(
                    number, current_pad_pos, current_pad_params,
                    kwargs.get("pad_overrides")
                )

                if kwargs.get('chamfer_size'):
                    if i == 0 and 'chamfer_corner_selection_first' in kwargs:
                        pads.append(
                            ChamferedPad(
                                number=pad_params_with_override.number,
                                at=pad_params_with_override.position,
                                corner_selection=kwargs.get('chamfer_corner_selection_first'),
                                **pad_params_with_override.parameters
                                ))
                        continue
                    if i == len(pad_numbers)-1 and 'chamfer_corner_selection_last' in kwargs:
                        pads.append(
                            ChamferedPad(
                                number=pad_params_with_override.number,
                                at=pad_params_with_override.position,
                                corner_selection=kwargs.get('chamfer_corner_selection_last'),
                                **pad_params_with_override.parameters
                                ))
                        continue

                # A normal unchamfered pad

                # TODO: This is a hack - assuming the PadArray kwargs must be valid for
                # all the pads, chamfered or not, seems dangerously implicit.
                if "chamfer_size" in pad_params_with_override.parameters:
                    pad_params_with_override.parameters.pop("chamfer_size")

                pads.append(Pad(number=pad_params_with_override.number,
                                at=pad_params_with_override.position,
                                **pad_params_with_override.parameters))

        for pad in pads:
            pad._parent = self

        return pads

    def getVirtualChilds(self):
        return self.virtual_childs

    def get_pads(self) -> Generator[Pad, None, None]:
        """
        Yields all pads in the array, one by one.
        """
        for pad in self.virtual_childs:
            if isinstance(pad, Pad):
                yield pad

    def get_pad_with_name(self, number: str | int) -> Pad | None:
        for pad in self.virtual_childs:
            if pad.number == number:
                return pad
        return None


def get_pad_radius_from_arrays(pad_arrays: list[PadArray]) -> float:
    pad_radius = 0.0
    for pa in pad_arrays:
        if (pad_radius == 0.0):
            pads = pa.getVirtualChilds()
            if (len(pads)):
                pad_radius = pads[0].getRoundRadius()
    return pad_radius


def find_lowest_numbered_pad(pad_arrays: list[PadArray]) -> Pad | None:
    """
    From a list of pad arrays, find the lowest-integer-numbered pad.
    """

    lowest_pad: Pad | None = None

    for pad_array in pad_arrays:
        for pad in pad_array:
            try:
                int_num = int(pad.number)
            except ValueError:
                # If the pad number is not an int, skip it
                continue

            if lowest_pad is None or int_num < int(lowest_pad.number):
                lowest_pad = pad

    return lowest_pad
