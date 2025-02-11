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

import pytest

from KicadModTree.nodes.Node import *


class HelperTestChildNode(Node):
    def __init__(self):
        Node.__init__(self)


class HelperNodeWithVirtualChilds(Node):
    def __init__(self, *, normal_childs, virtual_childs=[]):
        Node.__init__(self)
        for c in normal_childs:
            self.append(c)
        self._virtual_childs = []
        for c in virtual_childs:
            self._virtual_childs.append(c)
            c._parent = self

    def getVirtualChilds(self):
        return self._virtual_childs


def testInit():
    node = Node()
    assert node.getParent() is None
    assert node.getRootNode() is node
    assert len(node.getNormalChilds()) == 0
    assert len(node.getVirtualChilds()) == 0
    assert len(node.getAllChilds()) == 0


def testAppend():
    node = Node()
    assert len(node.getNormalChilds()) == 0

    childNode1 = Node()
    node.append(childNode1)
    assert childNode1 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert len(node.getNormalChilds()) == 1

    childNode2 = Node()
    node.append(childNode2)
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 2

    with pytest.raises(TypeError):
        node.append(None)
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 2

    with pytest.raises(TypeError):
        node.append(object)
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 2

    with pytest.raises(TypeError):
        node.append("a string is not a node object")
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 2

    with pytest.raises(MultipleParentsError):
        node.append(childNode1)
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 2

    childNode3 = HelperTestChildNode()
    node.append(childNode3)
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode3 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert childNode3.getParent() == node
    assert len(node.getNormalChilds()) == 3


def testExtend():
    node = Node()
    assert len(node.getNormalChilds()) == 0

    childNode1 = Node()
    childNode2 = Node()
    node.extend([childNode1, childNode2])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 2

    childNode3 = Node()
    node.extend([childNode3])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode3 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert childNode3.getParent() == node
    assert len(node.getNormalChilds()) == 3

    node.extend([])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode3 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert childNode3.getParent() == node
    assert len(node.getNormalChilds()) == 3

    with pytest.raises(TypeError):
        node.extend([None])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode3 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert childNode3.getParent() == node
    assert len(node.getNormalChilds()) == 3

    with pytest.raises(TypeError):
        node.append([object])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode3 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert childNode3.getParent() == node
    assert len(node.getNormalChilds()) == 3

    with pytest.raises(TypeError):
        node.append(["a string is not a node object"])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode3 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert childNode3.getParent() == node
    assert len(node.getNormalChilds()) == 3

    with pytest.raises(MultipleParentsError):
        node.extend([childNode1])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode3 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert childNode3.getParent() == node
    assert len(node.getNormalChilds()) == 3

    childNode4 = Node()
    childNode5 = Node()
    with pytest.raises(MultipleParentsError):
        node.extend([childNode4, childNode5, childNode5])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode3 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert childNode3.getParent() == node
    assert childNode4.getParent() is None
    assert childNode5.getParent() is None
    assert len(node.getNormalChilds()) == 3


def testRemove():
    node = Node()
    assert len(node.getNormalChilds()) == 0

    childNode1 = Node()
    childNode2 = Node()
    node.extend([childNode1, childNode2])
    assert childNode1 in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 2

    node.remove(childNode1)
    assert childNode1 not in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() is None
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 1

    node.remove(childNode1)
    assert childNode1 not in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() is None
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 1

    with pytest.raises(TypeError):
        node.remove([None])
    assert childNode1 not in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() is None
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 1

    with pytest.raises(TypeError):
        node.remove([object])
    assert childNode1 not in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() is None
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 1

    with pytest.raises(TypeError):
        node.remove(["a string is not a node object"])
    assert childNode1 not in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() is None
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 1


