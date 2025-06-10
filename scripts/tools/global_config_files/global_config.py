import yaml
from enum import Enum, auto
from importlib import resources

from pathlib import Path

from kilibs.geom import Vector2D
from KicadModTree.util.corner_handling import RoundRadiusHandler, ChamferSizeHandler


class IpcRotation(Enum):
    A = "A"
    B = "B"

class PadName(Enum):
    MECHANICAL = "mechanical"
    SHIELD = "shield"


class FieldPosition(Enum):
    INSIDE = "inside"
    OUTSIDE_TOP = "outside_top"
    OUTSIDE_BOTTOM = "outside_bottom"

class LayerTextProperties:
    """
    This describes the properties of text on a given layer.

    Generally it will be the allowed size range, and the thickness ratio
    for the font.
    """

    def __init__(
        self,
        size_nom: float,
        size_max: float,
        size_min: float,
        thickness_ratio: float, # usually 0.15
        width_ratio: float,  # usually 1.0 for "square" text
    ):
        self.size_nom = size_nom
        self.size_max = size_max
        self.size_min = size_min
        self.thickness_ratio = thickness_ratio
        self.width_ratio = width_ratio

    def clamp_size(self, height: float) -> tuple[Vector2D, float]:
        size = min(self.size_max, max(self.size_min, height))

        size = round(size, 2)
        thickness = round(self.thickness_ratio * size, 2)

        return Vector2D(self.width_ratio * size, size), thickness

class FieldProperties:

    def __init__(
        self,
        layer: str,
        position_y: FieldPosition | str,
        autosize: bool,
    ):
        self.layer = layer
        self.position_y = FieldPosition(position_y)
        self.autosize = autosize


