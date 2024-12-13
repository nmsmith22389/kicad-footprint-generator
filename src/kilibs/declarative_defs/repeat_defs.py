from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generator

from kilibs.geom import Vector2D

from . import evaluable_defs as EDs


@dataclass
class Transformation:
    """
    This is a transformation that can be applied to an object.

    Exactly _how_ the object is transformed is up to the calling code.
    """

    offset: Vector2D | None = None
    """Move the object by this amount."""

    rotation_angle: float | None = None
    """CCW rotation, in degrees"""
    mirror_x: float | None = None
    """
    The object should be mirrored in x about this point
    """
    mirror_y: float | None = None
    """
    The object should be mirrored in y about this point.

    You can set both, which is equivalent to a 180 degree rotation
    about the point (mirror_x, mirror_y), but it may be more convenient
    for the calling code to do 1 or 2 flips.
    """


class Transformer(ABC):
    """
    Some kind of transformation that can be applied to a point.
    """

    @abstractmethod
    def apply(self, pt: Vector2D) -> Transformation:
        """
        Apply the transformation to the point
        """
        raise NotImplementedError("Transformer.apply() must be implemented")


class Translation(Transformer):
    """
    Move the object by a given amount.
    """

    offset: Vector2D

    def __init__(self, offset: Vector2D):
        self.offset = offset

    def apply(self, pt: Vector2D) -> Transformation:
        return Transformation(offset=self.offset)

    def __repr__(self):
        return f"Translation(offset={self.offset})"


class Rotation(Transformer):
    """
    Rotate the object by a given amount.
    """

    rotation_center: Vector2D
    rotation_angle: float
    rotate_elements: bool
    """When true, the returned Transformation includes the rotation angle, otherwise
    it is None and the transformation is just a translation."""

    def __init__(
        self, rotation_center: Vector2D, rotation_angle: float, rotate_elements: bool
    ):
        self.rotation_center = rotation_center
        self.rotation_angle = rotation_angle
        self.rotate_elements = rotate_elements

    def apply(self, pt: Vector2D) -> Transformation:
        vec_to_pt = pt - self.rotation_center
        new_vec = vec_to_pt.with_rotation(self.rotation_angle)

        angle = self.rotation_angle if self.rotate_elements else None
        return Transformation(offset=new_vec - vec_to_pt, rotation_angle=angle)

    def __repr__(self):
        return (
            f"Rotation(center={self.rotation_center}, "
            f"angle={self.rotation_angle}, rotate_elements={self.rotate_elements})"
        )


class Mirror(Transformer):

    mirror_x: float | None
    mirror_y: float | None

    def __init__(self, mirror_x: float | None, mirror_y: float | None):
        self.mirror_x = mirror_x
        self.mirror_y = mirror_y

    def apply(self, pt: Vector2D) -> Transformation:
        new_pt = Vector2D(pt.x, pt.y)
        if self.mirror_x is not None:
            new_pt.x = self.mirror_x - (new_pt.x - self.mirror_x)

        if self.mirror_y is not None:
            new_pt.y = self.mirror_y - (new_pt.y - self.mirror_y)

        return Transformation(offset=new_pt - pt)


class RepeatDef(ABC):
    """
    Some definition that drives a repeat of some kind. Usually a grid, but could be
    circular or something else.

    These are usually constructed from some YAML specification.

    They generate a series of Transformations that should be applied to the object
    by the calling code (exactly what a Transformation does to an object may vary).
    """

    @abstractmethod
    def get_transformations(
        self, expr_evaluator: Callable
    ) -> Generator[Transformation | None, None, None]:
        """
        Yield the offsets for the repeat definition.

        If None is returned, it means "don't transform" for that instance (but there
        might be others coming), and the calling code should include the original object
        as-is.
        """
        raise NotImplementedError("RepeatDefinition.get_offsets() must be implemented")


