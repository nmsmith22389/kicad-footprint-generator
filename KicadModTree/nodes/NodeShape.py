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
# (C) The KiCad Librarian Team

"""Class definition for the shape node."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

from KicadModTree.nodes.Node import Node
from KicadModTree.util import LineStyle
from kilibs.geom import (
    MIN_SEGMENT_LENGTH,
    TOL_MM,
    BoundingBox,
    GeomArc,
    GeomCircle,
    GeomCompoundPolygon,
    GeomCross,
    GeomCruciform,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomRoundRectangle,
    GeomShape,
    GeomShapeClosed,
    GeomStadium,
    GeomTrapezoid,
    Vector2D,
)


class NodeShape(Node, GeomShape):
    """A node class for shapes."""

    layer: str
    """The layer on which the node is drawn."""
    width: float | None
    """The width of the outline of the shape."""
    style: LineStyle
    """The line style used to draw the outline of the shape."""
    fill: bool
    """Whether the shape is filled, `False` for open shapes."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
    ) -> None:
        """Create a `NodeShape`.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the rectangle is filled, `False` if only the outline is
                visible. `False` for open shapes.
        """
        Node.__init__(self)
        self.layer = layer
        self.width = width
        self.style = style
        self.fill = fill

    def copy(self) -> Self:
        """Creates a copy of itself."""
        if isinstance(self, GeomShapeClosed):
            copy = self.__class__(
                shape=self,  # pyright: ignore
                layer=self.layer,
                width=self.width,
                style=self.style,
                fill=self.fill,
            )
        else:
            copy = self.__class__(
                shape=self,  # type: ignore
                layer=self.layer,
                width=self.width,
                style=self.style,
            )
        copy._parent = self._parent
        return copy

    def copy_with(
        self,
        shape: Self | None = None,
        layer: str | None = None,
        width: float | None = None,
        style: object | None = None,
        fill: bool | None = None,
        offset: float | None = None,
    ) -> Self:
        """Creates a copy of itself using the given parameters instead of the original ones.

        Args:
            shape: Use the shape given as parameter instead of the original one.
            layer: Use the layer given as parameter instead of the original one.
            width: Use the width given as parameter instead of the original one.
            style: Use the style given as parameter instead of the original one.
            fill: Use the fill type given as parameter instead of the original one.
            ofsset: inflate/deflate the shape by this amount.
        """
        params: dict[str, Any] = {}
        shape = shape if shape else self
        if layer or hasattr(self, "layer"):
            params.update({"layer": (layer if layer else self.layer)})
        if width or hasattr(self, "width"):
            params.update({"width": (width if width else self.width)})
        if style or hasattr(self, "style"):
            params.update({"style": (style if style else self.style)})
        if fill or hasattr(self, "fill"):
            params.update({"fill": (fill if fill else self.fill)})
        if offset:
            params.update({"offset": offset})
        return self.__class__(shape=shape, **params)  # type: ignore

    def translate(self, vector: Vector2D) -> Self:
        """Move the node.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated node.
        """
        return super(Node, self).translate(vector=vector)

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the node around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated node.
        """
        return super(Node, self).rotate(angle=angle, origin=origin)

    def cut(  # type: ignore
        self,
        shape_to_cut: NodeShape,
        min_segment_length: float = MIN_SEGMENT_LENGTH,
        tol: float = TOL_MM,
    ) -> list[NodeShape]:
        """Cut the node with another node.

        Args:
            shape_to_cut: Node whose shape is cut with the shape of this node.
            min_segment_length: The minimum length of a segment. If a segment resulting
                from the `cut` operation is shorter than `min_segment_length`, it is
                omitted from the results.
            tol: The tolerance in mm that is used to determine if two points are equal.

        Return:
            Return a list of nodes that result from the cut operation.
        """
        shapes = GeomShape.cut(
            self,
            shape_to_cut=shape_to_cut,
            min_segment_length=min_segment_length,
            tol=tol,
        )
        return NodeShape.to_nodes(
            shapes=shapes,
            layer=shape_to_cut.layer,
            width=shape_to_cut.width,
            style=shape_to_cut.style,
            parent=shape_to_cut._parent,
        )

    def keepout(
        self,
        shape_to_keep_out: NodeShape,
        min_segment_length: float = MIN_SEGMENT_LENGTH,
        tol: float = TOL_MM,
    ) -> list[NodeShape]:
        """Treat this node as if it was a keepout and apply it to the node given as
        argument.

        Args:
            shape_to_keep_out: The node that is to be kept out of the keepout.
            min_segment_length: The minimum length of a segment. If a segment resulting
                from the keepout operation is shorter than `min_segment_length`, it is
                omitted from the results.
            tol: The tolerance in mm that is used to determine if two points are equal.

        Returns:
            If `shape_to_keep_out` is fully outside of this closed shape, then a list
            containing `shape_to_keep_out` is returned. If `shape_to_keep_out` is fully
            inside of this closed shape, then an empty list is returned. Otherwise,
            `shape_to_keep_out` is decomposed to its atomic nodes and a list containing
            the parts of the atomic nodes that are not inside the keepout is returned.
        """
        if isinstance(self, GeomShapeClosed):
            shapes = GeomShapeClosed.subtract(
                self,
                shape_to_keep_out=shape_to_keep_out,
                min_segment_length=min_segment_length,
                tol=tol,
            )
            return NodeShape.to_nodes(
                shapes=shapes,
                layer=shape_to_keep_out.layer,
                width=shape_to_keep_out.width,
                style=shape_to_keep_out.style,
                parent=None,
            )
        else:
            return [shape_to_keep_out]

    def to_child_node(self, shape: GeomShape) -> NodeShape:
        """Converts a geometric shape to its corresponding node class and sets the
        properties `layer`, `width` and `style` equal to the ones of this `NodeShape`
        and `_parent` to this `NodeShape`."""
        node = NodeShape.to_node(
            shape=shape,
            layer=self.layer,
            width=self.width,
            style=self.style,
            fill=self.fill,
            parent=self._parent,
        )
        node._parent = self
        return node

    def to_child_nodes(self, shapes: Sequence[GeomShape]) -> list[NodeShape]:
        """Converts a list of geometric shapes  to its corresponding node class and sets
        the properties `layer`, `width` and `style` equal to the ones of this
        `NodeShape` and `_parent` to this `NodeShape`."""
        nodes = NodeShape.to_nodes(
            shapes=shapes,
            layer=self.layer,
            width=self.width,
            style=self.style,
            fill=self.fill,
            parent=self._parent,
        )
        return nodes

    @classmethod
    def to_node(
        cls,
        shape: GeomShape,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        parent: Node | None = None,
    ) -> NodeShape:
        """Converts a geometric shape to its corresponding node class and sets the
        properties `layer`, `width`, `style` and `parent` to the values given as
        argument.

        Args:
            shape: The geometric shape to convert to a `NodeShape`.
            layer: The layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: Whether the shape is filled.
            parent: The parent of the newly created node.
        """
        from KicadModTree.nodes.base import (
            Arc,
            Circle,
            CompoundPolygon,
            Line,
            Polygon,
            Rectangle,
        )
        from KicadModTree.nodes.specialized.Cross import Cross
        from KicadModTree.nodes.specialized.Cruciform import Cruciform
        from KicadModTree.nodes.specialized.RoundRectangle import RoundRectangle
        from KicadModTree.nodes.specialized.Stadium import Stadium
        from KicadModTree.nodes.specialized.Trapezoid import Trapezoid

        # Checking order is ranked by probability of a "hit". First the atomic shapes,
        # then the basic shapes (native to KiCad), then the other shapes:
        node: NodeShape
        if isinstance(shape, GeomLine):
            node = Line(layer=layer, width=width, style=style, shape=shape)
        elif isinstance(shape, GeomArc):
            node = Arc(layer=layer, width=width, style=style, shape=shape)
        elif isinstance(shape, GeomCircle):
            node = Circle(layer=layer, width=width, style=style, fill=fill, shape=shape)
        # Now the basic shapes:
        elif isinstance(shape, GeomRectangle):
            node = Rectangle(
                layer=layer, width=width, style=style, fill=fill, shape=shape
            )
        elif isinstance(shape, GeomPolygon):
            node = Polygon(
                layer=layer, width=width, style=style, fill=fill, shape=shape
            )
        elif isinstance(shape, GeomCompoundPolygon):
            node = CompoundPolygon(
                layer=layer, width=width, style=style, fill=fill, shape=shape
            )
        # Now the special shapes:
        elif isinstance(shape, GeomCross):
            node = Cross(layer=layer, width=width, style=style, shape=shape)
        elif isinstance(shape, GeomCruciform):
            node = Cruciform(
                layer=layer, width=width, style=style, fill=fill, shape=shape
            )
        elif isinstance(shape, GeomRoundRectangle):
            node = RoundRectangle(
                layer=layer, width=width, style=style, fill=fill, shape=shape
            )
        elif isinstance(shape, GeomStadium):
            node = Stadium(
                layer=layer, width=width, style=style, fill=fill, shape=shape
            )
        elif isinstance(shape, GeomTrapezoid):
            node = Trapezoid(
                layer=layer, width=width, style=style, fill=fill, shape=shape
            )
        else:
            raise TypeError("Type not implemented.")
        node._parent = parent
        return node

    @classmethod
    def to_nodes(
        cls,
        shapes: Sequence[GeomShape],
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        parent: Node | None = None,
    ) -> list[NodeShape]:
        """Converts a list of geometric shape to a list of their corresponding node
        class and sets the properties `layer`, `width`, `style` and `parent` to the
        values given as argument.

        Args:
            shapes: The list of geometric shape to convert to a list of `NodeShape`.
            layer: The layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the nodes.
            style: Line style.
            parent: The parent of the newly created nodes.
            fill: Whether the shape is filled.
        """
        child_nodes: list[NodeShape] = []
        for shape in shapes:
            child_node = NodeShape.to_node(
                shape=shape,
                layer=layer,
                width=width,
                style=style,
                fill=fill,
                parent=parent,
            )
            child_nodes.append(child_node)
        return child_nodes

    def bbox(self) -> BoundingBox:
        """Get the bounding box of the node."""
        return super(Node, self).bbox()

    def __repr__(self) -> str:
        """The string representation of the NodeShape."""
        class_name = self.__class__.__name__
        # Start looking for a __repr__ method in the classes that appear after
        # Node in the MRO of the current instance (this will be the class that
        # inherits from GeomShape, e.g. GeomArc, GeomLine, ...):
        node_class = super(Node, self)
        shape = f"shape={node_class.__repr__()}, "
        layer = f"layer={self.layer}, " if hasattr(self, "layer") else ""
        width = f"width={self.width}, " if hasattr(self, "width") else ""
        style = f"style={self.style}, " if hasattr(self, "style") else ""
        fill = f"fill={self.fill}, " if hasattr(self, "fill") else ""
        repr = f"{class_name}({shape}{layer}{width}{style}{fill}".removesuffix(", ")
        repr += ")"
        return repr

    def __str__(self) -> str:
        """The string representation of the NodeShape."""
        return self.__repr__()
