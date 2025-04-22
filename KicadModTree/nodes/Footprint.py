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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>


from kilibs.geom import Vector2D
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.EmbeddedFonts import EmbeddedFonts
from KicadModTree.nodes.base.Pad import Pad

from enum import Enum
import uuid
import re

'''
This is my new approach, using a render tree for footprint generation.

ADVANTAGES:

* simple point transformations
* automatic calculation of courtyard,...
* simple duplication of rendering structures

'''

# define in which order the general "lisp" operators are arranged
render_order = ['descr', 'tags', 'attr', 'solder_mask_margin',
                'solder_paste_margin', 'solder_paste_ratio', 'fp_text',
                'fp_circle', 'fp_line', 'pad', 'model']
# TODO: sort Text by type


class FootprintType(Enum):
    UNSPECIFIED = 0
    SMD = 1
    THT = 2


class Footprint(Node):
    '''
    Root Node to generate KicadMod
    '''

    _description: str | None
    _tags: list[str]
    _embedded_fonts: EmbeddedFonts

    zone_connection: Pad.ZoneConnection
    clearance: float | None

    def __init__(self, name: str, footprintType: FootprintType, tstamp_seed: uuid.UUID | None = None):
        """
        :param name: Name of the footprint
        :param footprintType: Type of the footprint (None is the deprecated default)
        """
        Node.__init__(self)

        self.name = name
        self._description = None
        self._tags = []

        # These are attrs in the s-exp, but we can be type-safe here
        # and convert to strings in the file output layer
        self._footprintType = footprintType
        self.not_in_schematic = False
        self.excludeFromBOM = False
        self.excludeFromPositionFiles = False
        self.allow_soldermask_bridges = False
        self.allow_missing_courtyard = False
        self.dnp = False

        self.maskMargin = None
        self.pasteMargin = None
        self.pasteMarginRatio = None

        self.clearance = None
        self.zone_connection = Pad.ZoneConnection.INHERIT

        if tstamp_seed is not None:
            self.getTStampCls().setTStampSeed(tstamp_seed=tstamp_seed)

        # All footprints from v9 have an embedded_fonts node
        # even if it's not enabled
        self._embedded_fonts = EmbeddedFonts()
        self.append(self._embedded_fonts)

    def setName(self, name):
        self.name = name

    @property
    def description(self) -> str | None:
        return self._description

    _COMMA_FIXER_RE = re.compile(r',(\s*,)+')

    @description.setter
    def description(self, description: str) -> None:
        # Many generators have a bad habit of constructing descriptions
        # with hardcoded format strings with comma-separated empty values,
        # which results in cruft like ", , " in the description.
        #
        # Tidy this up here, but one day, this should be an exception and
        # callers should just get it right, becaue magical "helpful" fixes
        # are technical debt with a wig on.

        description = self._COMMA_FIXER_RE.sub(',', description)
        self._description = description

    def setDescription(self, description: str):
        """
        Compatibility setter, use the property instead
        """
        self.description = description

    @property
    def tags(self) -> list:
        return self._tags

    @tags.setter
    def tags(self, tags: list | str) -> None:
        if isinstance(tags, list):
            self._tags = tags
        else:
            self._tags = [tags]

    def setTags(self, tags) -> None:
        """
        Legacy setter
        """
        self.tags = tags

    @property
    def footprintType(self) -> FootprintType:
        return self._footprintType

    @footprintType.setter
    def footprintType(self, footprintType: FootprintType) -> None:
        if not isinstance(footprintType, FootprintType):
            raise TypeError(
                "footprintType must be a FootprintType, not {}".format(type(footprintType)))
        self._footprintType = footprintType

    @property
    def embeddedFonts(self) -> EmbeddedFonts:
        return self._embedded_fonts

    def setMaskMargin(self, value):
        self.maskMargin = value

    def setPasteMargin(self, value):
        self.pasteMargin = value

    def setPasteMarginRatio(self, value):
        # paste_margin_ratio is unitless between 0 and 1 while GUI uses percentage
        assert abs(
            value) <= 1, "Solder paste margin must be between -1 and 1. {} is too large.".format(value)

        self.pasteMarginRatio = value

    def cleanSilkMaskOverlap(self, side: str = 'F', silk_pad_clearance: float = 0.2, silk_line_width: float = 0.12):
        from KicadModTree.util.silkmask_util import cleanSilkOverMask
        cleanSilkOverMask(footprint=self, side=side, silk_pad_clearance=silk_pad_clearance,
                          silk_line_width=silk_line_width)
