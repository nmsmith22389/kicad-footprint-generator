import unittest
import math
from KicadModTree import *

# Trick pycodestyle into not assuming tab indents
if False:
    pass

RESULT_rotText = """(footprint "test_rotate_text"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(fp_text user "-1"
		(at 2 0 0)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(fp_text user "-1"
		(at 1.414214 1.414214 -45)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(fp_text user "-1"
		(at 0 2 -90)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(fp_text user "-1"
		(at -1.414214 1.414214 -135)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(fp_text user "-1"
		(at -2 0 -180)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(fp_text user "-1"
		(at -1.414214 -1.414214 -225)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(fp_text user "-1"
		(at 0 -2 -270)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(fp_text user "-1"
		(at 1.414214 -1.414214 -315)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
)"""  # NOQA: W191

RESULT_rotLine = """(footprint "test_rotate_line"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(fp_line
		(start 6 0)
		(end 7 1)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5.931852 0.517638)
		(end 6.638958 1.742383)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5.732051 1)
		(end 6.098076 2.366025)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5.414214 1.414214)
		(end 5.414214 2.828427)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5 1.732051)
		(end 4.633975 3.098076)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 4.517638 1.931852)
		(end 3.810531 3.156597)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 4 2)
		(end 3 3)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 3.482362 1.931852)
		(end 2.257617 2.638958)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 3 1.732051)
		(end 1.633975 2.098076)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 2.585786 1.414214)
		(end 1.171573 1.414214)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 2.267949 1)
		(end 0.901924 0.633975)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 2.068148 0.517638)
		(end 0.843403 -0.189469)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 2 0)
		(end 1 -1)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 2.068148 -0.517638)
		(end 1.361042 -1.742383)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 2.267949 -1)
		(end 1.901924 -2.366025)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 2.585786 -1.414214)
		(end 2.585786 -2.828427)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 3 -1.732051)
		(end 3.366025 -3.098076)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 3.482362 -1.931852)
		(end 4.189469 -3.156597)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 4 -2)
		(end 5 -3)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 4.517638 -1.931852)
		(end 5.742383 -2.638958)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5 -1.732051)
		(end 6.366025 -2.098076)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5.414214 -1.414214)
		(end 6.828427 -1.414214)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5.732051 -1)
		(end 7.098076 -0.633975)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5.931852 -0.517638)
		(end 7.156597 0.189469)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
)"""  # NOQA: W191

RESULT_rotArc = """(footprint "test_rotate_arc"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(fp_arc
		(start 5.741181 0.034074)
		(mid 6.5 0.133975)
		(end 6.965926 0.741181)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 5.673033 0.483564)
		(mid 6.380139 0.776457)
		(end 6.673033 1.483564)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 5.49087 0.9001)
		(mid 6.098076 1.366025)
		(end 6.197977 2.124844)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 5.207107 1.255295)
		(mid 5.673033 1.862501)
		(end 5.573132 2.62132)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 4.841081 1.524944)
		(mid 5.133975 2.232051)
		(end 4.841081 2.939158)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 4.417738 1.690671)
		(mid 4.517638 2.44949)
		(end 4.051712 3.056696)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 3.965926 1.741181)
		(mid 3.866025 2.5)
		(end 3.258819 2.965926)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 3.516436 1.673033)
		(mid 3.223543 2.380139)
		(end 2.516436 2.673033)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 3.0999 1.49087)
		(mid 2.633975 2.098076)
		(end 1.875156 2.197977)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 2.744705 1.207107)
		(mid 2.137499 1.673033)
		(end 1.37868 1.573132)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 2.475056 0.841081)
		(mid 1.767949 1.133975)
		(end 1.060842 0.841081)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 2.309329 0.417738)
		(mid 1.55051 0.517638)
		(end 0.943304 0.051712)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 2.258819 -0.034074)
		(mid 1.5 -0.133975)
		(end 1.034074 -0.741181)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 2.326967 -0.483564)
		(mid 1.619861 -0.776457)
		(end 1.326967 -1.483564)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 2.50913 -0.9001)
		(mid 1.901924 -1.366025)
		(end 1.802023 -2.124844)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 2.792893 -1.255295)
		(mid 2.326967 -1.862501)
		(end 2.426868 -2.62132)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 3.158919 -1.524944)
		(mid 2.866025 -2.232051)
		(end 3.158919 -2.939158)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 3.582262 -1.690671)
		(mid 3.482362 -2.44949)
		(end 3.948288 -3.056696)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 4.034074 -1.741181)
		(mid 4.133975 -2.5)
		(end 4.741181 -2.965926)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 4.483564 -1.673033)
		(mid 4.776457 -2.380139)
		(end 5.483564 -2.673033)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 4.9001 -1.49087)
		(mid 5.366025 -2.098076)
		(end 6.124844 -2.197977)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 5.255295 -1.207107)
		(mid 5.862501 -1.673033)
		(end 6.62132 -1.573132)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 5.524944 -0.841081)
		(mid 6.232051 -1.133975)
		(end 6.939158 -0.841081)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_arc
		(start 5.690671 -0.417738)
		(mid 6.44949 -0.517638)
		(end 7.056696 -0.051712)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
)"""  # NOQA: W191

