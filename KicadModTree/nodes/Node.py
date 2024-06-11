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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# modifications 2022 by Armin Schoisswohl (@armin.sch)
from __future__ import annotations
import math
import uuid
from copy import copy, deepcopy
from traceback import print_tb, print_stack
from hashlib import sha1
# from json import dumps
from enum import Enum

from KicadModTree.Vector import *


class MultipleParentsError(RuntimeError):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(MultipleParentsError, self).__init__(message)


class RecursionDetectedError(RuntimeError):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(RecursionDetectedError, self).__init__(message)


class VirtualNodeError(RuntimeError):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(VirtualNodeError, self).__init__(message)


class TStamp(object):
    def parseAsUUID(self, tstamp_uuid: str | uuid.UUID):
        if isinstance(tstamp_uuid, uuid.UUID):
            return tstamp_uuid
        else:
            return uuid.UUID(str(tstamp_uuid))

    def parseTStamp(self, tstamp: TStamp | str):
        if isinstance(tstamp, TStamp):
            return tstamp
        else:
            return TStamp(tstamp=self.parseAsUUID(tstamp))

    def setUniqueID(self, unique_id):
        self._unique_id = str(unique_id)
        self.updateTStampConditionally()

    def unsetTStamp(self):
        self._tstamp: uuid.UUID | str | None = None
        self._tstamp_seed: uuid.UUID | None = None
        self._unique_id: str | None = None
        self._isTStampManualFixed: bool = False

    def setParentNode(self, node):
        self._parentNode = node

    def getParentNode(self) -> Node | None:
        return self._parentNode

    def isTStampValid(self) -> bool:
        return ((self._tstamp is not None) and (self._tstamp != ""))

    def isTStampSeedValid(self) -> bool:
        return ((self._tstamp_seed is not None) and (self._tstamp_seed != ""))

    def getUniqueID(self):
        return self._unique_id

    def getTStamp(self) -> uuid.UUID | str | None:
        return self._tstamp

    def setTStamp(self, tstamp: uuid.UUID | str, tstamp_fixed: bool = True):
        self._tstamp = uuid.UUID(str(tstamp))
        self._isTStampManualFixed = tstamp_fixed

    def returnDerivedTStamp(self, unique_id: str | None = None, obj: object | None = None,
                            seed: uuid.UUID | None = None, use_obj_hash: bool = True, hash_using_dict=True):
        if use_obj_hash:
            if obj is not None and isinstance(obj, object):
                if hasattr(obj, '_hashdict'):
                    d = obj._hashdict()
                else:
                    # consider using hash_str = sha1( str(obj.__hash__()).encode('utf-8') ).hexdigest()
                    d = Node._cleanup_to_hash_dict(obj.__dict__)
                hash_str = sha1(repr(d).encode('utf-8')
                                ).hexdigest() if hash_using_dict else hash(obj)
            else:
                hash_str = 'None'
        else:
            hash_str = "*"
        if seed is None:
            seed = self._tstamp_seed
        if seed is not None:
            return uuid.uuid5(namespace=seed,
                              name=f"KicadModTree.Node.{str(obj.__class__.__name__)}.{str(unique_id)}.{str(hash_str)}")
        else:
            raise RuntimeError(
                f"Timestamp of node {repr(self._parentNode)} was not initialized before requesting it.")
            return None

    def reCalcTStamp(self):
        if not self._isTStampManualFixed:
            self._tstamp = self.returnDerivedTStamp(unique_id=self.getUniqueID(
            ), obj=self._parentNode, seed=self.getTStampSeed(), use_obj_hash=True)
        else:
            print(f"WARNING: TStamp is fixed at {print_stack()}")
        return self.getTStamp()

    def getTStampSeed(self) -> uuid.UUID | None:
        return self._tstamp_seed

    def initializeTStampSeed(self):
        self.setTStampSeed(uuid.uuid5(namespace=uuid.uuid1(
        ), name=f"KicadModTree.Node.{str(__class__.__name__)}.{str(self._unique_id)}"))
        return self.getTStampSeed()

    def updateTStampConditionally(self) -> uuid.UUID:
        if (self._tstamp is None) or (not self._isTStampManualFixed):
            return self.reCalcTStamp()
        else:
            return self.getTStamp()

    def setTStampSeed(self, tstamp_seed: uuid.UUID | str):
        self._tstamp_seed = uuid.UUID(str(tstamp_seed))
        if (tstamp_seed is not None):
            self.updateTStampConditionally()

    def __init__(self, tstamp: uuid.UUID | str | None = None, tstamp_seed: uuid.UUID | None = None,
                 parent: Node = None, unique_id: str | None = None) -> None:
        if tstamp is not None:
            tstamp = self.parseAsUUID(tstamp)
        self._tstamp: uuid.UUID | str | None = tstamp

        if tstamp_seed is not None:
            tstamp_seed = self.parseAsUUID(tstamp_seed)
        self._tstamp_seed: uuid.UUID | None = tstamp_seed

        fixed = (tstamp is not None) and (tstamp_seed is None)
        self._isTStampManualFixed: bool = fixed

        if unique_id is not None:
            unique_id = str(unique_id)
        self._unique_id: str | None = unique_id

        if parent is not None and not isinstance(parent, Node):
            print(f"WARNING: Parent should be a Node: {print_stack()}")
        self._parentNode: Node | None = parent

    def __str__(self) -> str:
        return str(self.getTStamp())

    def __repr__(self) -> str:
        return (f"TStamp(tstamp='{str(self.getTStamp())}', "
                + f"tstamp_seed='{self.getTStampSeed()}', unique_id='{self.getUniqueID()}')")