class GridRepeatDef(RepeatDef):
    """
    The "usual" grid repeater. Repeats in a grid pattern with a given spacing and count.
    """

    spacing: EDs.EvaluableVector2D
    count: EDs.EvaluableVector2Int
    reference_is: str
    omit_indexes: list[EDs.EvaluableVector2Int]

    def __init__(self, spec_dict: dict):
        self.spacing = EDs.EvaluableVector2D(spec_dict["spacing"])
        self.count = EDs.EvaluableVector2Int(spec_dict["count"])

        self.reference_is = spec_dict["reference_is"]

        self.omit_indexes = []
        if "omit" in spec_dict:
            if not isinstance(spec_dict["omit"], list):
                raise ValueError("Grid repeat omit must be a list")

            for omit in spec_dict["omit"]:
                omit_xy = EDs.EvaluableVector2Int(omit)
                self.omit_indexes.append(omit_xy)

    def get_transformations(
        self, expr_evaluator: Callable
    ) -> Generator[Transformation, None, None]:

        # First, resolve the spacing and count expressions
        spacing = self.spacing.evaluate(expr_evaluator)
        count = self.count.evaluate(expr_evaluator)

        size = Vector2D(
            spacing.x * (count[0] - 1),
            spacing.y * (count[1] - 1),
        )

        omits: set[tuple[int, int]] = set()
        for omit in self.omit_indexes:
            omit = omit.evaluate(expr_evaluator)
            omits.add(omit)

        if self.reference_is == "center":
            offset = Vector2D(-size.x / 2, -size.y / 2)
        elif self.reference_is == "left":
            offset = Vector2D(0, -size.y / 2)
        elif self.reference_is == "right":
            offset = Vector2D(-size.x, -size.y / 2)
        elif self.reference_is == "top":
            offset = Vector2D(-size.x / 2, 0)
        elif self.reference_is == "bottom":
            offset = Vector2D(-size.x / 2, -size.y)

        for y in range(count[1]):
            for x in range(count[0]):

                if (x, y) in omits:
                    continue

                grid_pt = Vector2D(x * spacing.x, y * spacing.y)
                transform = Translation(
                    offset=offset + grid_pt,
                )
                yield transform


class CircularRepeatDef(RepeatDef):

    center: EDs.EvaluableVector2D
    count: EDs.EvaluableInt

    def __init__(self, spec_dict: dict):
        self.center = EDs.EvaluableVector2D(spec_dict["center"])
        self.count = EDs.EvaluableInt(spec_dict["count"])

    def get_transformations(
        self, expr_evaluator: Callable
    ) -> Generator[Transformation | None, None, None]:

        center = self.center.evaluate(expr_evaluator)
        count = self.count.evaluate(expr_evaluator)

        # The first one is the original, no transform
        yield None

        for i in range(1, count):
            angle = 360 / count * i
            yield Rotation(
                rotation_center=Vector2D(center.x, center.y),
                rotation_angle=angle,
                rotate_elements=True,
            )


class MirrorRepeatDef(RepeatDef):
    """
    Create a copy of the object mirrored along the x and/or y axis.
    """

    mirror_x: EDs.EvaluableScalar
    """The expression that defines the x-axis mirror. None for no x-axis mirror."""
    mirror_y: EDs.EvaluableScalar
    """The expression that defines the y-axis mirror. None for no y-axis mirror."""

    def __init__(self, spec_dict: dict):

        self.mirror_x = None
        self.mirror_y = None

        if "x" in spec_dict:
            self.mirror_x = EDs.EvaluableScalar(spec_dict["x"])

        if "y" in spec_dict:
            self.mirror_y = EDs.EvaluableScalar(spec_dict["y"])

    def get_transformations(
        self, expr_evaluator: Callable
    ) -> Generator[Transformation | None, None, None]:

        # First, resolve the spacing and count expressions
        mirror_x = (
            self.mirror_x.evaluate(expr_evaluator)
            if self.mirror_x is not None
            else None
        )
        mirror_y = (
            self.mirror_y.evaluate(expr_evaluator)
            if self.mirror_y is not None
            else None
        )

        # The original point doesn't need a transform at all
        # But we need to yield something so the original object is included
        yield None

        if self.mirror_x is not None:
            yield Mirror(mirror_x=mirror_x, mirror_y=None)

        if self.mirror_y is not None:
            yield Mirror(mirror_x=None, mirror_y=mirror_y)

        if self.mirror_x is not None and self.mirror_y is not None:
            yield Mirror(mirror_x=mirror_x, mirror_y=mirror_y)