RESULT_rotCircle = """(footprint "test_rotate_circle"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(fp_circle
		(center 6 -1)
		(end 7 -1)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 5.673033 -0.516436)
		(end 6.673033 -0.516436)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 5.232051 -0.133975)
		(end 6.232051 -0.133975)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 4.707107 0.12132)
		(end 5.707107 0.12132)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 4.133975 0.232051)
		(end 5.133975 0.232051)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 3.551712 0.190671)
		(end 4.551712 0.190671)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 3 0)
		(end 4 0)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 2.516436 -0.326967)
		(end 3.516436 -0.326967)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 2.133975 -0.767949)
		(end 3.133975 -0.767949)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 1.87868 -1.292893)
		(end 2.87868 -1.292893)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 1.767949 -1.866025)
		(end 2.767949 -1.866025)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 1.809329 -2.448288)
		(end 2.809329 -2.448288)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 2 -3)
		(end 3 -3)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 2.326967 -3.483564)
		(end 3.326967 -3.483564)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 2.767949 -3.866025)
		(end 3.767949 -3.866025)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 3.292893 -4.12132)
		(end 4.292893 -4.12132)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 3.866025 -4.232051)
		(end 4.866025 -4.232051)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 4.448288 -4.190671)
		(end 5.448288 -4.190671)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 5 -4)
		(end 6 -4)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 5.483564 -3.673033)
		(end 6.483564 -3.673033)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 5.866025 -3.232051)
		(end 6.866025 -3.232051)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 6.12132 -2.707107)
		(end 7.12132 -2.707107)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 6.232051 -2.133975)
		(end 7.232051 -2.133975)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 6.190671 -1.551712)
		(end 7.190671 -1.551712)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
)"""  # NOQA: W191

RESULT_rotPoly = """(footprint "test_rotate_polygon"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(fp_poly
		(pts
			(xy -1 0)
			(xy -1.2 0.5)
			(xy 0 0)
			(xy -1.2 -0.5)
		)
		(stroke
			(width 0.12)
			(type solid)
		)
		(fill solid)
		(layer "F.SilkS")
	)
	(fp_poly
		(pts
			(xy -0.575833 -3.334679)
			(xy -1.108846 -3.257884)
			(xy -0.075833 -2.468653)
			(xy -0.24282 -3.757884)
		)
		(stroke
			(width 0.12)
			(type solid)
		)
		(fill solid)
		(layer "F.SilkS")
	)
	(fp_poly
		(pts
			(xy 2.524167 -4.634679)
			(xy 2.191154 -5.057884)
			(xy 2.024167 -3.768653)
			(xy 3.05718 -4.557884)
		)
		(stroke
			(width 0.12)
			(type solid)
		)
		(fill solid)
		(layer "F.SilkS")
	)
	(fp_poly
		(pts
			(xy 5.2 -2.6)
			(xy 5.4 -3.1)
			(xy 4.2 -2.6)
			(xy 5.4 -2.1)
		)
		(stroke
			(width 0.12)
			(type solid)
		)
		(fill solid)
		(layer "F.SilkS")
	)
	(fp_poly
		(pts
			(xy 4.775833 0.734679)
			(xy 5.308846 0.657884)
			(xy 4.275833 -0.131347)
			(xy 4.44282 1.157884)
		)
		(stroke
			(width 0.12)
			(type solid)
		)
		(fill solid)
		(layer "F.SilkS")
	)
	(fp_poly
		(pts
			(xy 1.675833 2.034679)
			(xy 2.008846 2.457884)
			(xy 2.175833 1.168653)
			(xy 1.14282 1.957884)
		)
		(stroke
			(width 0.12)
			(type solid)
		)
		(fill solid)
		(layer "F.SilkS")
	)
)"""  # NOQA: W191

