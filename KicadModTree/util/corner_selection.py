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
# (C) 2024 KiCad Library Team

class CornerSelection():
    r"""Class for handling corner selection
        :param corner_selection:
            * A list of bools do directly set the corners
              (top left, top right, bottom right, bottom left)
            * A dict with keys (constants see below)
            * The integer 1 means all corners
            * The integer 0 means no corners

        :constants:
            * CornerSelection.TOP_LEFT
            * CornerSelection.TOP_RIGHT
            * CornerSelection.BOTTOM_RIGHT
            * CornerSelection.BOTTOM_LEFT
    """

    TOP_LEFT = 'tl'
    TOP_RIGHT = 'tr'
    BOTTOM_RIGHT = 'br'
    BOTTOM_LEFT = 'bl'

    def __init__(self, corner_selection):
        self.top_left = False
        self.top_right = False
        self.bottom_right = False
        self.bottom_left = False

        if corner_selection == 1:
            self.selectAll()
            return

        if corner_selection == 0 or corner_selection is None:
            return

        if type(corner_selection) is dict:
            for key in corner_selection:
                self[key] = bool(corner_selection[key])
        else:
            for i, value in enumerate(corner_selection):
                self[i] = bool(value)

    def selectAll(self):
        for i in range(len(self)):
            self[i] = True

    def clearAll(self):
        for i in range(len(self)):
            self[i] = False

    def setLeft(self, value=1):
        self.top_left = bool(value)
        self.bottom_left = bool(value)

    def setTop(self, value=1):
        self.top_left = bool(value)
        self.top_right = bool(value)

    def setRight(self, value=1):
        self.top_right = bool(value)
        self.bottom_right = bool(value)

    def setBottom(self, value=1):
        self.bottom_left = bool(value)
        self.bottom_right = bool(value)

    def isAnySelected(self):
        for v in self:
            if v:
                return True
        return False

    def rotateCW(self):
        top_left_old = self.top_left

        self.top_left = self.bottom_left
        self.bottom_left = self.bottom_right
        self.bottom_right = self.top_right
        self.top_right = top_left_old
        return self

    def rotateCCW(self):
        top_left_old = self.top_left

        self.top_left = self.top_right
        self.top_right = self.bottom_right
        self.bottom_right = self.bottom_left
        self.bottom_left = top_left_old
        return self

    def __or__(self, other):
        return CornerSelection([s or o for s, o in zip(self, other)])

    def __ior__(self, other):
        for i in range(len(self)):
            self[i] |= other[i]
        return self

    def __and__(self, other):
        return CornerSelection([s and o for s, o in zip(self, other)])

    def __iand__(self, other):
        for i in range(len(self)):
            self[i] &= other[i]
        return self

    def __len__(self):
        return 4

    def __iter__(self):
        yield self.top_left
        yield self.top_right
        yield self.bottom_right
        yield self.bottom_left

    def __getitem__(self, item):
        if item in [0, CornerSelection.TOP_LEFT]:
            return self.top_left
        if item in [1, CornerSelection.TOP_RIGHT]:
            return self.top_right
        if item in [2, CornerSelection.BOTTOM_RIGHT]:
            return self.bottom_right
        if item in [3, CornerSelection.BOTTOM_LEFT]:
            return self.bottom_left

        raise IndexError('Index {} is out of range'.format(item))

    def __setitem__(self, item, value):
        if item in [0, CornerSelection.TOP_LEFT]:
            self.top_left = bool(value)
        elif item in [1, CornerSelection.TOP_RIGHT]:
            self.top_right = bool(value)
        elif item in [2, CornerSelection.BOTTOM_RIGHT]:
            self.bottom_right = bool(value)
        elif item in [3, CornerSelection.BOTTOM_LEFT]:
            self.bottom_left = bool(value)
        else:
            raise IndexError('Index {} is out of range'.format(item))

    def to_dict(self):
        return {
            CornerSelection.TOP_LEFT: self.top_left,
            CornerSelection.TOP_RIGHT: self.top_right,
            CornerSelection.BOTTOM_RIGHT: self.bottom_right,
            CornerSelection.BOTTOM_LEFT: self.bottom_left
            }

    def __str__(self):
        return str(self.to_dict())
