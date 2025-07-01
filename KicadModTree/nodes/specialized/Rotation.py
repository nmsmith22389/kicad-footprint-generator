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

"""Class definition for the rotation node."""

from KicadModTree.nodes.Node import Node
from kilibs.geom import BoundingBox, Vector2D


class Rotation(Node):
    """A rotation that is applied to every child node."""

    angle: float
    """The rotation angle in degrees."""
    origin: Vector2D
    """The coordinates of the point (in mm) around which the child nodes are rotated."""

    def __init__(self, angle: float = 0.0, origin: Vector2D = Vector2D.zero()) -> None:
        """Create a rotation node.

        Args:
            angle: The angle in degrees.
            origin: The coordinates of the point (in mm) around which the child nodes
                are rotated.
        """
        Node.__init__(self)
        self.angle = angle
        self.origin = origin

    def get_flattened_nodes(self) -> list[Node]:
        """Return a list of the rotated copies of all child nodes from the node tree.

        Returns:
            The list of a rotated copy of all child nodes.
        """
        raw_nodes: list[Node] = []
        transformed_nodes: list[Node] = []
        for child in self._children:
            raw_nodes.extend(child.get_flattened_nodes())
        for n in raw_nodes:
            transformed_nodes.append(n.rotated(angle=self.angle, origin=self.origin))
        return transformed_nodes

    def bbox(self) -> BoundingBox:
        """Return the rotated bounding box of every child node."""
        bbox = BoundingBox()
        for child in self._children:
            child_bbox = child.rotated(angle=self.angle, origin=self.origin).bbox()
            bbox.include_bbox(child_bbox)
        return bbox

    def __repr__(self) -> str:
        """The string representation of the rotation."""
        return f"Rotation(angle={self.angle}, origin={self.origin})"
