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

import unittest

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


class NodeTests(unittest.TestCase):

    def testInit(self):
        node = Node()
        self.assertIs(node.getParent(), None)
        self.assertIs(node.getRootNode(), node)
        self.assertEqual(len(node.getNormalChilds()), 0)
        self.assertEqual(len(node.getVirtualChilds()), 0)
        self.assertEqual(len(node.getAllChilds()), 0)

    def testAppend(self):
        node = Node()
        self.assertEqual(len(node.getNormalChilds()), 0)

        childNode1 = Node()
        node.append(childNode1)
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 1)

        childNode2 = Node()
        node.append(childNode2)
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 2)

        with self.assertRaises(TypeError):
            node.append(None)
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 2)

        with self.assertRaises(TypeError):
            node.append(object)
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 2)

        with self.assertRaises(TypeError):
            node.append("a string is not a node object")
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 2)

        with self.assertRaises(MultipleParentsError):
            node.append(childNode1)
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 2)

        childNode3 = HelperTestChildNode()
        node.append(childNode3)
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertIn(childNode3, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(childNode3.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 3)

    def testExtend(self):
        node = Node()
        self.assertEqual(len(node.getNormalChilds()), 0)

        childNode1 = Node()
        childNode2 = Node()
        node.extend([childNode1, childNode2])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 2)

        childNode3 = Node()
        node.extend([childNode3])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertIn(childNode3, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(childNode3.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 3)

        node.extend([])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertIn(childNode3, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(childNode3.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 3)

        with self.assertRaises(TypeError):
            node.extend([None])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertIn(childNode3, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(childNode3.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 3)

        with self.assertRaises(TypeError):
            node.append([object])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertIn(childNode3, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(childNode3.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 3)

        with self.assertRaises(TypeError):
            node.append(["a string is not a node object"])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertIn(childNode3, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(childNode3.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 3)

        with self.assertRaises(MultipleParentsError):
            node.extend([childNode1])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertIn(childNode3, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(childNode3.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 3)

        childNode4 = Node()
        childNode5 = Node()
        with self.assertRaises(MultipleParentsError):
            node.extend([childNode4, childNode5, childNode5])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertIn(childNode3, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(childNode3.getParent(), node)
        self.assertEqual(childNode4.getParent(), None)
        self.assertEqual(childNode5.getParent(), None)
        self.assertEqual(len(node.getNormalChilds()), 3)

    def testRemove(self):
        node = Node()
        self.assertEqual(len(node.getNormalChilds()), 0)

        childNode1 = Node()
        childNode2 = Node()
        node.extend([childNode1, childNode2])
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 2)

        node.remove(childNode1)
        self.assertNotIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), None)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 1)

        node.remove(childNode1)
        self.assertNotIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), None)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 1)

        with self.assertRaises(TypeError):
            node.remove([None])
        self.assertNotIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), None)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 1)

        with self.assertRaises(TypeError):
            node.remove([object])
        self.assertNotIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), None)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 1)

        with self.assertRaises(TypeError):
            node.remove(["a string is not a node object"])
        self.assertNotIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), None)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 1)

    def testInsert(self):
        node = Node()
        self.assertEqual(len(node.getNormalChilds()), 0)

        childNode1 = Node()
        node.insert(childNode1)
        self.assertIn(childNode1, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 1)

        childNode2 = Node()
        node.insert(childNode2)
        self.assertIn(childNode1, childNode2.getNormalChilds())
        self.assertNotIn(childNode1, node.getNormalChilds())
        self.assertIn(childNode2, node.getNormalChilds())
        self.assertEqual(childNode1.getParent(), childNode2)
        self.assertEqual(childNode2.getParent(), node)
        self.assertEqual(len(node.getNormalChilds()), 1)
        self.assertEqual(len(childNode1.getNormalChilds()), 0)
        self.assertEqual(len(childNode2.getNormalChilds()), 1)

    def testInsertWithManyChilds(self):
        node = Node()
        self.assertEqual(len(node.getNormalChilds()), 0)

        for i in range(0, 200):
            node.append(Node())

        insertNode = Node()
        self.assertEqual(len(node.getNormalChilds()), 200)
        self.assertEqual(len(insertNode.getNormalChilds()), 0)
        node.insert(insertNode)
        self.assertEqual(len(node.getNormalChilds()), 1)
        self.assertEqual(len(insertNode.getNormalChilds()), 200)

    def testRemoveTraversed(self):
        parent = Node()
        gen1a = Node()
        gen1b = Node()
        gen1a1 = Node()
        gen1a2 = Node()

        gen1a.append(gen1a1)
        gen1a.append(gen1a2)
        parent.append(gen1a)
        parent.append(gen1b)

        self.assertEqual(len(parent.getAllChilds()), 2)
        self.assertEqual(len(gen1a.getAllChilds()), 2)
        self.assertEqual(len(gen1b.getAllChilds()), 0)

        # try to remove gen1a1 from parent directly
        parent.remove(gen1a1)
        self.assertEqual(len(parent.getAllChilds()), 2)
        self.assertEqual(len(gen1a.getAllChilds()), 2)
        self.assertIsNotNone(gen1a1._parent)
        self.assertEqual(len(gen1b.getAllChilds()), 0)

        # remove gen1a1 from parent (traversing through the hierarchy))
        parent.remove(gen1a1, traverse=True)
        self.assertEqual(len(parent.getAllChilds()), 2)
        self.assertEqual(len(gen1a.getAllChilds()), 1)
        self.assertIsNone(gen1a1._parent)
        self.assertEqual(len(gen1b.getAllChilds()), 0)

        # remove gen1a from parent
        parent.remove(gen1a)
        self.assertEqual(len(parent.getAllChilds()), 1)
        self.assertEqual(len(gen1a.getAllChilds()), 1)
        self.assertIsNone(gen1a._parent)
        self.assertEqual(len(gen1b.getAllChilds()), 0)

    def testRemoveVirtual(self):
        node = HelperNodeWithVirtualChilds(
            normal_childs=[Node() for _ in range(3)],
            virtual_childs=[Node() for _ in range(5)],
        )
        self.assertEqual(node.num_normal_nodes, 3)
        self.assertEqual(node.num_virtual_nodes, 5)
        self.assertEqual(node.num_all_nodes, 8)

        parent = Node()
        parent.append(node)

        for n in range(node.num_virtual_nodes):
            c = node.getVirtualChilds()[n]
            self.assertRaises(VirtualNodeError, Node.remove, node, c)
            self.assertRaises(VirtualNodeError, Node.remove, parent, c, traverse=True)
            self.assertEqual(node.num_all_nodes, 8)

        for c in node.allChildItems():
            parent.remove(c)
            self.assertEqual(node.num_all_nodes, 8)

        count = node.num_all_nodes
        for _ in range(node.num_all_nodes):
            parent.remove(node.getAllChilds()[0], traverse=True, virtual=True)
            count -= 1
            self.assertEqual(node.num_all_nodes, count)

    def testIter(self):
        node = HelperNodeWithVirtualChilds(
            normal_childs=[Node() for _ in range(3)],
            virtual_childs=[Node() for _ in range(5)],
        )
        self.assertEqual(node.num_normal_nodes, 3)
        self.assertEqual(node.num_virtual_nodes, 5)
        self.assertEqual(node.num_all_nodes, 8)

        count = 0
        for _ in node.normalChildItems():
            count += 1
        self.assertEqual(count, node.num_normal_nodes)

        count = 0
        for _ in node:
            count += 1
        self.assertEqual(count, node.num_all_nodes)
        self.assertEqual(len(node), node.num_all_nodes)

        count = 0
        for _ in node.virtualChildItems():
            count += 1
        self.assertEqual(count, node.num_virtual_nodes)

        count = 0
        for _ in node.allChildItems():
            count += 1
        self.assertEqual(count, node.num_all_nodes)