RESULT_rotPad = """(footprint "test_rotate_pad"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(pad "1" smd custom
		(at 0 0)
		(size 0.2 0.2)
		(layers "F.Cu" "F.Paste" "F.Mask")
		(options
			(clearance outline)
			(anchor circle)
		)
		(primitives
			(gr_poly
				(pts
					(xy -1 0)
					(xy -1.2 0.5)
					(xy 0 0)
					(xy -1.2 -0.5)
				)
				(width 0)
			)
		)
	)
	(pad "2" smd custom
		(at 0.175 -0.303109 -60)
		(size 0.2 0.2)
		(layers "F.Cu" "F.Paste" "F.Mask")
		(options
			(clearance outline)
			(anchor circle)
		)
		(primitives
			(gr_poly
				(pts
					(xy -1 0)
					(xy -1.2 0.5)
					(xy 0 0)
					(xy -1.2 -0.5)
				)
				(width 0)
			)
		)
	)
	(pad "3" smd custom
		(at 0.525 -0.303109 -120)
		(size 0.2 0.2)
		(layers "F.Cu" "F.Paste" "F.Mask")
		(options
			(clearance outline)
			(anchor circle)
		)
		(primitives
			(gr_poly
				(pts
					(xy -1 0)
					(xy -1.2 0.5)
					(xy 0 0)
					(xy -1.2 -0.5)
				)
				(width 0)
			)
		)
	)
	(pad "4" smd custom
		(at 0.7 0 -180)
		(size 0.2 0.2)
		(layers "F.Cu" "F.Paste" "F.Mask")
		(options
			(clearance outline)
			(anchor circle)
		)
		(primitives
			(gr_poly
				(pts
					(xy -1 0)
					(xy -1.2 0.5)
					(xy 0 0)
					(xy -1.2 -0.5)
				)
				(width 0)
			)
		)
	)
	(pad "5" smd custom
		(at 0.525 0.303109 -240)
		(size 0.2 0.2)
		(layers "F.Cu" "F.Paste" "F.Mask")
		(options
			(clearance outline)
			(anchor circle)
		)
		(primitives
			(gr_poly
				(pts
					(xy -1 0)
					(xy -1.2 0.5)
					(xy 0 0)
					(xy -1.2 -0.5)
				)
				(width 0)
			)
		)
	)
)"""  # NOQA: W191


class RotationTests(unittest.TestCase):

    def testTextRotation(self):
        kicad_mod = Footprint("test_rotate_text", FootprintType.SMD)

        center = Vector2D(0, 0)
        at = center+Vector2D(2, 0)

        for t in range(0, 360, 45):
            kicad_mod.append(
                Text(text="-1", at=at).rotate(t, origin=center))

        file_handler = KicadFileHandler(kicad_mod)
        # file_handler.writeFile('test_rotate_text.kicad_mod')
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_rotText)

    def testLineRotation(self):
        kicad_mod = Footprint("test_rotate_line", FootprintType.SMD)

        center = Vector2D(4, 0)
        start = center + Vector2D(2, 0)
        end = start + Vector2D(1, 1)

        for t in range(0, 360, 15):
            kicad_mod.append(
                Line(start=start, end=end).rotate(t, origin=center))

        file_handler = KicadFileHandler(kicad_mod)
        # file_handler.writeFile('test_rotate_line.kicad_mod')
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_rotLine)

    def testArcRotation(self):
        kicad_mod = Footprint("test_rotate_arc", FootprintType.SMD)

        rot_center = Vector2D(4, 0)
        mid = rot_center + Vector2D(2, 0)
        center = rot_center + Vector2D(2, 1)
        angle = 90

        for t in range(0, 360, 15):
            kicad_mod.append(
                Arc(center=center, midpoint=mid, angle=angle)
                .rotate(angle/3, origin=center)
                .rotate(t, origin=rot_center))

        file_handler = KicadFileHandler(kicad_mod)
        # file_handler.writeFile('test_rotate_arc.kicad_mod')
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_rotArc)

    def testCircleRotation(self):
        kicad_mod = Footprint("test_rotate_circle", FootprintType.SMD)

        rot_center = Vector2D(4, -2)
        center = rot_center + Vector2D(2, 1)
        radius = 1

        for t in range(0, 360, 15):
            kicad_mod.append(
                Circle(center=center, radius=radius).rotate(t, origin=rot_center))

        file_handler = KicadFileHandler(kicad_mod)
        # file_handler.writeFile('test_rotate_circle.kicad_mod')
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_rotCircle)

    def testPolygonRotation(self):
        kicad_mod = Footprint("test_rotate_polygon", FootprintType.SMD)

        rot_center = Vector2D(2.1, -1.3)

        nodes = [(-1, 0), (-1.2, 0.5), (0, 0), (-1.2, -0.5)]

        for t in range(0, 360, 60):
            kicad_mod.append(
                Polygon(nodes=nodes).rotate(t, origin=rot_center))

        file_handler = KicadFileHandler(kicad_mod)
        # file_handler.writeFile('test_rotate_polygon.kicad_mod')
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_rotPoly)

    def testPadRotation(self):
        kicad_mod = Footprint("test_rotate_pad", FootprintType.SMD)

        rot_center = Vector2D(0.35, 0)
        nodes = [(-1, 0), (-1.2, 0.5), (0, 0), (-1.2, -0.5)]
        prim = Polygon(nodes=nodes)
        i = 1
        for t in range(0, 300, 60):
            kicad_mod.append(
                Pad(
                    number=i, type=Pad.TYPE_SMT, shape=Pad.SHAPE_CUSTOM,
                    at=[0, 0], size=[0.2, 0.2], layers=Pad.LAYERS_SMT,
                    primitives=[prim]
                    ).rotate(t, origin=rot_center))
            i += 1

        file_handler = KicadFileHandler(kicad_mod)
        # file_handler.writeFile('test_rotate_pad.kicad_mod')
        self.assertEqual(file_handler.serialize(timestamp=0), RESULT_rotPad)
