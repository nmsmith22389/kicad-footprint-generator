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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# modifications 2022 by Armin Schoisswohl (@armin.sch)
# (C) The KiCad Librarian Team

"""Class definition for the base node."""

from __future__ import annotations

import copy
import uuid
from abc import ABC
from collections.abc import Iterator, Sequence
from enum import Enum
from hashlib import sha1
from traceback import print_stack
from typing import Any, Protocol, Self, runtime_checkable

from _hashlib import HASH

from kilibs.geom import BoundingBox, Vector2D, Vector3D


class MultipleParentsError(RuntimeError):
    def __init__(self, message: str) -> None:
        # Call the base class constructor with the parameters it needs
        super(MultipleParentsError, self).__init__(message)


class RecursionDetectedError(RuntimeError):
    def __init__(self, message: str) -> None:
        # Call the base class constructor with the parameters it needs
        super(RecursionDetectedError, self).__init__(message)


@runtime_checkable
class HasCallableHashDict(Protocol):
    def hashdict(self) -> str: ...


class TStamp(object):
    """A timestamp."""

    _tstamp: uuid.UUID | str | None
    """The timestamp."""
    _tstamp_seed: uuid.UUID | None
    """The timestamp seed."""
    _unique_id: str | None
    """The unique ID."""
    _isTStampManualFixed: bool
    """`True` if the timestamp is manually fixed."""
    _parentNode: Node | None
    """The parent node."""

    @staticmethod
    def parseAsUUID(tstamp_uuid: str | uuid.UUID) -> uuid.UUID:
        """Convert the argument to a UUID.

        Args:
            tstamp_uuid: The argument to convert.

        Returns:
            The UUID.
        """
        if isinstance(tstamp_uuid, uuid.UUID):
            return tstamp_uuid
        else:
            return uuid.UUID(str(tstamp_uuid))

    @staticmethod
    def parseTStamp(tstamp: TStamp | str) -> TStamp:
        """Convert the argument to a timestamp.

        Args:
            tstamp_uuid: The argument to convert.

        Returns:
            The timestamp.
        """
        if isinstance(tstamp, TStamp):
            return tstamp
        else:
            return TStamp(tstamp=TStamp.parseAsUUID(tstamp))

    def setUniqueID(self, unique_id: uuid.UUID) -> None:
        """Set the UUID.

        Args:
            unique_id: The UUID.
        """
        self._unique_id = str(unique_id)
        self.updateTStampConditionally()

    def unsetTStamp(self) -> None:
        """Unset the timestamp."""
        self._tstamp = None
        self._tstamp_seed = None
        self._unique_id = None
        self._isTStampManualFixed = False

    def setParentNode(self, node: Node) -> None:
        """Set the parent node.

        Args:
            node: The parent node.
        """
        self._parentNode = node

    def getParentNode(self) -> Node | None:
        """Return the parent node."""
        return self._parentNode

    def isTStampValid(self) -> bool:
        """Return if the timestamp is valid or not."""
        return (self._tstamp is not None) and (self._tstamp != "")

    def isTStampSeedValid(self) -> bool:
        """Return if the timestamp seed is valid or not."""
        return (self._tstamp_seed is not None) and (self._tstamp_seed != "")

    def getUniqueID(self) -> str | None:
        """Return the UUID."""
        return self._unique_id

    def getTStamp(self) -> uuid.UUID | str | None:
        """Return the timestamp."""
        return self._tstamp

    def setTStamp(self, tstamp: uuid.UUID | str, tstamp_fixed: bool = True) -> None:
        """ "Set the timestamp.

        Args:
            tsamp: The timestamp.
            tsamp_fixed: `True` if the timestamp shall be considered to be manually
                fixed, i.e. it will not be changed when updating the timestamp."""
        self._tstamp = uuid.UUID(str(tstamp))
        self._isTStampManualFixed = tstamp_fixed

    def returnDerivedTStamp(
        self,
        unique_id: str | None = None,
        obj: object | None = None,
        seed: uuid.UUID | None = None,
        use_obj_hash: bool = True,
        hash_using_dict: bool = True,
    ) -> uuid.UUID:
        """Derive a timestamp from one of the given arguments.

        Args:
            unique_id: Optional UUID that is used hashed and used as seed to generate
                a new UUID.
            obj: An optional object whose class name is used as seed to generate a new
                UUID. If `use_obj_hash` is `True` its object dictionary is also used as
                seed.
            seed: An optional UUID that is used as a seed to generate a new UUID.
            use_obj_hash: See description of `hash_using_dict`.
            hash_using_dict: If `use_obj_hash` is `True` and an object is passed as
                argument `obj`, the UUID is derived from the SHA-1 hash of the string
                representation of the object (__repr__(obj)) if `has_using_dict` is
                `True`, otherwise it is derived from the hash value of the object
                itself.
        """
        if use_obj_hash:
            if obj is not None:
                d: str | dict[str, Any]
                if isinstance(obj, HasCallableHashDict):
                    d = obj.hashdict()
                else:
                    # consider using hash_str = sha1( str(obj.__hash__()).encode('utf-8') ).hexdigest()
                    d = Node.cleanup_to_hash_dict(obj.__dict__)
                hash_str = (
                    sha1(repr(d).encode("utf-8")).hexdigest()
                    if hash_using_dict
                    else hash(obj)
                )
            else:
                hash_str = "None"
        else:
            hash_str = "*"
        if seed is None:
            seed = self._tstamp_seed
        if seed is not None:
            return uuid.uuid5(
                namespace=seed,
                name=f"KicadModTree.Node.{str(obj.__class__.__name__)}.{str(unique_id)}.{str(hash_str)}",
            )
        else:
            raise RuntimeError(
                f"Timestamp of node {repr(self._parentNode)} was not initialized before requesting it."
            )

    def reCalcTStamp(self) -> uuid.UUID | str | None:
        """If the timestamp is not manually fixed, update the timestamp by using the
        parent node as object to derive the timestamp from (see:
        `returnDerivedTStamp()`)."""
        if not self._isTStampManualFixed:
            self._tstamp = self.returnDerivedTStamp(
                unique_id=self.getUniqueID(),
                obj=self._parentNode,
                seed=self.getTStampSeed(),
                use_obj_hash=True,
            )
        else:
            print("WARNING: TStamp is fixed at:")
            print_stack()
        return self.getTStamp()

    def getTStampSeed(self) -> uuid.UUID | None:
        """Return the timestamp seed."""
        return self._tstamp_seed

    def initializeTStampSeed(self) -> uuid.UUID | None:
        """Initialize the timestamp seed and return it."""
        self.setTStampSeed(
            uuid.uuid5(
                namespace=uuid.uuid1(),
                name=f"KicadModTree.Node.{str(self.__class__.__name__)}.{str(self._unique_id)}",
            )
        )
        return self.getTStampSeed()

    def updateTStampConditionally(self) -> uuid.UUID | str | None:
        """Update the timestamp if it is not manually fixed and return it."""
        if (self._tstamp is None) or (not self._isTStampManualFixed):
            return self.reCalcTStamp()
        else:
            return self.getTStamp()

    def setTStampSeed(self, tstamp_seed: uuid.UUID | str | None) -> None:
        """Set the timestamp seed."""
        self._tstamp_seed = uuid.UUID(str(tstamp_seed))
        if tstamp_seed is not None:
            self.updateTStampConditionally()

    def __init__(
        self,
        tstamp: uuid.UUID | str | None = None,
        tstamp_seed: uuid.UUID | None = None,
        parent: Node | None = None,
        unique_id: str | None = None,
    ) -> None:
        """Create a timestamp.

        Args:
            tstamp: The optional value of the timestamp.
            tstamp_seed: The optional seed of the timestamp.
            parent: The optional parent Node of the timestamp.
            unique_id: The optinoal UUID.
        """
        if tstamp is not None:
            tstamp = self.parseAsUUID(tstamp)
        self._tstamp = tstamp

        if tstamp_seed is not None:
            tstamp_seed = self.parseAsUUID(tstamp_seed)
        self._tstamp_seed = tstamp_seed

        fixed = (tstamp is not None) and (tstamp_seed is None)
        self._isTStampManualFixed = fixed

        if unique_id is not None:
            unique_id = str(unique_id)
        self._unique_id = unique_id

        self._parentNode = parent

    def __str__(self) -> str:
        """Return the timestamp as a string."""
        return str(self.getTStamp())

    def __repr__(self) -> str:
        """Return the string representation of the timestamp."""
        return (
            f"TStamp(tstamp='{str(self.getTStamp())}', "
            + f"tstamp_seed='{self.getTStampSeed()}', unique_id='{self.getUniqueID()}')"
        )


