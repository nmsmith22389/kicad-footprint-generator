# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016-2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

import io
import os
import abc


class FileHandler(abc.ABC):
    r"""some basic methods to write KiCad library files, the base class
    of footprint (and perhaps later, symbol) direct-file writer implementations
    """

    def writeFile(self, filename):
        r"""Write the output of FileHandler.serialize to a file

        :param filename:
            path of the output file
        :type filename: ``str``
        """

        fp = None
        with io.open(filename, "w", encoding="utf-8") as f:
            output = self.serialize()

            if not output.endswith("\n"):
                output += "\n"

            f.write(output)

            fp = os.path.realpath(f.name)

            f.close()
        return fp

    @abc.abstractmethod
    def serialize(self):
        r"""Get a valid string representation of the footprint in the specified format

        :Example:

        >>> from KicadModTree import *
        >>> kicad_mod = Footprint("example_footprint", FootprintType.THT)
        >>> file_handler = KicadFileHandler(kicad_mod)  # KicadFileHandler is a implementation of FileHandler
        >>> print(file_handler.serialize())
        """

        raise NotImplementedError(
            "serialize has to be implemented by child class")
