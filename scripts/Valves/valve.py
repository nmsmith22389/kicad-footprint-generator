#!/usr/bin/env python3

import math
import os
import sys

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", ".."))

from KicadModTree import *
        
        
def create_sadle(f, origo_x, origo_y, sadle, sadle_hole, sadle_pcb_hole, nlayer, wLayer):

    #
    # sadle = [6.6, 35.5, 26.5, 14.25, 13.2, 72],        # sadle z pos, length, width, xpos r2, diameter r2, rotation
    #
    sadle_z = sadle[0]
    sadle_w = sadle[1]
    sadle_r1 = sadle[2] / 2.0
    sadle_x = sadle[3]
    sadle_r2 = sadle[4] / 2.0
    sadle_a = sadle[5]
    sadle_h = 0.2
    #
    # Dummy
#    f.append(Circle(center=(round(origo_x, 2), round(origo_y, 2)), radius=round(sadle_r1, 2), layer=nlayer, width=wLayer))
    #
#    f.append(Circle(center=(round(origo_x + sadle_x, 2), round(origo_y, 2)), radius=round(sadle_r2, 2), layer=nlayer, width=wLayer))
    #
#    f.append(Circle(center=(round(origo_x - sadle_x, 2), round(origo_y, 2)), radius=round(sadle_r2, 2), layer=nlayer, width=wLayer))
    #
    # https://en.wikipedia.org/wiki/Tangent_lines_to_circles
    #
    x1 = 0.0 - sadle_x;
    y1 = 0.0
    r = sadle_r2
    x2 = 0.0
    y2 = 0.0
    R = sadle_r1
    #
    theta = 0 - math.atan((y2 - y1) / (x2 - x1))
    beta = math.asin((R - r) / (math.sqrt(((x2 - x1)**2) + ((y2 - y1)**2))))
    alpha = theta - beta
    x3 = x1 + r * math.cos((math.pi / 2.0) - alpha)
    y3 = y1 + r * math.sin((math.pi / 2.0) - alpha)
    x4 = x2 + R * math.cos((math.pi / 2.0) - alpha)
    y4 = y2 + R * math.sin((math.pi / 2.0) - alpha)
  
    #
    th = math.sqrt((((0.0 - sadle_x) - x3)**2) + ((0.0 - y3)**2))
    aa = math.fabs(math.degrees(math.acos((x3 - (0.0 - sadle_x)) / th))) - 90.0
    #
    # reflect Y in small circle
    #
    y5 = 0.0 - (y3 - 0.0)
    y6 = 0.0 - (y4 - 0.0)
    #
    x5 = x3
    x6 = x4
    # Upper left line
    #
    # Upper part of large circle
    th = math.sqrt(((0.0 - x6)**2) + ((0.0 - y6)**2))
    aa2 = 90.0 - math.fabs(math.degrees(math.acos((0.0 - x6) / th)))
    #
    # reflect X in large circle
    #
    x7 = 0.0 + (0.0 - x6)
    y7 = y6
    #
    # reflect small circle in the large circles origo
    #
    x8 = 0.0 + (0.0 - x5)
    y8 = y5
    #
    #
    # reflect small circle in the large circles origo
    #
    #
    # reflect large circle in the large circles origo
    #
    x10 = x7
    y10 = 0.0 + (0.0 - y7)
    x9 = x8
    y9 = y3
    #
    # Rotate all postions
    #
    x3n = x3 * math.cos(math.radians(sadle_a)) - (y3 * math.sin(math.radians(sadle_a)))
    y3n = x3 * math.sin(math.radians(sadle_a)) + (y3 * math.cos(math.radians(sadle_a)))
    #
    x4n = x4 * math.cos(math.radians(sadle_a)) - (y4 * math.sin(math.radians(sadle_a)))
    y4n = x4 * math.sin(math.radians(sadle_a)) + (y4 * math.cos(math.radians(sadle_a)))
    #
    xL1n = (0 - sadle_x) * math.cos(math.radians(sadle_a)) - (0.0 * math.sin(math.radians(sadle_a)))
    yL1n = (0 - sadle_x) * math.sin(math.radians(sadle_a)) + (0.0 * math.cos(math.radians(sadle_a)))
    #
    x5n = x5 * math.cos(math.radians(sadle_a)) - (y5 * math.sin(math.radians(sadle_a)))
    y5n = x5 * math.sin(math.radians(sadle_a)) + (y5 * math.cos(math.radians(sadle_a)))
    #
    x6n = x6 * math.cos(math.radians(sadle_a)) - (y6 * math.sin(math.radians(sadle_a)))
    y6n = x6 * math.sin(math.radians(sadle_a)) + (y6 * math.cos(math.radians(sadle_a)))
    #
    #
    #
    x7n = x7 * math.cos(math.radians(sadle_a)) - (y7 * math.sin(math.radians(sadle_a)))
    y7n = x7 * math.sin(math.radians(sadle_a)) + (y7 * math.cos(math.radians(sadle_a)))
    #
    x8n = x8 * math.cos(math.radians(sadle_a)) - (y8 * math.sin(math.radians(sadle_a)))
    y8n = x8 * math.sin(math.radians(sadle_a)) + (y8 * math.cos(math.radians(sadle_a)))
    #
    xL2n = sadle_x * math.cos(math.radians(sadle_a)) - (0.0 * math.sin(math.radians(sadle_a)))
    yL2n = sadle_x * math.sin(math.radians(sadle_a)) + (0.0 * math.cos(math.radians(sadle_a)))
    #
    #
    #
    x9n = x9 * math.cos(math.radians(sadle_a)) - (y9 * math.sin(math.radians(sadle_a)))
    y9n = x9 * math.sin(math.radians(sadle_a)) + (y9 * math.cos(math.radians(sadle_a)))
    #
    x10n = x10 * math.cos(math.radians(sadle_a)) - (y10 * math.sin(math.radians(sadle_a)))
    y10n = x10 * math.sin(math.radians(sadle_a)) + (y10 * math.cos(math.radians(sadle_a)))
    #
    # reflect x and y for large circle
    #
    x2n = 0.0 - x10n
    y2n = 0.0 - y10n
    #
    # Translate cordinates to real origo
    #
    x2n = origo_x + x2n
    y2n = origo_y + y2n
    x3n = origo_x + x3n
    y3n = origo_y + y3n
    x4n = origo_x + x4n
    y4n = origo_y + y4n
    xL1n = origo_x + xL1n
    yL1n = origo_y + yL1n
    xL2n = origo_x + xL2n
    yL2n = origo_y + yL2n
    x5n = origo_x + x5n
    y5n = origo_y + y5n
    x6n = origo_x + x6n
    y6n = origo_y + y6n
    x7n = origo_x + x7n
    y7n = origo_y + y7n 
    x8n = origo_x + x8n
    y8n = origo_y + y8n
    x9n = origo_x + x9n
    y9n = origo_y + y9n
    x10n = origo_x + x10n
    y10n = origo_y + y10n
    #
    f.append(Line(start=(round(x3n, 2), round(y3n, 2)), end=(round(x4n, 2), round(y4n, 2)), layer=nlayer, width=wLayer))
    f.append(Arc(center=(round(xL1n, 2), round(yL1n, 2)), start=(round(x3n, 2), round(y3n, 2)), angle = round(2.0 * (90.0 - aa), 2) , layer=nlayer, width=wLayer))
    f.append(Line(start=(round(x5n, 2), round(y5n, 2)), end=(round(x6n, 2), round(y6n, 2)), layer=nlayer, width=wLayer))
    f.append(Line(start=(round(x7n, 2), round(y7n, 2)), end=(round(x8n, 2), round(y8n, 2)), layer=nlayer, width=wLayer))
    f.append(Arc(center=(round(xL2n, 2), round(yL2n, 2)), start=(round(x8n, 2), round(y8n, 2)), angle = round(2.0 * (90.0 - aa), 2) , layer=nlayer, width=wLayer))
    f.append(Line(start=(round(x9n, 2), round(y9n, 2)), end=(round(x10n, 2), round(y10n, 2)), layer=nlayer, width=wLayer))
    f.append(Arc(center=(round(origo_x, 2), round(origo_y, 2)), start=(round(x10n, 2), round(y10n, 2)), angle = round(2.0 * aa2, 2) , layer=nlayer, width=wLayer))
    f.append(Arc(center=(round(origo_x, 2), round(origo_y, 2)), start=(round(x2n, 2), round(y2n, 2)), angle = round(2.0 * aa2, 2) , layer=nlayer, width=wLayer))
    #
    # Min max for where to palce REF** and valve
    #
    maxy = 0.0
    maxy = max(maxy, y2n)
    maxy = max(maxy, y3n)
    maxy = max(maxy, y4n)
    maxy = max(maxy, yL1n + sadle_r2)
    maxy = max(maxy, yL2n + sadle_r2)
    maxy = max(maxy, y5n)
    maxy = max(maxy, y6n)
    maxy = max(maxy, y7n)
    maxy = max(maxy, y8n)
    maxy = max(maxy, y9n)
    maxy = max(maxy, y10n)
    miny = 0.0
    miny = min(miny, y2n)
    miny = min(miny, y3n)
    miny = min(miny, y4n)
    miny = min(miny, yL1n - sadle_r2)
    miny = min(miny, yL2n - sadle_r2)
    miny = min(miny, y5n)
    miny = min(miny, y6n)
    miny = min(miny, y7n)
    miny = min(miny, y8n)
    miny = min(miny, y9n)
    miny = min(miny, y10n)
    #
    # Fix sadle PCB hole
    #  pkg_sadle_pcb_hole: [('pad', 14.25, 1.3), ('npth', -14.25, 3.3)]  # Sadle holes in the PCB
    #
    if len(sadle_pcb_hole) > 0:
        for pd in sadle_pcb_hole:
            #
            # Rotate all postions
            #
            npx = pd[1] * math.cos(math.radians(sadle_a)) - (0.0 * math.sin(math.radians(sadle_a)))
            npy = pd[1] * math.sin(math.radians(sadle_a)) + (0.0 * math.cos(math.radians(sadle_a)))
            #
            # Translate cordinates to real origo
            #
            npx = origo_x + npx
            npy = origo_y + npy
            #
            if pd[0] == 'pad':
                #
                f.append(Pad(number="", 
                        type=Pad.TYPE_NPTH,
                        shape=Pad.SHAPE_CIRCLE,
                        at=[round(npx, 2), round(npy, 2)],
                        size=round(pd[2], 1),
                        layers=Pad.LAYERS_THT, 
                        drill=round(pd[2], 1),
                        radius_ratio=0.25))
                        
            if pd[0] == 'npth':
                #
                f.append(Pad(number="", 
                        type=Pad.TYPE_NPTH,
                        shape=Pad.SHAPE_CIRCLE,
                        at=[round(npx, 2), round(npy, 2)],
                        size=round(pd[2], 1),
                        layers=Pad.LAYERS_THT, 
                        drill=round(pd[2], 1),
                        radius_ratio=0.25))

        return(miny, maxy)

