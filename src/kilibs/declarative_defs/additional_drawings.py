from abc import ABC, abstractmethod
from itertools import product
from typing import Callable, Generator

from kilibs.declarative_defs import repeat_defs
from kilibs.geom import Vector2D
from kilibs.util import dict_tools


class DrawingProvider:

    @staticmethod
    def _modify_point(
        pt: Vector2D, transforms: list[repeat_defs.Transformation]
    ) -> Vector2D:
        """
        Apply the repeat transforms (grid. mirror, etc) to a point in order.

        Points are easy, because they can't be rotated, and a flip is just a
        matter of negating the x or y coordinate.

        But it won't work for things like rectangles when they are rotated by a
        non-90 degree angle.

        It also won't cover things like rotating polygons while keeping them
        upright, but that requires quite some thought, as the result you
        get depends on what you call the "origin" of the polygon. And probably
        isn't really useful.
        """
        for transformer in transforms:
            transformation = transformer.apply(pt)

            if transformation.offset is not None:
                pt = pt + transformation.offset

            # Rotations don't do anything to points
            # Flip doesn't do anything to points
        return pt

    class Context:
        pass


class AdditionalDrawing(ABC):
    """
    Additional drawings are free-form drawings that can be added to the
    footprint in addition to the main shape. They can be used to add
    unique features to the footprint that are not covered by a main
    generator.

    For example, adding circle to denote a pressure port or similar:

    additional_drawing:
        inner_circle:
            type: circle
            center: [0, 0]
            radius: 1
            layer: Cmts.User
            width: 0.1
        outer_circle:
            inherit: key1
            radius: 2

    Inheritance is possible between additional drawings.

    Complex shapes can be implemented as their own drawing types, or,
    perhaps, as a full-blown declarative definition class.

    This class could is agnostic to whether it's in a footprint
    or symbol or something else.

    See more detail at https://gitlab.com/groups/kicad/libraries/-/wikis/Footprint-Generators/Common-YAML-data
    """

    STANDARD_KEY = "additional_drawings"

    type: str
    """
    The type key. Mostly useful for debugging/logging
    """

    shape_provider: DrawingProvider

    """
    The constructed shape object for the drawing. Note that this
    may contain un-evaluated expressions.
    """
    _repeat: repeat_defs.RepeatDef | None
    _mirror: repeat_defs.MirrorRepeatDef | None

    def __init__(self, spec_dict: dict, key_name: str):
        """
        Initialize the additional drawing object from a single specification.
        """
        # Mostly for debugging/logging purposes
        self.key_name = key_name

        if "type" not in spec_dict:
            raise ValueError(
                f"Additional drawing {self.key_name} must have a 'type' key"
            )

        providers = self._get_default_providers()

        self.type = spec_dict["type"]

        if self.type in providers:
            shape_provider = providers[self.type]
            self.shape_provider = shape_provider(spec_dict)
        else:
            # Failed to get a shape object
            raise NotImplementedError(
                f"Cannot create shape object for additional drawing '{self.type}'"
            )

        if "repeat" not in spec_dict:
            self._repeat = None
        else:
            repeat_type = spec_dict["repeat"]["type"]
            if repeat_type == "grid":
                self._repeat = repeat_defs.GridRepeatDef(spec_dict["repeat"])
            elif repeat_type == "circular":
                self._repeat = repeat_defs.CircularRepeatDef(spec_dict["repeat"])
            else:
                raise ValueError(f"Unknown repeat type: {repeat_type}")

        # Mirror is a separate property, because it can compose with the repeat
        if "mirror" not in spec_dict:
            self._mirror = None
        else:
            self._mirror = repeat_defs.MirrorRepeatDef(spec_dict["mirror"])

    @abstractmethod
    def _get_default_providers(self) -> dict[str, DrawingProvider]:
        """
        Implement this to provide providers that make sense in your application.
        """
        pass

    @classmethod
    def from_standard_yaml(
        cls, parent_spec: dict, key: str = STANDARD_KEY
    ) -> list["AdditionalDrawing"]:
        """
        Create a list of additional drawings from the standard YAML format.
        This also handles any inheritance of the additional drawings amongst
        the keys.
        """

        add_dwgs = []
        specs = parent_spec.get(key, None)
        if specs is not None:

            # process inheritance of the drawing definitions
            dict_tools.dictInherit(specs)

            for key_name, rule_area_spec in specs.items():
                add_dwg = cls(rule_area_spec, key_name)
                add_dwgs.append(add_dwg)

        return add_dwgs

    def get_transforms(
        self, expr_evaluator: Callable
    ) -> Generator[list[repeat_defs.Transformation], None, None]:
        """
        Yield the repeat instances for the additional drawing.
        """

        # If there is no repeat, we still need to yield something, so we
        # yield an empty list.
        null_iter = iter([[]])

        mirrors = (
            self._mirror.get_transformations(expr_evaluator)
            if self._mirror
            else null_iter
        )
        repeats = (
            self._repeat.get_transformations(expr_evaluator)
            if self._repeat
            else null_iter
        )

        any_transform = False

        for m, g in product(mirrors, repeats):
            # Provide the list of whatever tranforms are produced,
            # weeding out when no transform is produced.
            any_transform = True
            yield [transform for transform in (m, g) if transform]

        if not any_transform:
            # If we didn't yield any transforms, yield a null transform
            # to ensure the original object is included.
            yield []
