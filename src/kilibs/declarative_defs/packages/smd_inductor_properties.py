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
"""Classes for SMD inductor properties."""

import csv
import logging
from pathlib import Path
from typing import Any

from kilibs.declarative_defs.packages.two_pad_dimensions import TwoPadDimensions


class SmdInductorProperties:
    """Object that represents the definition of a single inductor part.

    This may not be a complete definition, as some parts may be defined
    partly in the series definition, and partly in the part definition.
    """

    width_x: float
    """Width of the inductor in mm."""
    length_y: float
    """Length of the inductor in mm."""
    height: float
    """Height of the inductor in mm."""
    corner_radius: float | None
    """Optional corner radius of the inductor in mm."""
    core_diameter: float | None
    """Optional diameter of the core in mm."""
    landing_dims: TwoPadDimensions
    """Dimensions of PCB landing pads in mm."""
    device_pad_dims: TwoPadDimensions
    """Dimensions of pads on the inductorin mm."""
    part_number: str
    """Part number of the inductor."""
    datasheet: str | None
    """Datasheet of the inductor or `None` if the series datasheet is used."""

    def __init__(self, part_block: dict[str, str]) -> None:
        """Create an instance of `SmdInductorProperties`.

        Args:
            part_block: The dictionary containing the properties of the inductor.
        """
        self.width_x = float(part_block["widthX"])
        self.length_y = float(part_block["lengthY"])
        self.height = float(part_block["height"])
        self.corner_radius = (
            float(part_block["cornerRadius"])
            if part_block.get("cornerRadius")
            else None
        )
        self.core_diameter = (
            float(part_block["coreDiameter"])
            if part_block.get("coreDiameter")
            else None
        )
        self.landing_dims = self._derive_landing_size(part_block)
        self.device_pad_dims = self._derive_pad_spacing(part_block)
        self.part_number = part_block["PartNumber"]
        self.datasheet = part_block.get("datasheet", None)

    @staticmethod
    def _get_key_as_float_or_none(d: dict[str, Any], key: str) -> float | None:
        """Return the key as a `float` or, if the key is not present in the dictionary,
        then `None` is returned.

        Args:
            d: The dictionary.
            key: The key.
        """
        try:
            return float(d[key])
        except KeyError:
            return None

    def _derive_landing_size(self, data: dict[str, Any]) -> TwoPadDimensions:
        """Handle the various methods of providing sufficient dimensions to derive the
        land X dimension.

        Args:
            data: The dictionary containing the PCB landing pad dimensions.

        Returns:
            An instance of `TwoPadDimensions` containing the pad dimensions extracted
            from the given `dict`.
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

    def _derive_pad_spacing(self, data: dict[str, str]) -> TwoPadDimensions:
        """Handle the various methods of providing sufficient dimensions to derive the
        pad dimensions (this is the pad on the device, not on the PCB - that is the
        landing).

        If the parameters are not given, pads will be constructed from the landing sizes
        (is this an error?).

        Args:
            data: The dictionary from which to extract the pad dimensions of the
                inductor.

        Returns:
            An instance of `TwoPadDimensions` containing the pad dimensions extracted
            from the given `dict`.
        """
        pad_y = self._get_key_as_float_or_none(data, "padY")
        if pad_y is None:
            logging.info(
                "No physical pad dimensions (padY) found - using body and PCB landing "
                "dimensions (lengthY, landingY) as a substitute."
            )
            pad_y = min(self.landing_dims.size_crosswise, self.length_y)

        spc_c = self._get_key_as_float_or_none(data, "padSpacingX")
        spc_ix = self._get_key_as_float_or_none(data, "padInsideX")
        spc_ox = self._get_key_as_float_or_none(data, "padOutsideX")
        pad_x = self._get_key_as_float_or_none(data, "padX")
        try:
            pad_dims = TwoPadDimensions(pad_y, pad_x, spc_c, spc_ix, spc_ox)
        except ValueError:
            # We don't have enough info here to construct the pad dimensions
            # So construct a pad width to be getting on with.
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
    """Object that represents the definition of a series of inductors, read from a dict,
    probably from a YAML file.
    """

    name: str
    """The name of the series."""
    manufacturer: str
    """The manufacturer of the inductors."""
    datasheet: str | None
    """The series datasheet or `None` if each inductor of the series has its own
    datasheet."""
    tags: list[str]
    """The tags."""
    has_orientation: bool
    """`True` if the inductors have an orientation and require a pin 1 marker."""
    library_name: str
    """The name of the library to store the output in."""
    parts: list[SmdInductorProperties]
    """List of the part definitions in the series."""

    def __init__(self, series_block: dict[str, Any], csv_dir: Path | None) -> None:
        """Create an instance of `InductorSeriesProperties` by loading the data from
        the given dictionary (and optionally additional CSV files).

        Args:
            series_block: The dictionary from which to extract the data of the series.
            csv_dir: Optionally, the path of the directory containing the CSV files that
                might be referenced by the dictionary.
        """
        self.name = series_block["series"]
        logging.info(f"Processing properties for series: {self.name}")
        self.manufacturer = series_block["manufacturer"]
        # allow empty datasheet in case of unique per-part datasheets
        self.datasheet = series_block.get("datasheet", "")
        # space delimited list of the tags
        self.tags = series_block.get("tags", [])
        self.has_orientation = series_block.get("has_orientation", False)
        self.library_name = series_block["library_name"]

        def csv_line_filter(line: str) -> bool:
            """Filter function to remove lines that are comments or empty."""
            if line.startswith("#"):
                return False
            if not line.strip():
                return False
            return True

        if "csv" in series_block:
            csv_file = series_block["csv"]
            if csv_dir is not None:
                csv_file = csv_dir / csv_file
            with open(csv_file, encoding="utf-8-sig") as f:
                # Filter out rows that start with "#"
                filtered_rows = filter(csv_line_filter, f)
                # Read the CSV file and create SmdInductorProperties instances from each row
                self.parts = [
                    SmdInductorProperties(x) for x in csv.DictReader(filtered_rows)
                ]
        elif "parts" in series_block:
            # Load directly from the YAML (for a single-size series, for example)
            self.parts = [SmdInductorProperties(x) for x in series_block["parts"]]
        else:
            raise RuntimeError("Data block must contain a 'csv' or 'parts' key")
