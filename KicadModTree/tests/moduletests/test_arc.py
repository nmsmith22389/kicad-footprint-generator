import unittest
import math
from KicadModTree import *
from KicadModTree.util import geometric_util as geo

from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest


class ArcTests(unittest.TestCase):

    def testArcGeometry(self):

        def assert_vectors_approx(v1: Vector2D, v2: Vector2D):
            """
            Assert that two vectors are almost equal
            """
            self.assertAlmostEqual(v1.x, v2.x)
            self.assertAlmostEqual(v1.y, v2.y)

        def vector_from_tuple(v):
            """
            Convert a tuple to a Vector2D if needed
            """
            if isinstance(v, tuple) or isinstance(v, list):
                return Vector2D(v[0], v[1])
            return v

        def assert_arc_geom(
            arc: geo.geometricArc, start, end, center, midpoint, radius: float
        ) -> None:
            """
            Assert that the arc has the given geometry
            """
            assert_vectors_approx(arc.getStartPoint(), vector_from_tuple(start))
            assert_vectors_approx(arc.getEndPoint(), vector_from_tuple(end))
            assert_vectors_approx(arc.getCenter(), vector_from_tuple(center))
            assert_vectors_approx(arc.getMidPoint(), vector_from_tuple(midpoint))
            self.assertAlmostEqual(arc.getRadius(), radius)

        sqrt2_2 = math.sqrt(2) / 2

        # A semi-circular arc
        semicircle = geo.geometricArc(
            center=Vector2D(0, 0), start=Vector2D(1, 0), angle=180
        )

        assert_arc_geom(
            arc=semicircle,
            start=(1, 0),
            end=(-1, 0),
            center=(0, 0),
            midpoint=(0, 1),
            radius=1,
        )

        # A semi-circular arc by endpoint goes in a specific direction
        semicircle_by_endpoint = geo.geometricArc(
            center=Vector2D(0, 0), start=Vector2D(1, 0), end=Vector2D(-1, 0)
        )

        assert_arc_geom(
            arc=semicircle_by_endpoint,
            start=(1, 0),
            end=(-1, 0),
            center=(0, 0),
            midpoint=(0, -1),
            radius=1,
        )

        # Check that end or angle is required
        with self.assertRaises(KeyError):
            geo.geometricArc(center=Vector2D(0, 0), start=Vector2D(1, 0))

        # Test that the negative angle goes the other way
        negative_semicircle = geo.geometricArc(
            center=Vector2D(0, 0), start=Vector2D(1, 0), angle=-180
        )

        assert_arc_geom(
            arc=negative_semicircle,
            start=(1, 0),
            end=(-1, 0),
            center=(0, 0),
            midpoint=(0, -1),
            radius=1,
        )

        arc_90deg_down = geo.geometricArc(
            center=Vector2D(0, 0), start=Vector2D(1, 0), angle=-90
        )

        assert_arc_geom(
            arc=arc_90deg_down,
            start=(1, 0),
            end=(0, -1),
            center=(0, 0),
            midpoint=(sqrt2_2, -sqrt2_2),
            radius=1,
        )

        arc_90deg_down_nonunity_radius = geo.geometricArc(
            center=Vector2D(0, 0), start=Vector2D(0, -1.2), angle=-90
        )

        assert_arc_geom(
            arc=arc_90deg_down_nonunity_radius,
            start=(0, -1.2),
            end=(-1.2, 0),
            center=(0, 0),
            midpoint=1.2 * Vector2D(-sqrt2_2, -sqrt2_2),
            radius=1.2,
        )

        # Arc not centred on the origin
        arc_not_on_origin = geo.geometricArc(
            center=Vector2D(1, 1), start=Vector2D(2, 1), angle=-90
        )

        assert_arc_geom(
            arc=arc_not_on_origin,
            start=(2, 1),
            end=(1, 0),
            center=(1, 1),
            midpoint=(1 + sqrt2_2, 1 - sqrt2_2),
            radius=1
        )

        # Not a simple angle for the midpoint
        arc_45_deg = geo.geometricArc(center=Vector2D(0, 0), start=Vector2D(1, 0), angle=45)

        assert_arc_geom(
            arc=arc_45_deg,
            start=(1, 0),
            end=(sqrt2_2, sqrt2_2),
            center=(0, 0),
            midpoint=(math.cos(math.radians(22.5)), math.sin(math.radians(22.5))),
            radius=1,
        )

        # Degenerate radius
        a_zero_radius = geo.geometricArc(
            center=Vector2D(0, 0), start=Vector2D(0, 0), angle=42
        )

        assert_arc_geom(
            arc=a_zero_radius,
            start=(0, 0),
            end=(0, 0),
            center=(0, 0),
            midpoint=(0, 0),
            radius=0,
        )

    def testCircleCircleIntersection(self):
        # check intersection of two circles with identical radii
        c1 = geo.geometricCircle(center=[0, 0], radius=math.sqrt(2))
        c2 = geo.geometricCircle(center=[2, 0], radius=math.sqrt(2))
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 2)
        for p in ip:
            self.assertTrue(any((p - Vector2D(1, y)).is_nullvec(tol=1e-7) for y in [1, -1]))

        # check intersection of two circles with different radii
        c1 = geo.geometricCircle(center=[0, 0], radius=2)
        c2 = geo.geometricCircle(center=[2 * math.sqrt(3/4), 0], radius=1)
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 2)
        for p in ip:
            self.assertTrue(any((p - Vector2D(2 * math.sqrt(3/4), y)).is_nullvec(tol=1e-7) for y in [1, -1]))

        # check intersection of two circles with different radii, too far apart
        c1 = geo.geometricCircle(center=[0, 0], radius=2)
        c2 = geo.geometricCircle(center=[4, 0], radius=1)
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 0)

        # check intersection of two circles with different radii, contained in each other
        c1 = geo.geometricCircle(center=[0, 0], radius=2)
        c2 = geo.geometricCircle(center=[0.5, 0], radius=1)
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 0)

        # check intersection point of circles touching outside
        c1 = geo.geometricCircle(center=[0, 0], radius=1)
        c2 = geo.geometricCircle(center=[2, 0], radius=1)
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 1)
        self.assertTrue((ip[0] - Vector2D(1, 0)).is_nullvec(tol=1e-7))

        # check intersection point of circles touching inside
        c1 = geo.geometricCircle(center=[0, 0], radius=2)
        c2 = geo.geometricCircle(center=[1, 0], radius=1)
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 1)
        self.assertTrue((ip[0] - Vector2D(2, 0)).is_nullvec(tol=1e-7))

        # vary position on x and y axis
        c1 = geo.geometricCircle(center=[0, 0], radius=math.sqrt(2))
        c2 = geo.geometricCircle(center=[0, 2], radius=math.sqrt(2))
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 2)
        for p in ip:
            self.assertTrue(any((p - Vector2D(x, 1)).is_nullvec(tol=1e-7) for x in [1, -1]))
        c2 = geo.geometricCircle(center=[-2, 0], radius=math.sqrt(2))
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 2)
        for p in ip:
            self.assertTrue(any((p - Vector2D(-1, y)).is_nullvec(tol=1e-7) for y in [1, -1]))
        c2 = geo.geometricCircle(center=[0, -2], radius=math.sqrt(2))
        for p in geo.BaseNodeIntersection.intersectTwoNodes(c1, c2):
            self.assertTrue(any((p - Vector2D(x, -1)).is_nullvec(tol=1e-7) for x in [1, -1]))

        # circle 2 on the first median
        c1 = geo.geometricCircle(center=[0, 0], radius=1)
        c2 = geo.geometricCircle(center=[1, 1], radius=1)
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 2)
        for p in ip:
            self.assertTrue(any((p - Vector2D(x, y)).is_nullvec(tol=1e-7) for x, y in [(1, 0), (0, 1)]))

        # circle 2 on the fourth median
        c1 = geo.geometricCircle(center=[0, 0], radius=1)
        c2 = geo.geometricCircle(center=[1, -1], radius=1)
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 2)
        for p in ip:
            self.assertTrue(any((p - Vector2D(x, y)).is_nullvec(tol=1e-7) for x, y in [(1, 0), (0, -1)]))

        # circles on arbitrary positions
        center = Vector2D(3, -2)
        for angle in [0, 30, -30, 180, -180, 72, 143]:
            offset = Vector2D(sin(radians(angle)), cos(radians(angle)))
            c1 = geo.geometricCircle(center=center, radius=math.sqrt(2))
            c2 = geo.geometricCircle(center=center + 2 * offset, radius=math.sqrt(2))
            ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
            self.assertEqual(len(ip), 2)
            for p in ip:
                self.assertTrue(any(
                    (p - (center + offset + s * copy(offset).rotate(90))).is_nullvec(tol=1e-7)
                    for s in [-1, 1]))

        # two degenerated circles with the same center
        center = Vector2D(3, -2)
        c1 = geo.geometricCircle(center=center, radius=0)
        c2 = geo.geometricCircle(center=center, radius=0)
        ip = geo.BaseNodeIntersection.intersectTwoNodes(c1, c2)
        self.assertEqual(len(ip), 1)
        self.assertTrue((ip[0] - center).is_nullvec(tol=1e-7))

        # two identical circles with the same center
        center = Vector2D(3, -2)
        c1 = geo.geometricCircle(center=center, radius=1)
        c2 = geo.geometricCircle(center=center, radius=1)
        self.assertRaises(ValueError, geo.BaseNodeIntersection.intersectTwoNodes, c1, c2)


