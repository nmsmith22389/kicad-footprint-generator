import unittest
from KicadModTree import *


def _dir_vec(line):
    return line.end_pos - line.start_pos


def _length(line):
    return _dir_vec(line).norm()


class IntersectionTests(unittest.TestCase):

    def testPolgonlineIntersections(self):

        rect1 = RectLine(start=[-2, -2], end=[2, 2], layer=None)
        rect2 = copy(rect1).rotate(45)

        # Rectangle-Rectangle
        lines = rect1.cut(rect2)
        circumfence = 0
        for line in lines:
            circumfence += (line.end_pos - line.start_pos).norm()
            self.assertTrue(rect1.isPointOnSelf(line.getMidPoint()))
            self.assertFalse(rect2.isPointOnSelf(line.getMidPoint()))
        self.assertAlmostEqual(circumfence, 16)
        self.assertEqual(len(lines), 12)

        # Rectangle-Circle
        circle = Circle(center=(0, 0), radius=2.5)
        lines = rect1.cut(circle)
        circumfence = 0
        for line in lines:
            circumfence += (line.end_pos - line.start_pos).norm()
            self.assertTrue(rect1.isPointOnSelf(line.getMidPoint()))
            self.assertFalse(circle.isPointOnSelf(line.getMidPoint()))
        self.assertAlmostEqual(circumfence, 16)
        self.assertEqual(len(lines), 12)

        # Circle-Rectangle
        arcs = circle.cut(rect1)
        angle = 0
        for arc in arcs:
            angle += arc.angle
            self.assertTrue(circle.isPointOnSelf(arc.getMidPoint()))
            self.assertFalse(rect1.isPointOnSelf(arc.getMidPoint()))
        self.assertAlmostEqual(angle, 360)
        self.assertEqual(len(arcs), 9)  # the arc including 0 deg is split into two
