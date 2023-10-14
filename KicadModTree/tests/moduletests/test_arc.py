import unittest
import math
from KicadModTree import *
from KicadModTree.util import geometric_util as geo

RESULT_kx90DEG = """(footprint test (version 20221018) (generator kicad-footprint-generator)
  (layer F.Cu)
  (attr smd)
  (fp_arc (start 1 0) (mid 0.707107 -0.707107) (end 0 -1)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 -1.2) (mid -0.848528 -0.848528) (end -1.2 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -1.4 0) (mid -0.989949 0.989949) (end 0 1.4)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 1.6) (mid 1.131371 1.131371) (end 1.6 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 2 0) (mid 1.414214 1.414214) (end 0 2)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 2.2) (mid -1.555635 1.555635) (end -2.2 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -2.4 0) (mid -1.697056 -1.697056) (end 0 -2.4)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 -2.6) (mid 1.838478 -1.838478) (end 2.6 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 3 0) (mid 2.12132 -2.12132) (end 0 -3)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 -3.2) (mid -2.262742 -2.262742) (end -3.2 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -3.4 0) (mid -2.404163 2.404163) (end 0 3.4)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 3.6) (mid 2.545584 2.545584) (end 3.6 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 4 0) (mid 2.828427 2.828427) (end 0 4)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 4.2) (mid -2.969848 2.969848) (end -4.2 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -4.4 0) (mid -3.11127 -3.11127) (end 0 -4.4)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 -4.6) (mid 3.252691 -3.252691) (end 4.6 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 5 0) (mid -3.535534 3.535534) (end 0 -5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 -5.2) (mid 3.676955 3.676955) (end -5.2 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5.4 0) (mid 3.818377 -3.818377) (end 0 5.4)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0 5.6) (mid -3.959798 -3.959798) (end 5.6 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 6 0) (mid 0 -6) (end -6 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -6.2 0) (mid 0 6.2) (end 6.2 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 6.6 0) (mid 0 6.6) (end -6.6 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -6.8 0) (mid 0 -6.8) (end 6.8 0)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 4.949747 -4.949747) (mid 7 0) (end 4.949747 4.949747)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5.091169 -5.091169) (mid 0 -7.2) (end 5.091169 -5.091169)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5.23259 5.23259) (mid -7.4 0) (end -5.23259 -5.23259)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 5.374012 5.374012) (mid 0 7.6) (end -5.374012 5.374012)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 5.656854 5.656854) (mid 8 0) (end 5.656854 -5.656854)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 5.798276 -5.798276) (mid 0 -8.2) (end -5.798276 -5.798276)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5.939697 -5.939697) (mid -8.4 0) (end -5.939697 5.939697)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -6.081118 6.081118) (mid 0 8.6) (end 6.081118 6.081118)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
)"""

RESULT_kx90DEG_45deg = """(footprint test (version 20221018) (generator kicad-footprint-generator)
  (layer F.Cu)
  (attr smd)
  (fp_arc (start -4.292893 5.707107) (mid -4 5) (end -4.292893 4.292893)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -4.151472 4.151472) (mid -5 3.8) (end -5.848528 4.151472)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5.989949 4.010051) (mid -6.4 5) (end -5.989949 5.989949)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -6.131371 6.131371) (mid -5 6.6) (end -3.868629 6.131371)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -3.585786 6.414214) (mid -5 7) (end -6.414214 6.414214)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -6.555635 6.555635) (mid -7.2 5) (end -6.555635 3.444365)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -6.697056 3.302944) (mid -5 2.6) (end -3.302944 3.302944)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -3.161522 3.161522) (mid -2.4 5) (end -3.161522 6.838478)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -2.87868 7.12132) (mid -2 5) (end -2.87868 2.87868)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -2.737258 2.737258) (mid -5 1.8) (end -7.262742 2.737258)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -7.404163 2.595837) (mid -8.4 5) (end -7.404163 7.404163)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -7.545584 7.545584) (mid -5 8.6) (end -2.454416 7.545584)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -2.171573 7.828427) (mid -5 9) (end -7.828427 7.828427)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -7.969848 7.969848) (mid -9.2 5) (end -7.969848 2.030152)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -8.11127 1.88873) (mid -5 0.6) (end -1.88873 1.88873)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -1.747309 1.747309) (mid -0.4 5) (end -1.747309 8.252691)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -1.464466 8.535534) (mid -10 5) (end -1.464466 1.464466)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -1.323045 1.323045) (mid -5 10.2) (end -8.676955 1.323045)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -8.818377 1.181623) (mid 0.4 5) (end -8.818377 8.818377)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -8.959798 8.959798) (mid -5 -0.6) (end -1.040202 8.959798)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -0.757359 9.242641) (mid -0.757359 0.757359) (end -9.242641 0.757359)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -9.384062 0.615938) (mid -9.384062 9.384062) (end -0.615938 9.384062)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -0.333095 9.666905) (mid -9.666905 9.666905) (end -9.666905 0.333095)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -9.808326 0.191674) (mid -0.191674 0.191674) (end -0.191674 9.808326)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 2 5) (mid -0.050253 9.949747) (end -5 12)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5 -2.2) (mid 0.091169 -0.091169) (end 2.2 5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -12.4 5) (mid -10.23259 -0.23259) (end -5 -2.4)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5 12.6) (mid -10.374012 10.374012) (end -12.6 5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5 13) (mid 0.656854 10.656854) (end 3 5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 3.2 5) (mid 0.798276 -0.798276) (end -5 -3.2)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -5 -3.4) (mid -10.939697 -0.939697) (end -13.4 5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -13.6 5) (mid -11.081118 11.081118) (end -5 13.6)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
)"""

RESULT_kx3Point = """(footprint test (version 20221018) (generator kicad-footprint-generator)
  (layer F.Cu)
  (attr smd)
  (fp_arc (start 0.707107 -0.707107) (mid 0 -1) (end -0.707107 -0.707107)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -1 0) (mid -0.707107 0.707107) (end 0 1)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 1 0) (mid 0.707107 0.707107) (end 0 1)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0.5 -0.5) (mid -0.5 -0.5) (end -0.5 0.5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start 0.5 -0.5) (mid -0.5 -0.5) (end -0.5 0.5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -2.5 -1.5) (mid -1.5 -0.5) (end -0.5 -1.5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -0.5 -1.5) (mid -1.5 -2.5) (end -2.5 -1.5)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -3.5 -1) (mid -3.5 -2) (end -4.5 -2)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
  (fp_arc (start -4.5 -2) (mid -4.5 -1) (end -3.5 -1)
    (stroke (width 0.12) (type solid)) (layer F.SilkS))
)"""


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

        file_handler = KicadFileHandler(kicad_mod)
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_kx90DEG)
        # file_handler.writeFile('test_arc4.kicad_mod')

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

        file_handler = KicadFileHandler(kicad_mod)
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_kx90DEG_45deg)
        # file_handler.writeFile('test_arc5.kicad_mod')

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

        file_handler = KicadFileHandler(kicad_mod)
        # file_handler.writeFile('test_3point.kicad_mod')
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_kx3Point)

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
