import yaml
from enum import Enum, auto
from importlib import resources

from pathlib import Path

from KicadModTree.util.corner_handling import RoundRadiusHandler, ChamferSizeHandler

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

    courtyard_line_width: float
    courtyard_grid: float

    silk_line_width: float
    silk_pad_clearance: float
    silk_fab_offset: float
    silk_line_length_min: float

    fab_line_width: float
    fab_bevel_size_absolute: float
    fab_bevel_size_relative: float

    edge_cuts_line_width: float

    # Includes trailing '/'
    model_3d_prefix: str

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

        self.edge_cuts_line_width = float(data["edge_cuts_line_width"])

        self.model_3d_prefix = data["3d_model_prefix"]

        self.round_rect_default_radius = data["round_rect_radius_ratio"]
        self.round_rect_max_radius = data["round_rect_max_radius"]

        # Map the string keys into the typed enum
        self._cy_offs = {
            self.CourtyardType.DEFAULT: float(data["courtyard_offset"]['default']),
            self.CourtyardType.CONNECTOR: float(data["courtyard_offset"]['connector']),
            self.CourtyardType.BGA: float(data["courtyard_offset"]['bga']),
        }

    def get_courtyard_offset(self, courtyard_type: CourtyardType) -> float:
        return self._cy_offs[courtyard_type]

    @property
    def roundrect_radius_handler(self) -> RoundRadiusHandler:
        """
        Get the default pad radius handler for roundrects
        """
        return RoundRadiusHandler(
            default_redius_ratio=self.round_rect_default_radius,
            maximum_radius=self.round_rect_max_radius,
        )

    def get_fab_bevel_size(self, overall_size: float) -> float:
        """
        Get the bevel size for the fab layer, based on the overall size
        of the part.
        """
        return min(self.fab_bevel_size_absolute, overall_size * self.fab_bevel_size_relative)

    @property
    def get_fab_bevel(self) -> ChamferSizeHandler:
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

    with resources.path(
        "scripts.tools.global_config_files", default_global_config_name
    ) as default_global_config:
        global_config = GlobalConfig.load_from_file(default_global_config)

    return global_config
