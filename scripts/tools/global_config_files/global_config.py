import yaml
from enum import Enum, auto

from pathlib import Path

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

        # Map the string keys into the typed enum
        self._cy_offs = {
            self.CourtyardType.DEFAULT: float(data["courtyard_offset"]['default']),
            self.CourtyardType.CONNECTOR: float(data["courtyard_offset"]['connector']),
            self.CourtyardType.BGA: float(data["courtyard_offset"]['bga']),
        }

    def get_courtyard_offset(self, courtyard_type: CourtyardType) -> float:
        return self._cy_offs[courtyard_type]

    def get_fab_bevel_size(self, overall_size: float) -> float:
        """
        Get the bevel size for the fab layer, based on the overall size
        of the part.
        """
        return min(self.fab_bevel_size_absolute, overall_size * self.fab_bevel_size_relative)

    @classmethod
    def load_from_file(self, path: Path):
        """
        Simple helper to open a global config from some data file
        """
        with open(path, 'r') as config_stream:
            data = yaml.safe_load(config_stream)
            return GlobalConfig(data)