class Node(object):
    def __init__(self):
        self._parent = None
        self._childs = []

        self._tstamp = TStamp(parent=self)

    def hasValidTStamp(self) -> bool:
        return self._tstamp.isTStampValid()

    def hasValidSeedForTStamp(self) -> bool:
        return self._tstamp.isTStampSeedValid()

    def setTStampSeedFromNode(self, node: Node):
        if node.getTStampCls().getTStampSeed() is not None:
            return self._tstamp.setTStampSeed(node.getTStampCls().getTStampSeed())
        else:
            return None

    def getTStampCls(self) -> TStamp:
        return self._tstamp

    def setTStamp(self, tstamp: uuid.UUID | str | TStamp):
        if isinstance(tstamp, TStamp):
            self._tstamp = tstamp
        else:
            self._tstamp.setTStamp(tstamp)

    def getTStamp(self) -> uuid.UUID | str | None:
        return self._tstamp.getTStamp()

    @staticmethod
    def _cleanup_to_hash_dict(obj_dict):
        hash_dict = {}
        if "polygon_nodes_raw" in obj_dict.keys():
            pass
        for k, v in obj_dict.items():
            if k in ["_parent", "_tstamp"]:
                continue
            if hasattr(v, '_deterministic_hash'):
                v = v._deterministic_hash()
            elif hasattr(v, '_hashdict'):
                v = v._hashdict()
            elif (isinstance(v, str) or isinstance(v, int) or isinstance(v, float) or isinstance(v, Vector2D)
                  or isinstance(v, Vector3D) or isinstance(v, TStamp) or isinstance(v, Enum)):
                v = str(v)
            else:
                # complex types may contain objects that would return hashes based
                # on run-time memory locations, which are unstable, skip
                v = "[...]"
            hash_dict[k] = v
        return hash_dict

    def _hashdict(self):
        hash_dict = self._cleanup_to_hash_dict(self.__dict__)
        return hash_dict

    def _deterministic_hash(self):
        return sha1(repr(self._hashdict()).encode('utf-8'))

    def __hash__(self):
        return int.from_bytes(self._deterministic_hash().digest(), byteorder='little')

    def __iter__(self):
        return self.allChildItems()

    def __len__(self):
        return len(self.getNormalChilds()) + len(self.getVirtualChilds())

    def append(self, node):
        '''
        add node to child nodes
        '''
        if not isinstance(node, Node):
            raise TypeError('invalid object, has to be based on Node')

        if node._parent:
            raise MultipleParentsError('muliple parents are not allowed!')

        self._childs.append(node)

        node._parent = self
        if (node.getTStampCls().getTStampSeed() is None) and (self.getTStampCls().getTStampSeed() is not None):
            node.setTStampSeedFromNode(self)

    def extend(self, nodes):
        '''
        add list of nodes to child nodes
        '''
        new_nodes = []
        for node in nodes:
            if not isinstance(node, Node):
                raise TypeError('invalid object, has to be based on Node')

            if node._parent or node in new_nodes:
                raise MultipleParentsError('muliple parents are not allowed!')

            new_nodes.append(node)

        # when all went smooth by now, we can set the parent nodes to ourself
        for node in new_nodes:
            node._parent = self
            if (node.getTStampCls().getTStampSeed() is None) and (self.getTStampCls().getTStampSeed() is not None):
                node.setTStampSeedFromNode(self)

        self._childs.extend(new_nodes)

    @staticmethod
    def _removeNode(*, parent, node, virtual: bool = False):
        '''
        remove child from node
        '''
        if not isinstance(node, Node):
            raise TypeError('invalid object, has to be based on Node')

        removed = False

        while node in parent.getNormalChilds():
            parent.getNormalChilds().remove(node)
            removed = True

        if virtual:
            while node in parent.getVirtualChilds():
                parent.getVirtualChilds().remove(node)
                removed = True

        if (removed):
            node._parent = None

    def remove(self, node, traverse: bool = False, virtual: bool = False):
        '''
        remove child from node or from the tree
        '''
        if not isinstance(node, Node):
            raise TypeError('invalid object, has to be based on Node')

        if not virtual and node in self.getVirtualChilds():
            raise VirtualNodeError(
                'the node you are trying to remove is virtual')

        if (not traverse):
            self._removeNode(parent=self, node=node, virtual=virtual)
        else:
            if (node == self):
                if (node._parent):
                    self._removeNode(parent=node._parent,
                                     node=node, virtual=virtual)
            else:
                for child in self.allChildItems() if virtual else self.normalChildItems():
                    child.remove(node, traverse=traverse, virtual=virtual)

    def insert(self, node):
        '''
        moving all childs into the node, and using the node as new parent of those childs
        '''
        if not isinstance(node, Node):
            raise TypeError('invalid object, has to be based on Node')

        for child in copy(self._childs):
            self.remove(child)
            node.append(child)

        self.append(node)

    def copy(self):
        copy = deepcopy(self)
        copy._parent = None
        return copy

    def serialize(self):
        nodes = [self]
        for child in self.getAllChilds():
            nodes += child.serialize()
        return nodes

    def getNormalChilds(self):
        '''
        Get all normal childs of this node
        '''
        return self._childs

    def normalChildItems(self):
        return iter(self.getNormalChilds())

    def getVirtualChilds(self):
        '''
        Get virtual childs of this node
        '''
        return []

    def virtualChildItems(self):
        """
        virtual child iterator
        """
        return iter(self.getVirtualChilds())

    def getAllChilds(self):
        '''
        Get virtual and normal childs of this node
        '''
        return self.getNormalChilds() + self.getVirtualChilds()

    def allChildItems(self):
        for c in self.normalChildItems():
            yield c
        for c in self.virtualChildItems():
            yield c

    @property
    def num_virtual_nodes(self):
        return len(self.getVirtualChilds())

    @property
    def num_normal_nodes(self):
        return len(self.getNormalChilds())

    @property
    def num_all_nodes(self):
        return self.num_virtual_nodes + self.num_normal_nodes

    def getParent(self):
        '''
        get Parent Node of this Node
        '''
        return self._parent

    def getRootNode(self):
        '''
        get Root Node of this Node
        '''

        # TODO: recursion detection
        if not self.getParent():
            return self

        return self.getParent().getRootNode()

    def getRealPosition(self, coordinate, rotation=None):
        '''
        return position of point after applying all transformation and rotation operations
        '''
        if not self._parent:
            if rotation is None:
                # TODO: most of the points are 2D Nodes
                return Vector3D(coordinate)
            else:
                return Vector3D(coordinate), rotation

        return self._parent.getRealPosition(coordinate, rotation)

    def calculateBoundingBox(self, outline=None):
        min_x, min_y = math.inf, math.inf
        max_x, max_y = -math.inf, -math.inf

        if outline:
            min_x = outline['min']['x']
            min_y = outline['min']['y']
            max_x = outline['max']['x']
            max_y = outline['max']['y']

        for child in self.getAllChilds():
            child_outline = child.calculateBoundingBox()

            min_x = min([min_x, child_outline['min']['x']])
            min_y = min([min_y, child_outline['min']['y']])
            max_x = max([max_x, child_outline['max']['x']])
            max_y = max([max_y, child_outline['max']['y']])

        return {'min': Vector2D(min_x, min_y), 'max': Vector2D(max_x, max_y)}

    def _getRenderTreeText(self):
        '''
        Text which is displayed when generating a render tree
        '''
        return type(self).__name__

    def _getRenderTreeSymbol(self):
        '''
        Symbol which is displayed when generating a render tree
        '''
        if self._parent is None:
            return "+"

        return "*"

    def getRenderTree(self, rendered_nodes=None):
        '''
        print render tree
        '''
        if rendered_nodes is None:
            rendered_nodes = set()

        if self in rendered_nodes:
            raise RecursionDetectedError(
                'recursive definition of render tree!')

        rendered_nodes.add(self)

        tree_str = "{0} {1}".format(
            self._getRenderTreeSymbol(), self._getRenderTreeText())
        for child in self.getNormalChilds():
            tree_str += '\n  '
            tree_str += '  '.join(child.getRenderTree(rendered_nodes).splitlines(True))

        return tree_str

    def getCompleteRenderTree(self, rendered_nodes=None):
        '''
        print virtual render tree
        '''
        if rendered_nodes is None:
            rendered_nodes = set()

        if self in rendered_nodes:
            raise RecursionDetectedError(
                'recursive definition of render tree!')

        rendered_nodes.add(self)

        tree_str = "{0} {1}".format(
            self._getRenderTreeSymbol(), self._getRenderTreeText())
        for child in self.getAllChilds():
            tree_str += '\n  '
            tree_str += '  '.join(child.getCompleteRenderTree(
                rendered_nodes).splitlines(True))

        return tree_str
