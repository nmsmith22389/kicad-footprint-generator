import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# If this is in the 3D generator - DO NOT MODIFY!
# This is a copy of the file from the footprint
# generator - the two should stay in sync until we can figure out
# how to share code!

# Don't use any KicadModTree utils - this file will be copied to the
# 3D generator, and that doesn't have access to it.


class TwoPadDimensions:
    """

    Defines two pads spaced like this (doesn't have to be in the x-direction,
    or even parallel to any axis))

                spacing outside
    |<------------------------------------->|
    |                                       |
    |           spacing centre              |
    |     |<------------------------->|     |
    |     |                           |
    +-----------+               +-----------+ ---
    |     |     |               |     |     |  ^
    |     +     |               |     +     |  | size_crosswise
    |           |               |           |  v
    +-----------+               +-----------+ ---
    |           |               |
    |           |<------------->|
    |<--------->| spacing inside
     size_inline
    """

    size_crosswise: float
    size_inline: float
    spacing_inside: float

    def __init__(
        self,
        size_crosswise: float,
        size_inline: Optional[float] = None,
        spacing_centre: Optional[float] = None,
        spacing_inside: Optional[float] = None,
        spacing_outside: Optional[float] = None,
    ):
        """
                Handle the various methods of providing sufficient dimensions to
                derive a size, and the inside edge to edge distance
                that this script works with internally.

                Exactly two of the size_inline and spacing parameters are needed.
        _
                @param size_crosswise: the size perpendicular to the spacing dimensions
                @param size_inline: the size parallel to the spacing dimensions
                @param spacing_centre: the spacing between pad centres
        """

        if size_inline and spacing_inside:
            # Already have what we need
            pass
        elif size_inline and spacing_outside:
            spacing_inside = spacing_outside - (size_inline * 2)
        elif size_inline and spacing_centre:
            spacing_inside = spacing_centre - size_inline
        elif spacing_inside and spacing_outside:
            size_inline = (spacing_outside - spacing_inside) / 2

        if size_inline is None or spacing_inside is None:
            raise ValueError(
                "Could not derive the two-pad size from the given parameters"
            )

        self.size_inline = size_inline
        self.spacing_inside = spacing_inside
        self.size_crosswise = size_crosswise

    @property
    def spacing_outside(self) -> float:
        return self.spacing_inside + (self.size_inline * 2)

    @property
    def spacing_centre(self) -> float:
        return self.spacing_inside + self.size_inline


