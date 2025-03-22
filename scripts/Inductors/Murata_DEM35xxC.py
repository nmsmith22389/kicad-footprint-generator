#!/usr/bin/env python3

from KicadModTree import *
from scripts.tools.global_config_files import global_config as GC
global_config = GC.DefaultGlobalConfig()

datasheet = "https://www.murata.com/~/media/webrenewal/products/inductor/chip/tokoproducts/wirewoundferritetypeforpl/m_dem3518c.ashx"
footprint_name = "L_Murata_DEM35xxC"
lib_name = "Inductor_SMD"

pkgWidth = 3.9
pkgHeight = 3.7
padXSpacing = 3.3
padWidth = 1
padHeight = 1.4

f = Footprint(footprint_name, FootprintType.SMD)
f.setDescription(datasheet)
f.setTags("Inductor SMD DEM35xxC")
f.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix,
               at=[0.0, 0.0, 0.0],
               scale=[1.0, 1.0, 1.0],
               rotate=[0.0, 0.0, 0.0]))

padSize = [padWidth, padHeight]
textSize = [1.0, 1.0]
fabRefTextSize = [0.7, 0.7]

thickness1 = 0.1
thickness2 = 0.15

wCrtYd = 0.05
wFab = 0.1
wSilkS = 0.12
crtYd = 0.25
silkClearance = 0.2

xCenter = 0.0
xPadRight = padXSpacing / 2
xFabRight = pkgWidth / 2
xSilkRight = xPadRight
xRightCrtYd = max(xPadRight + padWidth / 2, xFabRight) + crtYd

xLeftCrtYd = - xRightCrtYd
xPadLeft = -xPadRight
xFabLeft = -xFabRight
xSilkTopLeft = -xSilkRight
xSilkBottomLeft = -xSilkRight

yCenter = 0.0
yFabBottom = pkgHeight / 2
ySilkBottom = yFabBottom + silkClearance
yBottomCrtYd = yFabBottom + crtYd

yTopCrtYd = -yBottomCrtYd
ySilkTop = -ySilkBottom
yFabTop = -yFabBottom

yValue = yFabBottom + 1.25
yRef = yFabTop - 1.25

f.append(Property(name=Property.REFERENCE, text="REF**", at=[xCenter, yRef],
              layer="F.SilkS", size=textSize, thickness=thickness2))
f.append(Property(name=Property.VALUE, text=footprint_name, at=[xCenter, yValue],
              layer="F.Fab", size=textSize, thickness=thickness2))
f.append(Text(text='${REFERENCE}', at=[xCenter, yCenter],
              layer="F.Fab", size=fabRefTextSize, thickness=thickness1))

f.append(RectLine(start=[xLeftCrtYd, yTopCrtYd],
                  end=[xRightCrtYd, yBottomCrtYd],
                  layer="F.CrtYd", width=wCrtYd))

f.append(PolygonLine(polygon=[[xFabLeft, yFabTop],
                               [xFabRight, yFabTop],
                               [xFabRight, yFabBottom],
                               [xFabLeft, yFabBottom],
                               [xFabLeft, yFabTop]],
                     layer="F.Fab", width=wFab))

f.append(Line(start=[xSilkTopLeft, ySilkTop],
              end=[xSilkRight, ySilkTop],
              layer="F.SilkS", width=wSilkS))
f.append(Line(start=[xSilkBottomLeft, ySilkBottom],
              end=[xSilkRight, ySilkBottom],
              layer="F.SilkS", width=wSilkS))

padShape = Pad.SHAPE_ROUNDRECT
radius_handler  = RoundRadiusHandler(
    radius_ratio=0.2,
)

f.append(Pad(number=1, type=Pad.TYPE_SMT, shape=padShape,
             at=[xPadLeft, yCenter], size=padSize, layers=Pad.LAYERS_SMT,
             round_radius_handler=radius_handler))
f.append(Pad(number=2, type=Pad.TYPE_SMT, shape=padShape,
             at=[xPadRight, yCenter], size=padSize, layers=Pad.LAYERS_SMT,
             round_radius_handler=radius_handler))

lib = KicadPrettyLibrary(lib_name, None)
lib.save(f)