def testInsert():
    node = Node()
    assert len(node.getNormalChilds()) == 0

    childNode1 = Node()
    node.insert(childNode1)
    assert childNode1 in node.getNormalChilds()
    assert childNode1.getParent() == node
    assert len(node.getNormalChilds()) == 1

    childNode2 = Node()
    node.insert(childNode2)
    assert childNode1 in childNode2.getNormalChilds()
    assert childNode1 not in node.getNormalChilds()
    assert childNode2 in node.getNormalChilds()
    assert childNode1.getParent() == childNode2
    assert childNode2.getParent() == node
    assert len(node.getNormalChilds()) == 1
    assert len(childNode1.getNormalChilds()) == 0
    assert len(childNode2.getNormalChilds()) == 1


def testInsertWithManyChilds():
    node = Node()
    assert len(node.getNormalChilds()) == 0

    for i in range(0, 200):
        node.append(Node())

    insertNode = Node()
    assert len(node.getNormalChilds()) == 200
    assert len(insertNode.getNormalChilds()) == 0
    node.insert(insertNode)
    assert len(node.getNormalChilds()) == 1
    assert len(insertNode.getNormalChilds()) == 200


def testRemoveTraversed():
    parent = Node()
    gen1a = Node()
    gen1b = Node()
    gen1a1 = Node()
    gen1a2 = Node()

    gen1a.append(gen1a1)
    gen1a.append(gen1a2)
    parent.append(gen1a)
    parent.append(gen1b)

    assert len(parent.getAllChilds()) == 2
    assert len(gen1a.getAllChilds()) == 2
    assert len(gen1b.getAllChilds()) == 0

    # try to remove gen1a1 from parent directly
    parent.remove(gen1a1)
    assert len(parent.getAllChilds()) == 2
    assert len(gen1a.getAllChilds()) == 2
    assert gen1a1._parent is not None
    assert len(gen1b.getAllChilds()) == 0

    # remove gen1a1 from parent (traversing through the hierarchy))
    parent.remove(gen1a1, traverse=True)
    assert len(parent.getAllChilds()) == 2
    assert len(gen1a.getAllChilds()) == 1
    assert gen1a1._parent is None
    assert len(gen1b.getAllChilds()) == 0

    # remove gen1a from parent
    parent.remove(gen1a)
    assert len(parent.getAllChilds()) == 1
    assert len(gen1a.getAllChilds()) == 1
    assert gen1a._parent is None
    assert len(gen1b.getAllChilds()) == 0


def testRemoveVirtual():
    node = HelperNodeWithVirtualChilds(
        normal_childs=[Node() for _ in range(3)],
        virtual_childs=[Node() for _ in range(5)],
    )
    assert node.num_normal_nodes == 3
    assert node.num_virtual_nodes == 5
    assert node.num_all_nodes == 8

    parent = Node()
    parent.append(node)

    for n in range(node.num_virtual_nodes):
        c = node.getVirtualChilds()[n]
        pytest.raises(VirtualNodeError, Node.remove, node, c)
        pytest.raises(VirtualNodeError, Node.remove, parent, c, traverse=True)
        assert node.num_all_nodes == 8

    for c in node.allChildItems():
        parent.remove(c)
        assert node.num_all_nodes == 8

    count = node.num_all_nodes
    for _ in range(node.num_all_nodes):
        parent.remove(node.getAllChilds()[0], traverse=True, virtual=True)
        count -= 1
        assert node.num_all_nodes == count


def testIter():
    node = HelperNodeWithVirtualChilds(
        normal_childs=[Node() for _ in range(3)],
        virtual_childs=[Node() for _ in range(5)],
    )
    assert node.num_normal_nodes == 3
    assert node.num_virtual_nodes == 5
    assert node.num_all_nodes == 8

    count = 0
    for _ in node.normalChildItems():
        count += 1
    assert count == node.num_normal_nodes

    count = 0
    for _ in node:
        count += 1
    assert count == node.num_all_nodes
    assert len(node) == node.num_all_nodes

    count = 0
    for _ in node.virtualChildItems():
        count += 1
    assert count == node.num_virtual_nodes

    count = 0
    for _ in node.allChildItems():
        count += 1
    assert count == node.num_all_nodes