class GlobalConfig:
    """
    Class that provides global footprint generation parameters.

    For example, the preferred line widths, etc.

    This decouples the generators from the format or layout
    of the config and allows both type safety and more flexible
    handling of things like fallbacks or deprecations.
    """

    class CourtyardType(Enum):
        DEFAULT = auto()
        BGA = auto()
        CONNECTOR = auto()
        CRYSTAL = auto()

    courtyard_line_width: float
    courtyard_grid: float

    silk_line_width: float
    silk_pad_clearance: float
    silk_fab_offset: float
    silk_line_length_min: float

    fab_line_width: float
    fab_bevel_size_absolute: float
    fab_bevel_size_relative: float
    fab_pin1_marker_length: float
    """The length of a fab-layer pin1 chevron marker (in mm)"""

    edge_cuts_line_width: float

    # The default line width for anything without a specific
    # default (e.g. silk, fab, etc)
    default_line_width: float

    # Includes trailing '/'
    model_3d_prefix: str

    # Includes leading '.'
    model_3d_suffix: str

    _layer_functions: dict

    _pad_names: dict

    _layer_text_properties: dict

    reference_fields: list[FieldProperties]
    value_fields: list[FieldProperties]

    handsoldering_suffix: str

    def __init__(self, data: dict):
        """
        Initialise from some dictonary of data (likely a
        config_KLC YAML or similar)
        """

        self.courtyard_line_width = float(data["courtyard_line_width"])
        self.courtyard_grid = float(data["courtyard_grid"])

        self.silk_line_width = float(data["silk_line_width"])
        self.silk_pad_clearance = float(data["silk_pad_clearance"])
        self.silk_fab_offset = float(data["silk_fab_offset"])
        self.silk_line_length_min = float(data["silk_line_length_min"])

        self.fab_line_width = float(data["fab_line_width"])
        self.fab_bevel_size_absolute = float(data["fab_bevel_size_absolute"])
        self.fab_bevel_size_relative = float(data["fab_bevel_size_relative"])
        self.fab_pin1_marker_length = float(data["fab_pin1_marker_length"])

        self.edge_cuts_line_width = float(data["edge_cuts_line_width"])

        self.default_line_width = float(data["default_line_width"])

        self.model_3d_prefix = data["3d_model_prefix"]
        self.model_3d_suffix = data["3d_model_suffix"]

        self.round_rect_default_radius = data["round_rect_radius_ratio"]
        self.round_rect_max_radius = data["round_rect_max_radius"]

        self._ep_round_rect_default_radius = data["ep_round_rect_radius_ratio"]
        self._ep_round_rect_max_radius = data["ep_round_rect_max_radius"]

        self._paste_round_rect_default_radius = data["paste_round_rect_radius_ratio"]
        self._paste_round_rect_max_radius = data["paste_round_rect_max_radius"]

        # Map the string keys into the typed enum
        self._cy_offs = {
            self.CourtyardType.DEFAULT: float(data["courtyard_offset"]['default']),
            self.CourtyardType.CONNECTOR: float(data["courtyard_offset"]['connector']),
            self.CourtyardType.BGA: float(data["courtyard_offset"]['bga']),
            self.CourtyardType.CRYSTAL: float(data["courtyard_offset"]['crystal']),
        }

        self._layer_functions = data["layer_functions"]

        self._pad_names = data["pad_names"]

        self._layer_text_properties = {
            layer: LayerTextProperties(**props)
            for layer, props in data["text_properties"].items()
        }

        self.reference_fields = [FieldProperties(**field) for field in data["references"]]  # fmt: skip
        self.value_fields = [FieldProperties(**field) for field in data["values"]]

        self._rotation_suffix_pattern = data["rotation_suffix_pattern"]

        self.handsoldering_suffix = data["handsoldering_suffix"]

    def get_courtyard_offset(self, courtyard_type: CourtyardType) -> float:
        return self._cy_offs[courtyard_type]

    @property
    def roundrect_radius_handler(self) -> RoundRadiusHandler:
        """
        Get the default pad radius handler for roundrects
        """
        return RoundRadiusHandler(
            radius_ratio=self.round_rect_default_radius,
            maximum_radius=self.round_rect_max_radius,
        )

    @property
    def ep_roundrect_radius_handler(self) -> RoundRadiusHandler:
        """
        Get the default pad radius handler for roundrect exposed/thermal pads
        """
        return RoundRadiusHandler(
            radius_ratio=self._ep_round_rect_default_radius,
            maximum_radius=self._ep_round_rect_max_radius
        )

    @property
    def paste_roundrect_radius_handler(self) -> RoundRadiusHandler:
        """
        Get the default pad radius handler for roundrect paste pads
        """
        return RoundRadiusHandler(
            radius_ratio=self._paste_round_rect_default_radius,
            maximum_radius=self._paste_round_rect_max_radius
        )

    def get_fab_bevel_size(self, overall_size: float) -> float:
        """
        Get the bevel size for the fab layer, based on the overall size
        of the part.
        """
        return min(self.fab_bevel_size_absolute, overall_size * self.fab_bevel_size_relative)

    @property
    def fab_bevel(self) -> ChamferSizeHandler:
        """
        Get the default fab bevel size handler
        """
        return ChamferSizeHandler(
            maximum_chamfer=self.fab_bevel_size_absolute,
            default_chamfer_ratio=self.fab_bevel_size_relative,
        )

    @property
    def silk_pad_offset(self):
        """
        Get the center offset for silk line centerline from the pad edge.

        This assumes the default silk line width and pad clearance

        --------------
        Silk line     ) ---
        --------------   ^
                         | silk-pad offset
                         v
        --------+ --------
        Pad     |
                |
        """

        return self.silk_pad_clearance + self.silk_line_width / 2

    @property
    def silk_fab_clearance(self):
        """
        Get the clearance between the silk and fab layers.

        This is the distance from the silk line centerline to the fab line centerline.
        """

        return self.silk_fab_offset - (self.silk_line_width + self.fab_line_width) / 2

    def get_layer_for_function(self, layer_or_function: str) -> float:
        """
        Get the layer function for the given function name.

        :param function_or_layer: The function name or layer name to get the function for.
            If it is not in the layer functions, it is assumed to be a layer name and
            returned directly.
        """
        if layer_or_function in self._layer_functions:
            return self._layer_functions[layer_or_function]

        return layer_or_function

    def get_default_width_for_layer(self, layer: str) -> float:
        """
        Get the default line width for a given layer.
        """
        if layer in ["F.SilkS", "B.SilkS"]:
            return self.silk_line_width
        elif layer in ["F.Fab", "B.Fab"]:
            return self.fab_line_width
        elif layer in ["Edge.Cuts"]:
            return self.edge_cuts_line_width
        elif layer in ["F.CrtYd", "B.CrtYd"]:
            return self.courtyard_line_width

        return self.default_line_width

    def get_pad_name(self, name: PadName) -> str:
        """
        Get a predefined pad name from the global config. E.g. MP or SH.
        """
        return self._pad_names[name.value]

    def get_text_properties_for_layer(self, layer: str) -> LayerTextProperties:
        """
        Get the text properties for a given layer.
        """
        if layer in ["F.Fab", "B.Fab"]:
            layer_key = "fab"
        elif layer in ["F.SilkS", "B.SilkS"]:
            layer_key = "silk"
        else:
            raise ValueError(f"Unknown layer {layer} for layer properties (did you mean a Fab or Silk layer?)")

        return self._layer_text_properties[layer_key]

    def get_generated_by_description(self, generator_name: str | None = None) -> str:
        """
        Get the "Generated by" description for a given generator name.
        """
        s = "generated with kicad-footprint-generator"

        if generator_name is not None:
            s += f" {generator_name}"
        return s

    def get_rotation_suffix(self, rotation_level=IpcRotation):
        """
        Get the name suffix for the given IPC rotation leve
        """
        return self._rotation_suffix_pattern.format(
            rotation=rotation_level.value
        )

    @classmethod
    def load_from_file(self, path: Path):
        """
        Simple helper to open a global config from some data file
        """
        with open(path, 'r') as config_stream:
            data = yaml.safe_load(config_stream)
            return GlobalConfig(data)


def DefaultGlobalConfig() -> GlobalConfig:
    """
    Get a default global config object (the current KLC version)

    This should be used only for when a generator is not yet ported to
    FootprintGenerator or similar where the global config can be injected
    properly.

    But it's better than using the global variables in footprint_global_properties,
    or hardcoding values. It also makes it very easy to port later, as you just
    inject a GlobalConfig object into the generator, rather than calling this
    function.
    """

    default_global_config_name = "config_KLCv3.0.yaml"

    resource = resources.files("scripts.tools.global_config_files").joinpath(
        default_global_config_name
    )
    with resources.as_file(resource) as default_global_config:
        return GlobalConfig.load_from_file(default_global_config)
