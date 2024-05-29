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
# (C) 2024 by C. Kuhlmann, gitlab @CKuhlmann

from __future__ import annotations

from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.Node import TStamp


class Group(Node):
    def __init__(self, name: str = "", uuid: TStamp | None = None,
                 member_tstamps: list[TStamp] | list[str] | None = None,
                 member_nodes: list[Node] | None = None, ) -> None:
        super().__init__()

        self._name: str = name
        self._member_nodes: list[Node] | None = member_nodes
        # self._member_tstamps:set[TStamp]|set[str]|None  = member_tstamps

        self._gathered_member_tstamp_str_set = set()

        if member_tstamps is not None:
            for m in member_tstamps:
                self._gathered_member_tstamp_str_set.add(str(m))
        if member_nodes is not None:
            for mn in member_nodes:
                ts = mn.getTStamp()
                self._gathered_member_tstamp_str_set.add(str(ts))
        pass

    def getGroupName(self):
        return str(self._name)

    def getSortedGroupMemberTStamps(self):
        return sorted(self._gathered_member_tstamp_str_set)

    def getGroupMemberTStamps(self):
        return self._gathered_member_tstamp_str_set

    def getGroupMemberNodes(self):
        return self._member_nodes

    def append(self, new_member_node_or_tsamp):
        if hasattr(new_member_node_or_tsamp, 'getTStamp'):
            ts = str(new_member_node_or_tsamp.getTStamp())
        else:
            ts = str(new_member_node_or_tsamp)
        if ts not in self._gathered_member_tstamp_str_set:
            self._gathered_member_tstamp_str_set.add(ts)
            self._member_nodes.append(new_member_node_or_tsamp)

    def remove(self, old_member_node_or_tsamp):
        if hasattr(old_member_node_or_tsamp, 'getTStamp'):
            ts = str(old_member_node_or_tsamp.getTStamp())
        else:
            ts = str(old_member_node_or_tsamp)
        rem = []
        if ts in self._gathered_member_tstamp_str_set:
            self._gathered_member_tstamp_str_set.remove(ts)
            for idx, nd in enumerate(self._member_nodes):
                if str(nd.getTStamp()) == ts:
                    rem += nd
            for r in rem:
                self._member_nodes.remove(r)