def bga(args):
    footprint_name = args["name"]
    description = args["pkg_description"]
    sadle = args["pkg_sadle"]
    sadle_hole = args["pkg_sadle_hole"]
    sadle_shield = args["pkg_sadle_shield"]
    sadle_pcb_hole = args["pkg_sadle_pcb_hole"]
    datasheet = args["pkg_datasheet"]
    D = args["pkg_D"]
    valve_offset = args["pkg_valve_offset"]
    socket_offset = args["pkg_socket_offset"]
    npth_pin = args["pkg_npth_pin"]
    center_pin = args["pkg_center_pin"]
    pin_type = args["pkg_pin_type"]
    pin_number = args["pkg_pin_number"]
    pin_arc = args["pkg_pin_arc"]
    pin_diameter = args["pkg_pin_diameter"]
    socket = args["pkg_socket"]
    tube = args["pkg_tube"]

    socket
    
    alpha_delta = 0 - ((pin_arc * math.pi) / 180.0)
    h = pin_diameter / 2.0
    origo_dx = (h * math.sin(alpha_delta))
    origo_dy = (h * math.cos(alpha_delta))
    
    origo_x = 0 - origo_dx
    origo_y = origo_dy
    
    print("origo_x origo_y " + str(round(origo_x / 2.0, 2)) + ', ' + str(round(origo_y / 2.0, 2)))
    
    s1 = [1.0, 1.0]
    s2 = [1.0, 1.0]
    
    t1 = 0.15 * s1[0]
    t2 = 0.15 * s2[0]

    yRef = origo_y - (D / 2.0) - (s1[1] * 1.2)
    yValue = origo_y + (D / 2.0) + (s1[1] * 1.2)
    #
    if len(sadle) > 4:
        if len(sadle) > 4:
            if sadle[5] > -45.0 and sadle[5] < 45.0:
                yRef = origo_y - (sadle[4] / 2.0) - (s1[1] * 1.2)
                yValue = origo_y + (sadle[4] / 2.0) + (s1[1] * 1.2)
            else:
                yRef = origo_y - (sadle[3] / 2.0) - (s1[1] * 1.2)
                yValue = origo_y + (sadle[3] / 2.0) + (s1[1] * 1.2)
        else:
            yRef = origo_y - (sadle[3] / 2.0) - (s1[1] * 1.2)
            yValue = origo_y + (sadle[3] / 2.0) + (s1[1] * 1.2)

    wFab = 0.10
    wCrtYd = 0.05
    wSilkS = 0.12
    
    description_tot = description + ', Made by script https://github.com/pointhi/kicad-footprint-generator/scripts/Valves, ' + datasheet
    
    #
    f = Footprint(footprint_name)
    f.setDescription(description_tot)
    f.setTags("{}".format(footprint_name))
    #
    s2ddh = 0.0
    if len(socket) > 2:
        s2ddh = valve_offset[2]
        s = socket
        f.append(Model(filename="${{KISYS3DMOD}}/Valve.3dshapes/{}.wrl".format(s), offset=(socket_offset[0], socket_offset[1], socket_offset[2])))
    #
    if len(tube) > 2:
        s = tube
        f.append(Model(filename="${{KISYS3DMOD}}/Valve.3dshapes/{}.wrl".format(s), offset=(valve_offset[0], valve_offset[1], s2ddh)))
    #
    if len(socket) == 0 and len(tube) == 0:
        f.append(Model(filename="${{KISYS3DMOD}}/Valve.3dshapes/{}.wrl".format(footprint_name), offset=(0,0,0)))

    #

    

    pad_size = round(pin_type[1] * 1.7, 1)
    pad_drill = round(pin_type[1] * 1.1, 1)
    alpha = alpha_delta
    pad_shape = Pad.SHAPE_RECT
    if pin_type[0] == 'tap':
        pad_size = [round(pin_type[1] * 1.7, 1), round(pin_type[2] * 1.7, 1)]
        pad_drill = [round(pin_type[1] * 1.1, 1), round(pin_type[2] * 1.1, 1)]
        pad_shape = Pad.SHAPE_OVAL
    #
    pad_type = Pad.TYPE_THT
    pad_layers = Pad.LAYERS_THT
    for i in range(0, pin_number):
        x1 = (h * math.sin(alpha)) + origo_x
        y1 = (h * math.cos(alpha)) - origo_y

        rotation = 0.0
        if pin_type[0] == 'tap':
            rotation = 360.0 - (alpha * (360.0 / (2.0 * math.pi)))
        #
        f.append(Pad(number="{}".format(i+1), 
                    type=pad_type,
                    shape=pad_shape,
                    at=[round(x1, 2), round((0 - y1), 2)],
                    size=pad_size,
                    layers=pad_layers, 
                    rotation=rotation,
                    drill=pad_drill,
                    radius_ratio=0.25))
        #
        pad_shape = Pad.SHAPE_ROUNDRECT
        if pin_type[0] == 'tap':
            pad_shape = Pad.SHAPE_OVAL
        alpha = alpha + alpha_delta

    if len(center_pin) > 0:
        if center_pin[0] == "metal":
            f.append(Pad(number="{}".format(pin_number + 1), 
                    type=pad_type,
                    shape=pad_shape,
                    at=[round(origo_x, 2), round(origo_y, 2)],
                    size=pad_size,
                    layers=pad_layers, 
                    drill=pad_drill,
                    radius_ratio=0.25))

    if len(npth_pin) > 0:
        for n in npth_pin:
            #
            # Add npth hole
            #
            f.append(Pad(number="", 
                    type=Pad.TYPE_NPTH,
                    shape=Pad.SHAPE_CIRCLE,
                    at=[round(n[0], 2), round(n[1], 2)],
                    size=n[2],
                    layers=Pad.LAYERS_THT, 
                    drill=n[2],
                    radius_ratio=0.25))
    
    
    #
    f.append(Text(type="user", text="%R",               at=[round(origo_x, 2), round(origo_y, 2)],  layer="F.Fab",      size=s2, thickness=t2))
                    
    
    maxy = yRef
    miny = yValue
    
    if len(sadle) > 1:
   
        create_sadle(f, origo_x, origo_y, sadle, sadle_hole, sadle_pcb_hole, "F.Fab", wFab)
        sadle2 = sadle.copy()
        sadle2[1] = sadle2[1] + 0.26
        sadle2[2] = sadle2[2] + 0.26
        sadle2[4] = sadle2[4] + 0.26
        create_sadle(f, origo_x, origo_y, sadle2, sadle_hole, sadle_pcb_hole, "F.SilkS", wSilkS)
        sadle3 = sadle.copy()
        sadle3[1] = sadle3[1] + 0.50
        sadle3[2] = sadle3[2] + 0.50
        sadle3[4] = sadle3[4] + 0.50
        (miny, maxy) = create_sadle(f, origo_x, origo_y, sadle3, sadle_hole, sadle_pcb_hole, "F.CrtYd", wCrtYd)
        miny = miny - (s1[1] * 1.2) 
        maxy = maxy + (s1[1] * 1.2) 
        
    else:
    
        DDq = D;
        er = math.sqrt(((pad_size / 2.0) * (pad_size / 2.0)) + ((pad_size / 2.0) * (pad_size / 2.0)))
        ar = math.sqrt((origo_x * origo_x) + (origo_y * origo_y))
        ad = ((ar + er) * 2.0) + 0.25

        if DDq < ad:
            DDq = ad
    
        # Fab
        f.append(Circle(center=(round(origo_x, 2), round(origo_y, 2)), radius=round((D / 2.0), 2), layer="F.Fab", width=wFab))

        # Silk
        f.append(Circle(center=(round(origo_x, 2), round(origo_y, 2)), radius=round((DDq / 2.0) + 0.13, 2), layer="F.SilkS", width=wSilkS))

        # Courtyard
        f.append(Circle(center=(round(origo_x, 2), round(origo_y, 2)), radius=round((DDq / 2.0) + 0.25, 2), layer="F.CrtYd", width=wCrtYd))
        
        miny = min(miny, origo_y - (DDq / 2.0) - (s1[1] * 1.2))
        maxy = max(maxy, origo_y + (DDq / 2.0) + (s1[1] * 1.2))

    # Text
    #
    f.append(Text(type="reference", text="REF**",    at=[round(origo_x, 2), round(miny, 2)], layer="F.SilkS", size=s1, thickness=t1))
    f.append(Text(type="value", text=footprint_name, at=[round(origo_x, 2), round(maxy, 2)], layer="F.Fab",   size=s1, thickness=t1))
        
                    
    file_handler = KicadFileHandler(f)
    file_handler.writeFile(footprint_name + ".kicad_mod")

