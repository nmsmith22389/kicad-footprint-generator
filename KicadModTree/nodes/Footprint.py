# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

"""Class definition for the footprint node."""


import re
import uuid
from enum import Enum

from KicadModTree.nodes.base.EmbeddedFonts import EmbeddedFonts
from KicadModTree.nodes.base.Pad import Pad
from KicadModTree.nodes.Node import Node


class FootprintType(Enum):
    UNSPECIFIED = 0
    SMD = 1
    THT = 2


class Footprint(Node):
    """The root node."""

    name: str
    """Name of the footprint."""
    _description: str | None
    """Description of the footprint."""
    _tags: list[str]
    """Tags of the footprint."""
    _embedded_fonts: EmbeddedFonts
    """Embedded fonts."""
    zone_connection: Pad.ZoneConnection
    """Zone connection."""
    clearance: float | None
    """Clearance of the pads."""
    maskMargin: float | None
    """Mask margin of the pads."""
    pasteMargin: float | None
    """Past margin of the pads."""
    pasteMarginRatio: float | None
    """Past margin ratio of the pads."""
    _footprintType: FootprintType
    """Footprint type."""
    not_in_schematic: bool
    """If `True` the footprint is not in the schematics."""
    excludeFromBOM: bool
    """If `True` the footprint is excluded from the BOM."""
    excludeFromPositionFiles: bool
    """If `True` the footprint is excluded from the position files."""
    allow_soldermask_bridges: bool
    """If `True` solder mask bridges are allowed in the footprint."""
    allow_missing_courtyard: bool
    """If `True` the courtyard can be omitted."""
    dnp: bool
    """If `True` the component is not populated."""

    def __init__(
        self,
        name: str,
        footprint_type: FootprintType,
        tstamp_seed: uuid.UUID | None = None,
    ) -> None:
        """Create a footprint node.

        Args:
            name: Name of the footprint.
            footprint_type: Type of the footprint.
            tstamp_seed: The seed for the time stamp.
        """
        Node.__init__(self)
        self.name = name
        self._description = None
        self._tags = []

        # These are attrs in the s-exp, but we can be type-safe here and convert to
        # strings in the file output layer:
        self._footprintType = footprint_type
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

        # All footprints from v9 have an embedded_fonts node even if it's not enabled.
        self._embedded_fonts = EmbeddedFonts()
        self.append(self._embedded_fonts)

    def get_flattened_nodes(self) -> list[Node]:
        """Return a flattened list of all the child nodes. The child nodes that are
        child of a transform node (Rotation or Translation) are copied and transformed
        before being added to the list."""
        nodes: list[Node] = []
        for child in self.get_child_nodes():
            nodes.extend(child.get_flattened_nodes())
        return nodes

    @property
    def description(self) -> str | None:
        """The optional description of the footprint."""
        return self._description

    _COMMA_FIXER_RE = re.compile(r",(\s*,)+")
    """A regular expression to fix a technical debt with comma-separated empty
    values."""

    @description.setter
    def description(self, description: str) -> None:
        """The optional description of the footprint."""
        # Many generators have a bad habit of constructing descriptions
        # with hardcoded format strings with comma-separated empty values,
        # which results in cruft like ", , " in the description.
        #
        # Tidy this up here, but one day, this should be an exception and
        # callers should just get it right, becaue magical "helpful" fixes
        # are technical debt with a wig on.

        description = self._COMMA_FIXER_RE.sub(",", description)
        self._description = description

    def setDescription(self, description: str) -> None:
        """Legacy setter for the footprint description."""
        self.description = description

    @property
    def tags(self) -> list[str]:
        """The tags of the footprint."""
        return self._tags

    @tags.setter
    def tags(self, tags: list[str] | str) -> None:
        """The tags of the footprint."""
        if isinstance(tags, list):
            self._tags = tags
        else:
            self._tags = [tags]

    def setTags(self, tags: list[str]) -> None:
        """Legacy setter for the tags of the footprint."""
        self.tags = tags

    @property
    def footprintType(self) -> FootprintType:
        """The footprint type."""
        return self._footprintType

    @footprintType.setter
    def footprintType(self, footprintType: FootprintType) -> None:
        """The footprint type."""
        self._footprintType = footprintType

    @property
    def embeddedFonts(self) -> EmbeddedFonts:
        """The embedded font."""
        return self._embedded_fonts

    def setMaskMargin(self, value: float) -> None:
        """Legacy setter for the mask margin."""
        self.maskMargin = value

    def setPasteMargin(self, value: float) -> None:
        """Legacy setter for the paste margin."""
        self.pasteMargin = value

    def setPasteMarginRatio(self, value: float) -> None:
        """Legacy setter for the paste margin ratio."""
        # paste_margin_ratio is unitless between 0 and 1 while GUI uses percentage
        assert (
            abs(value) <= 1
        ), f"Solder paste margin must be between -1 and 1. {value} given."

        self.pasteMarginRatio = value

    def cleanSilkMaskOverlap(
        self,
        side: str = "F",
        silk_pad_clearance: float = 0.2,
        silk_line_width: float = 0.12,
    ) -> None:
        """Clean the silkscreen contours by removing overlap with pads and holes.

        Args:
            side: `'F'` for front or `'B'` for back side of the footprint.
            silk_pad_clearance: The clearance between silk and pad.
            silk_line_width: The line width of the silk screen (used to calculate the
                clearance).
        """
        from KicadModTree.util.silkmask_util import cleanSilkOverMask

        cleanSilkOverMask(
            footprint=self,
            side=side,
            silk_pad_clearance=silk_pad_clearance,
            silk_line_width=silk_line_width,
        )