class Node(ABC):
    """The abstract base node."""

    _parent: Node | None
    """The parent node."""
    _childs: list[Node]
    """"The child nodes."""
    _tstamp: TStamp
    """The timestamp."""

    def __init__(self) -> None:
        """Create a node."""
        self._parent = None
        self._childs = []
        self._tstamp = TStamp(parent=self)

    def hasValidTStamp(self) -> bool:
        """Return whether the node has a valid timestamp or not."""
        return self._tstamp.isTStampValid()

    def hasValidSeedForTStamp(self) -> bool:
        """Return whether the node has a valid timestamp seed or not."""
        return self._tstamp.isTStampSeedValid()

    def setTStampSeedFromNode(self, node: Node) -> None:
        """Sets the timestamp by using the nodes' timestamps' seed."""
        if node.getTStampCls().getTStampSeed() is not None:
            return self._tstamp.setTStampSeed(node.getTStampCls().getTStampSeed())
        else:
            return None

    def getTStampCls(self) -> TStamp:
        """Return the timestamp object (class) of the node."""
        return self._tstamp

    def setTStamp(self, tstamp: uuid.UUID | str | TStamp) -> None:
        """Return the timestamp UUID of the node."""
        if isinstance(tstamp, TStamp):
            self._tstamp = tstamp
        else:
            self._tstamp.setTStamp(tstamp)

    def getTStamp(self) -> uuid.UUID | str | None:
        """Return the timestamp of the node."""
        return self._tstamp.getTStamp()

    @staticmethod
    def cleanup_to_hash_dict(obj_dict: dict[str, Any]) -> dict[str, Any]:
        """Clean up the object dictionary passed as argument for the purpose of hashing
        it and using it to derive a UUID or timestamp from.

        Args:
            obj_dict: The object dictionary.

        Returns:
            The cleaned up object dictionary.
        """
        hash_dict: dict[str, Any] = {}
        if "polygon_nodes_raw" in obj_dict.keys():
            pass
        for k, v in obj_dict.items():
            if k in ["_parent", "_tstamp"]:
                continue
            if hasattr(v, "_deterministic_hash"):
                v = v._deterministic_hash()
            elif isinstance(v, HasCallableHashDict):
                v = v.hashdict()
            elif (
                isinstance(v, str)
                or isinstance(v, int)
                or isinstance(v, float)
                or isinstance(v, Vector2D)
                or isinstance(v, Vector3D)
                or isinstance(v, TStamp)
                or isinstance(v, Enum)
            ):
                v = str(v)
            else:
                # complex types may contain objects that would return hashes based
                # on run-time memory locations, which are unstable, skip
                v = "[...]"
            hash_dict[k] = v
        return hash_dict

    def hashdict(self) -> dict[str, Any]:
        """Clean up this node's dictionary for the purpose of hashing it and return it."""
        hash_dict = self.cleanup_to_hash_dict(self.__dict__)
        return hash_dict

    def _deterministic_hash(self) -> HASH:
        """Return a deterministic SHA1 hash of this object."""
        return sha1(repr(self.hashdict()).encode("utf-8"))

    def __hash__(self) -> int:
        """Return this object's SHA1 hash as an integer."""
        return int.from_bytes(self._deterministic_hash().digest(), byteorder="little")

    def __iter__(self) -> Iterator[Node]:
        """Return an iterator to iterate through all child nodes of this object."""
        return iter(self.get_child_nodes())

    def __len__(self) -> int:
        """Return the number of children this node has."""
        return len(self.get_child_nodes())

    def append(self, node: Node) -> None:
        """Add a node as child node.

        Args:
            node: The node to add.
        """
        if node._parent:
            raise MultipleParentsError("muliple parents are not allowed!")

        self._childs.append(node)

        node._parent = self
        if (node.getTStampCls().getTStampSeed() is None) and (
            self.getTStampCls().getTStampSeed() is not None
        ):
            node.setTStampSeedFromNode(self)

    def extend(self, nodes: Sequence[Node]) -> None:
        """Add a list of nodes as child nodes."""
        new_nodes: list[Node] = []

        for node in nodes:
            if node._parent or node in new_nodes:
                raise MultipleParentsError("muliple parents are not allowed!")
            new_nodes.append(node)

        # when all went smooth by now, we can set the parent nodes to ourself
        for node in new_nodes:
            node._parent = self
            if (node.getTStampCls().getTStampSeed() is None) and (
                self.getTStampCls().getTStampSeed() is not None
            ):
                node.setTStampSeedFromNode(self)

        self._childs.extend(new_nodes)

    def __add__(self, nodes: Node | Sequence[Node]) -> Self:
        """Convenience function to allow simple append/extend to a Node."""
        if isinstance(nodes, Node):
            self.append(nodes)
        else:
            self.extend(nodes)

        return self

    @staticmethod
    def _removeNode(*, parent: Node, node: Node) -> None:
        """Remove a child from the list of child nodes of a given parent node.

        Args:
            parent: The parent node.
            node: The node to remove.
        """
        child_nodes = parent.get_child_nodes()
        while node in child_nodes:
            child_nodes.remove(node)
            node._parent = None

    def remove(self, node: Node, traverse: bool = False) -> None:
        """Remove a node from this node's list of child nodes.

        Args:
            node: The node to remove.
            traverse: If `True` then the children are recursively searched for a match
                within their children.
        """
        if not traverse:
            Node._removeNode(parent=self, node=node)
        else:
            if node == self:
                if node._parent:
                    Node._removeNode(parent=node._parent, node=node)
            else:
                for child in self.get_child_nodes():
                    child.remove(node, traverse=traverse)

    def insert(self, node: Node) -> None:
        """Move all child nodes from this node into the given node and append the given
        node to this node.

        Args:
            node: The node that becomes the new parent node of this node's children.
        """
        for child in copy.copy(self._childs):
            self.remove(child)
            node.append(child)
        self.append(node)

    def copy(self) -> Self:
        """Create a copy of itself."""
        copied_node = copy.copy(self)
        copied_node._parent = None
        return copied_node

    def translate(self, vector: Vector2D) -> Self:
        """Move the node.

        Args:
            vector: The distance in mm in the x- and y-direction.

        Returns:
            The translated node.
        """
        # Note: nodes that need this functionality need to implement this method.
        return self

    def translated(self, vector: Vector2D) -> Self:
        """Create a copy of the node and move it.

        Args:
            vector: The distance in mm in the x- and y-direction.

        Returns:
            The translated copy of the node.
        """
        return self.copy().translate(vector)

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
        use_degrees: bool = True,
    ) -> Self:
        """Rotate the node around a given point.

        Args:
            angle: Rotation angle.
            origin: Coordinates (in mm) of the point around which to rotate.
            use_degrees: `True` if rotation angle is given in degrees, `False` if given
                in radians.

        Returns:
            The rotated node.
        """
        # Note: nodes that need this functionality need to implement this method.
        return self

    def rotated(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
        use_degrees: bool = True,
    ) -> Self:
        """Create a copy of the node and rotate it around a given point.

        Args:
            angle: Rotation angle.
            origin: Coordinates (in mm) of the point around which to rotate.
            use_degrees: `True` if rotation angle is given in degrees, `False` if given
                in radians.

        Returns:
            The rotated copy of the node.
        """
        return self.copy().rotate(angle=angle, origin=origin, use_degrees=use_degrees)

    def get_flattened_nodes(self) -> list[Node]:
        """Return a flattened list of all the child nodes. The child nodes that are
        child of a transform node (Rotation or Translation) are copied and transformed
        before being added to the list."""
        return [self]

    def get_child_nodes(self) -> list[Node]:
        """Return the direct child nodes."""
        return self._childs

    def getParent(self) -> Node | None:
        """Return the parent node of this node."""
        return self._parent

    def getRootNode(self) -> Node:
        """Return the root node of this node."""

        # TODO: recursion detection
        if not self._parent:
            return self
        else:
            return self._parent.getRootNode()

    def bbox(self) -> BoundingBox:
        """
        Get the bounding box of the node. This is in its own context, so it is
        independent of the parent nodes' transformation, but does incldue any
        transformation it applies itself.

        Example:
            >>> translation_node = Translation(-10, 0)
            >>> line = Line(start=(0, 0), end=(1, 1))
            >>> translation.append(line)
            >>> line.bbox()
            >>> bbox.min, bbox.max
                Vector2D(0, 0), Vector2D(1, 1)
            >>> line.translate(Vector2D(10, 0))
            >>> line.bbox()
            >>> bbox.min, bbox.max
                Vector2D(10, 0), Vector2D(11, 1)
        """
        bbox = BoundingBox()
        for child in self.get_child_nodes():
            child_bbox = child.bbox()
            bbox.include_bbox(child_bbox)
        return bbox

    def __repr__(self) -> str:
        """The string representation of the Node."""
        class_name = self.__class__.__name__
        return f"{class_name}(parent={self._parent})"

    def _getRenderTreeSymbol(self) -> str:
        """Symbol which is displayed when generating a render tree."""
        return "+" if self._parent is None else "*"

    def getRenderTree(self, rendered_nodes: set[Node] = set()) -> str:
        """Return the render tree of this node including only the real children.

        Args:
            rendered_nodes: A set containing the nodes.
        """

        if self in rendered_nodes:
            raise RecursionDetectedError("recursive definition of render tree!")

        rendered_nodes.add(self)

        tree_str = f"{self._getRenderTreeSymbol()} {self.__repr__()}"

        for child in self.get_child_nodes():
            tree_str += "\n  "
            tree_str += "  ".join(child.getRenderTree(rendered_nodes).splitlines(True))

        return tree_str

    def getCompleteRenderTree(self, rendered_nodes: set[Node] = set()) -> str:
        """Return the render tree of this node including the real and the virtual
        children.

        Args:
            rendered_nodes: A set containing the nodes.
        """

        if self in rendered_nodes:
            raise RecursionDetectedError("recursive definition of render tree!")

        rendered_nodes.add(self)

        tree_str = f"{self._getRenderTreeSymbol()} {self.__repr__()}"

        for child in self.get_child_nodes():
            tree_str += "\n  "
            tree_str += "  ".join(
                child.getCompleteRenderTree(rendered_nodes).splitlines(True)
            )

        return tree_str