class ArcSerialisation(SerialisationTest):

    def setUp(self):
        super().setUp(__file__, 'results')

    def testArcsKx90deg(self):
        """
        Test that the Arc type can be serialised to KiCad format,
        looking at the 90 degree arcs.

        This is mostly a test of the serialisation, not the geometry, since
        while the geometry is tested above, the actual validity of the
        values in the output is not rigourously checked.
        """
        kicad_mod = Footprint("test", FootprintType.SMD)

        center = Vector2D(0, 0)
        kicad_mod.append(
            Arc(center=center, start=Vector2D(1, 0), angle=-90))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -1.2), angle=-90))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-1.4, 0), angle=-90))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 1.6), angle=-90))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(2, 0), angle=90))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 2.2), angle=90))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-2.4, 0), angle=90))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -2.6), angle=90))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(3, 0), end=Vector2D(0, -3)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -3.2), end=Vector2D(-3.2, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-3.4, 0), end=Vector2D(0, 3.4)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 3.6), end=Vector2D(3.6, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(4, 0), end=Vector2D(0, 4)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 4.2), end=Vector2D(-4.2, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-4.4, 0), end=Vector2D(0, -4.4)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -4.6), end=Vector2D(4.6, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(5, 0), end=Vector2D(0, -5),
                long_way=True))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, -5.2), end=Vector2D(-5.2, 0),
                long_way=True))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(-5.4, 0), end=Vector2D(0, 5.4),
                long_way=True))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(0, 5.6), end=Vector2D(5.6, 0),
                long_way=True))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(6, 0), end=Vector2D(-6, 0)))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(-6.2, 0), end=Vector2D(6.2, 0)))

        kicad_mod.append(
            Arc(center=center, start=Vector2D(6.6, 0), end=Vector2D(-6.6, 0),
                long_way=True))
        kicad_mod.append(
            Arc(center=center, start=Vector2D(-6.8, 0), end=Vector2D(6.8, 0),
                long_way=True))

        kicad_mod.append(
            Arc(center=center, midpoint=Vector2D(7, 0), angle=90))
        kicad_mod.append(
            Arc(center=center, midpoint=Vector2D(0, -7.2), angle=90))
        kicad_mod.append(
            Arc(center=center, midpoint=Vector2D(-7.4, 0), angle=90))
        kicad_mod.append(
            Arc(center=center, midpoint=Vector2D(0, 7.6), angle=90))

        kicad_mod.append(
            Arc(center=center, midpoint=Vector2D(8, 0), angle=-90))
        kicad_mod.append(
            Arc(center=center, midpoint=Vector2D(0, -8.2), angle=-90))
        kicad_mod.append(
            Arc(center=center, midpoint=Vector2D(-8.4, 0), angle=-90))
        kicad_mod.append(
            Arc(center=center, midpoint=Vector2D(0, 8.6), angle=-90))

        self.assert_serialises_as(kicad_mod, 'arc_90deg.kicad_mod')

    def testArcsKx90degOffsetRotated(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        center = Vector2D(-5, 5)
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(1, 0)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -1.2)+center).rotate(45, origin=center),
                angle=-90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-1.4, 0)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 1.6)+center).rotate(45, origin=center),
                angle=-90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(2, 0)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 2.2)+center).rotate(45, origin=center),
                angle=90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-2.4, 0)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -2.6)+center).rotate(45, origin=center),
                angle=90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(3, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, -3)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -3.2)+center).rotate(45, origin=center),
                end=(Vector2D(-3.2, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-3.4, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, 3.4)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 3.6)+center).rotate(45, origin=center),
                end=(Vector2D(3.6, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(4, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, 4)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 4.2)+center).rotate(45, origin=center),
                end=(Vector2D(-4.2, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-4.4, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, -4.4)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -4.6)+center).rotate(45, origin=center),
                end=(Vector2D(4.6, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(5, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, -5)+center).rotate(45, origin=center),
                long_way=True
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, -5.2)+center).rotate(45, origin=center),
                end=(Vector2D(-5.2, 0)+center).rotate(45, origin=center),
                long_way=True
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-5.4, 0)+center).rotate(45, origin=center),
                end=(Vector2D(0, 5.4)+center).rotate(45, origin=center),
                long_way=True
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(0, 5.6)+center).rotate(45, origin=center),
                end=(Vector2D(5.6, 0)+center).rotate(45, origin=center),
                long_way=True
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(6, 0)+center).rotate(45, origin=center),
                end=(Vector2D(-6, 0)+center).rotate(45, origin=center)
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-6.2, 0)+center).rotate(45, origin=center),
                end=(Vector2D(6.2, 0)+center).rotate(45, origin=center)
            ))

        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(6.6, 0)+center).rotate(45, origin=center),
                end=(Vector2D(-6.6, 0)+center).rotate(45, origin=center),
                long_way=True
            ))
        kicad_mod.append(
            Arc(
                center=center,
                start=(Vector2D(-6.8, 0)+center).rotate(45, origin=center),
                end=(Vector2D(6.8, 0)+center).rotate(45, origin=center),
                long_way=True
            ))

        kicad_mod.append(
            Arc(
                center=center,
                midpoint=(Vector2D(7, 0)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                midpoint=(Vector2D(0, -7.2)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                midpoint=(Vector2D(-7.4, 0)+center).rotate(45, origin=center),
                angle=90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                midpoint=(Vector2D(0, 7.6)+center).rotate(45, origin=center),
                angle=90
            ))

        kicad_mod.append(
            Arc(
                center=center,
                midpoint=(Vector2D(8, 0)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                midpoint=(Vector2D(0, -8.2)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                midpoint=(Vector2D(-8.4, 0)+center).rotate(45, origin=center),
                angle=-90
            ))
        kicad_mod.append(
            Arc(
                center=center,
                midpoint=(Vector2D(0, 8.6)+center).rotate(45, origin=center),
                angle=-90
            ))

        self.assert_serialises_as(kicad_mod, 'arc_90deg_45deg.kicad_mod')

    def testArcsKx3Point(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        root2div2 = (2 ** 0.5) / 2

        kicad_mod.append(
            Arc(
                start=(root2div2, -root2div2),
                midpoint=(0, -1),
                end=(-root2div2, -root2div2),
            )
        )

        kicad_mod.append(
            Arc(
                start=(-1, 0),
                midpoint=(-root2div2, root2div2),
                end=(0, 1),
            )
        )

        kicad_mod.append(
            Arc(
                start=(1, 0),
                midpoint=(root2div2, root2div2),
                end=(0, 1),
            )
        )

        kicad_mod.append(
            Arc(
                start=(-0.5, 0.5),
                midpoint=(-0.5, -0.5),
                end=(0.5, -0.5),
            )
        )

        kicad_mod.append(
            Arc(
                start=(0.5, -0.5),
                midpoint=(-0.5, -0.5),
                end=(-0.5, 0.5),
            )
        )

        kicad_mod.append(
            Arc(
                start=(-2.5, -1.5),
                midpoint=(-1.5, -2.5),
                end=(-0.5, -1.5),
            )
        )

        kicad_mod.append(
            Arc(
                start=(-0.5, -1.5),
                midpoint=(-1.5, -0.5),
                end=(-2.5, -1.5),
            )
        )

        kicad_mod.append(
            Arc(
                start=(-3.5, -1),
                midpoint=(-4.5, -1),
                end=(-4.5, -2),
            )
        )

        kicad_mod.append(
            Arc(
                start=(-4.5, -2),
                midpoint=(-3.5, -2),
                end=(-3.5, -1),
            )
        )

        self.assert_serialises_as(kicad_mod, 'arc_3point.kicad_mod')
