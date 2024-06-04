#!/usr/bin/env python

'''
kicad-footprint-generator is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

kicad-footprint-generator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
'''

import sys
import os
sys.path.append(os.path.join(sys.path[0],".."))
#sys.path.append('../..') # enable package import from parent directory

from KicadModTree import *

# adjust to create output in KiCad footprints path
footprints_path = './'
#footprints_path = 'path-to-your-footprints/Varistor.3dshapes/'

# Dimensions taken from https://www.tdk-electronics.tdk.com/inf/70/db/var/SIOV_Leaded_StandarD.pdf
#
# nom = nominal diameter (used in order code)
# e = pitch in horizontal direction (larger value)
# a = pitch in vertical direction (smaller value)
# w_max = maximum width / diameter
# th_max = maximum thickness
# d = wire diameter

def makeVaristor(nom, e, a, w_max, th_max, d):

    footprint_name = 'RV_Disc_D' + str(nom) + 'mm_P' + str(e) + 'mm_T' + str(th_max) + 'mm'

    # calculate some useful dimensions
    ddrill = d + 0.2
    left = -(w_max - e) / 2
    right = e + (w_max - e) / 2
    top = -th_max / 4
    bot = th_max * 3 / 4

    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription("Varistor, nominal diameter " + str(nom) + "mm, pitch " + str(e) + "mm, thickness " + str(th_max) + "mm" +
        "(https://www.tdk-electronics.tdk.com/inf/70/db/var/SIOV_Leaded_StandarD.pdf)")
    kicad_mod.setTags("varistor SIOV MOV")

    kicad_mod.append(Text(type='value', text=footprint_name, at=[e/2,top-1], layer='F.Fab'))
    kicad_mod.append(Text(type='user', text='%R', at=[e/2,th_max/4], layer='F.Fab'))
    kicad_mod.append(Text(type='reference', text='REF**', at=[e/2,bot+1], layer='F.SilkS'))

    kicad_mod.append(RectLine(start=[left,top], end=[right,bot], layer='F.SilkS', width=0.15))
    kicad_mod.append(RectLine(start=[left,top], end=[right,bot], layer='F.Fab', width=0.1))
    kicad_mod.append(RectLine(start=[left,top], end=[right,bot], layer='F.CrtYd', width=0.05, offset=0.25))

    kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, at=[0,0], size=[2*ddrill,2*ddrill], drill=ddrill, layers=['*.Cu', '*.Mask']))
    kicad_mod.append(Pad(number=2, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, at=[e,th_max/2], size=[2*ddrill,2*ddrill], drill=ddrill, layers=['*.Cu', '*.Mask']))

    kicad_mod.append(Model(filename="Varistor.3dshapes/" + footprint_name + ".wrl"
                          ,at=[0,0,0]
                          ,scale=[1,1,1]
                          ,rotate=[0,0,0]))

    #kicad_mod.set
    # output kicad model
    #print(kicad_mod)

    # print render tree
    #print(kicad_mod.getRenderTree())
    #print(kicad_mod.getCompleteRenderTree())

    # write file
    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(footprints_path + footprint_name + '.kicad_mod')


def makeVaristorSeries(nom, e, a_arr, w_max, th_max_arr, d):
    for i in range(0, len(th_max_arr)):
        makeVaristor(nom, e, a_arr[i], w_max, th_max_arr[i], d)

if __name__ == '__main__':

    # nominal diameter 5 (max. 7.0)
    th_max_arr = [3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.2, 4.3, 4.5, 4.8, 4.9, 5.1, 5.4, 5.5, 5.7]
    a_arr      = [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.5, 1.5, 1.6, 1.7, 1.9, 2.0, 2.1, 2.4, 2.4, 2.6]
    makeVaristorSeries(5, 5.0, a_arr, 7.0, th_max_arr, 0.6)

    # nominal diameter 7 (max. 9.0)
    th_max_arr = [3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.2, 4.3, 4.5, 4.8, 4.9, 5.1, 5.2, 5.4, 5.5, 5.7]
    a_arr      = [1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.5, 1.5, 1.6, 1.7, 1.9, 2.0, 2.1, 2.1, 2.4, 2.4, 2.6]
    makeVaristorSeries(7, 5.0, a_arr, 9.0, th_max_arr, 0.6)

    # nominal diameter 10 (max. 12.0)
    th_max_arr = [4.0, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 5.0, 5.1, 5.4, 5.6, 5.8, 6.1, 6.2, 6.3, 6.7, 7.1, 7.5, 7.9]
    a_arr      = [1.4, 1.6, 1.8, 2.0, 2.1, 2.2, 1.7, 1.8, 1.9, 2.1, 2.2, 2.4, 2.6, 2.7, 2.8, 3.1, 3.4, 3.7, 4.1]
    makeVaristorSeries(10, 7.5, a_arr, 12.0, th_max_arr, 0.8)

    # nominal diameter 14 (max 15.5)
    th_max_arr = [4.0, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 5.0, 5.2, 5.4, 5.6, 5.9, 6.1, 6.2, 6.3, 6.7, 7.2, 7.5, 8.0, 11.0]
    a_arr      = [1.4, 1.6, 1.8, 2.0, 2.1, 2.2, 1.7, 1.8, 1.9, 2.1, 2.2, 2.4, 2.6, 2.7, 2.8, 3.1, 3.4, 3.7, 4.1, 6.3]
    makeVaristorSeries(14, 7.5, a_arr, 15.5, th_max_arr, 0.8)

    # nominal diameter 20 (max 21.5)
    th_max_arr = [4.5, 4.6, 4.7, 4.8, 4.9, 5.0, 5.1, 5.3, 5.4, 5.6, 5.8, 6.0, 6.2, 6.3, 6.5, 6.7, 6.8, 7.1, 7.5, 7.9, 8.4, 11.4]
    a_arr      = [2.1, 1.9, 2.0, 2.1, 2.2, 2.3, 1.8, 1.9, 2.0, 2.1, 2.3, 2.4, 2.7, 2.5, 2.7, 2.8, 3.0, 3.2, 3.6, 3.9, 4.2, 6.4]
    makeVaristorSeries(20, 10.0, a_arr, 21.5, th_max_arr, 1.0)
