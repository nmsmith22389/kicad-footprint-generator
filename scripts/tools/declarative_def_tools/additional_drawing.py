from typing import Callable

from KicadModTree import Node, Rect, Circle
from kilibs.util import dict_tools

from . import shape_properties as SP
from scripts.tools.global_config_files.global_config import GlobalConfig

class AdditionalDrawing:
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

    This class could eventually be agnostic to whether it's in a footprint
    or symbol or something else.
    """

    STANDARD_KEY = "additional_drawings"

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

        self.type = spec_dict["type"]

        # Delegate the geometry to the appropriate shape class
        self.shape = SP.construct_shape(spec_dict)

        self.layer = spec_dict["layer"]
        self.width = spec_dict.get("width", None)

        self.fill = spec_dict.get("fill", False)

    @staticmethod
    def from_standard_yaml(
        parent_spec: dict, key: str = STANDARD_KEY
    ) -> list["AdditionalDrawing"]:
        """
        Create a list of additional drawings from the standard YAML format.
        This also handles any inheritance of the additional drawings.
        """

        add_dwgs = []
        specs = parent_spec.get(key, None)
        if specs is not None:

            # process inheritance of the rule area definitions
            dict_tools.dictInherit(specs)

            for key_name, rule_area_spec in specs.items():
                add_dwg = AdditionalDrawing(rule_area_spec, key_name)
                add_dwgs.append(add_dwg)

        return add_dwgs


def create_additional_drawings(
    additional_drawings: list[AdditionalDrawing],
    global_config: GlobalConfig,
    expr_evaluator: Callable
) -> list[Node]:
    """
    Create the drawing objects from the given additional drawing properties,
    after evaluating any expressions in the drawing shapes.

    Relevant defaults are also be applied from the global configuration at this
    time.

    This is the "glue" that converts "generic" addtional drawing properties
    into footprint-specific drawing objects. In theory, a similar function
    could be used to create suitable objects for adding to symbols.
    """

    dwg_nodes = []

    for add_dwg in additional_drawings:

        layer = global_config.get_layer_for_function(add_dwg.layer)

        if add_dwg.width is not None:
            width = add_dwg.width
        else:
            width = global_config.get_default_width_for_layer(layer)

        if add_dwg.type == SP.RECT:
            rect = add_dwg.shape.evaluate_expressions(expr_evaluator)
            dwg_nodes.append(
                Rect(
                    start=rect.top_left,
                    end=rect.bottom_right,
                    layer=layer,
                    width=width,
                    fill=add_dwg.fill,
                )
            )

        elif add_dwg.type == SP.CIRCLE:
            circ = add_dwg.shape.evaluate_expressions(expr_evaluator)

            dwg_nodes.append(
                Circle(
                    center = circ.center_pos,
                    radius = circ.radius,
                    layer=layer,
                    width=width,
                    fill=add_dwg.fill,
                )
            )

        else:
            raise NotImplementedError(f"Drawing type {add_dwg.type} not implemented")

    return dwg_nodes
