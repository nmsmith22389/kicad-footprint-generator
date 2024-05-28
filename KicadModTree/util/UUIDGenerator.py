#!/usr/bin/env python3
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
# (C) 2024-at least infinity by Uli Köhler <kicad@techoverflow.nte>
import hashlib
import uuid
from typing import List

from KicadModTree.util.kicad_util import SexprSerializer

class DeterministicUUIDGenerator(object):
    """
    A UUID generator which does not generate random UUIDs,
    but instead takes a per-UUID seed and deterministically
    produces a "random-looking" (yeah yeah) UUID from said seed.
    """
    
    @staticmethod
    def generate(seed: str) -> str:
        """
        Generate a UUID from the given seed
        """
        # Hash seed so the generated UUID has more entropy
        digest = hashlib.sha3_256(seed.encode('utf-8')).digest()
        # Generate UUID4 from digest
        uuid = uuid.UUID(bytes=digest[:16], version=4)
        return str(uuid)
        
    @staticmethod
    def uuid_sexpr_node(seed: str) -> List:
        """
        Get a Sexpr UUID node which can be added to a KicadModTree
        """
        return [
            SexprSerializer.Symbol('uuid'), 123
        ])
        