class SmdInductorProperties:
    """
    Object that represents the definition of a single inductor part.

    This may not be a complete definition, as some parts may be defined
    partly in the series definition, and partly in the part definition.
    """

    # All parts have these members
    # some (landing and pads) may be derived from input data
    width_x: float
    length_y: float
    height: float
    corner_radius: Optional[float]
    core_diameter: Optional[float]
    # Dimensions of PCB lands
    landing_dims: TwoPadDimensions
    # Dimension of pads on the device
    device_pad_dims: TwoPadDimensions
    # All parts have a part number
    part_number: str
    # Some parts use the series datasheet
    datasheet: Optional[str]

    def __init__(self, part_block: dict[str, str]):

        self.width_x = float(part_block["widthX"])
        self.length_y = float(part_block["lengthY"])
        self.height = float(part_block["height"])
        self.corner_radius = float(part_block["cornerRadius"]) if part_block.get("cornerRadius") else None
        self.core_diameter = float(part_block["coreDiameter"]) if part_block.get("coreDiameter") else None

        self.landing_dims = self._derive_landing_size(part_block)
        self.device_pad_dims = self._derive_pad_spacing(part_block)

        self.part_number = part_block["PartNumber"]
        self.datasheet = part_block.get("datasheet", None)

    @staticmethod
    def _get_key_as_float_or_none(d, key: str) -> float:
        try:
            return float(d[key])
        except KeyError:
            return None

    def _derive_landing_size(self, data: Dict[str, Any]) -> TwoPadDimensions:
        """
        Handle the various methods of providing sufficient dimensions to
        derive the land X dimension.

        :param data: some dictionary of data
        :return: a TwoPadDimension object
        """

        landing_y = float(data["landingY"])

        xin = self._get_key_as_float_or_none(data, "landingX")
        spc_c = self._get_key_as_float_or_none(data, "landingSpacingX")
        spc_ix = self._get_key_as_float_or_none(data, "landingInsideX")
        spc_ox = self._get_key_as_float_or_none(data, "landingOutsideX")

        try:
            return TwoPadDimensions(landing_y, xin, spc_c, spc_ix, spc_ox)
        except ValueError:
            raise RuntimeError(
                "Unhandled combination of landing dimensions, "
                "saw: " + ", ".join(data.keys())
            )

    def _derive_pad_spacing(self, data: Dict[str, str]) -> TwoPadDimensions:
        """
        Handle the various methods of providing sufficient dimensions to
        derive the pad dimensions (this is the pad on the device, not on
        the PCB - that is the landing)

        If the parameters are not given, pads will be constructed from the
        landing sizes (is this an error?)

        :param data: some dictionary of data
        :return: a TwoPadDimension object
        """

        pad_y = self._get_key_as_float_or_none(data, "padY")

        if pad_y is None:
            logging.info(
                "No physical pad dimensions (padY) found - using body and PCB landing dimensions "
                "(lengthY, landingY) as a substitute."
            )
            pad_y = min(self.landing_dims.size_crosswise, self.length_y)

        spc_c = self._get_key_as_float_or_none(data, "padSpacing")
        spc_ix = self._get_key_as_float_or_none(data, "padInsideX")
        spc_ox = self._get_key_as_float_or_none(data, "padOutsideX")
        pad_x = self._get_key_as_float_or_none(data, "padX")

        try:
            pad_dims = TwoPadDimensions(pad_y, pad_x, spc_c, spc_ix, spc_ox)
        except ValueError:
            # We don't have enough info here to construct the pad dimensions
            # So construct a pad width to be getting on with

            logging.info(
                "No physical pad dimensions (padX) found - using landing dimensions "
                "as a substitute."
            )
            # limit the outside dim to the overall package size
            pad_ox = min(self.landing_dims.spacing_outside, self.width_x)
            pad_dims = TwoPadDimensions(
                pad_y,
                spacing_inside=self.landing_dims.spacing_inside,
                spacing_outside=pad_ox,
            )

        return pad_dims


class InductorSeriesProperties:
    """
    Object that represents the definition of a series of inductors,
    read from a dict probably from a YAML file.
    """

    name: str
    manufacturer: str
    datasheet: Optional[str]
    tags: List[str]

    library_name: str

    # List of the part definitions in the series
    parts: List[SmdInductorProperties]

    def __init__(self, series_block: dict, csv_dir: Optional[Path]):
        self.name = series_block["series"]

        logging.info(f"Processing properties for series: {self.name}")

        self.manufacturer = series_block["manufacturer"]
        # allow empty datasheet in case of unique per-part datasheets
        self.datasheet = series_block.get("datasheet", "")
        # space delimited list of the tags
        self.tags = series_block.get("tags", [])

        self.library_name = series_block["library_name"]

        if "csv" in series_block:
            csv_file = series_block["csv"]

            if csv_dir is not None:
                csv_file = csv_dir / csv_file

            with open(csv_file, encoding="utf-8-sig") as f:
                self.parts = [SmdInductorProperties(x) for x in csv.DictReader(f)]

        elif "parts" in series_block:
            # Load directly from the YAML (for a single-size series, for example)
            self.parts = [SmdInductorProperties(x) for x in series_block["parts"]]
        else:
            raise RuntimeError("Data block must contain a 'csv' or 'parts' key")