if __name__ == '__main__':
    parser = ModArgparser(bga)
    # the root node of .yml files is parsed as name
    parser.add_parameter("name",                type=str,   required=True)
    parser.add_parameter("pkg_description",     type=str,   required=True)
    parser.add_parameter("pkg_datasheet",       type=str,   required=True)
    parser.add_parameter("pkg_D",               type=float, required=True)
    parser.add_parameter("pkg_sadle",           type=list,  required=True)
    parser.add_parameter("pkg_sadle_hole",      type=list,  required=True)
    parser.add_parameter("pkg_sadle_shield",    type=list,  required=True)
    parser.add_parameter("pkg_sadle_pcb_hole",  type=list,  required=True)
    parser.add_parameter("pkg_valve_offset",    type=list,  required=True)
    parser.add_parameter("pkg_socket_offset",   type=list,  required=True)
    parser.add_parameter("pkg_npth_pin",        type=list,  required=True)
    parser.add_parameter("pkg_center_pin",      type=list,  required=True)
    parser.add_parameter("pkg_pin_type",        type=list,  required=True)
    parser.add_parameter("pkg_pin_number",      type=int,   required=True)
    parser.add_parameter("pkg_pin_arc",         type=float, required=False)
    parser.add_parameter("pkg_pin_diameter",    type=float, required=False)
    parser.add_parameter("pkg_socket",          type=str,   required=False)
    parser.add_parameter("pkg_tube",            type=str,   required=False)
    
    # now run our script which handles the whole part of parsing the files
    parser.run()
