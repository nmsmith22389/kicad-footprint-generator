from math import isclose
import cadquery as cq

def make_qfn(params):

    color_pin_mark=True

    c  = params['c']
    ef  = params['ef']
    cce = params['cce']
    fp_s = params['fp_s']
    fp_r  = params['fp_r']
    fp_d  = params['fp_d']
    fp_z  = params['fp_z']
#    K  = params['K']
    L  = params['L']
    Lx = params['Lx'] if 'Lx' in params else None
    Ly = params['Ly'] if 'Ly' in params else None
    D  = params['D']
    E   = params['E']
    A1  = params['A1']
    A2  = params['A2']
    b   = params['b']
    e   = params['e']
    m   = params['m']
    ps  = params['ps']
    npx = params['npx']
    npy = params['npy']
    mN  = params['model_name']
    rot = params['rotation']
    # dest_dir_pref = params['dest_dir_prefix']
    pin_shapes = params['pin_shapes']
    if params['excluded_pins']:
        excluded_pins = params['excluded_pins']
    else:
        excluded_pins=() ##no pin excluded 

    if isclose(A1, 0.0):
        print("A1 can NOT be zero (or this script will fail). Setting A1 to 0.02")
        A1 = 0.02

    if L is not None:
        Lx = L
        Ly = L
    else:
        if npx > 0 and Lx is None:
            print("Pin length along x axis is not set (neither 'Lx' nor 'L'). Setting pin length to pin width.")
            Lx = c
        if npy > 0 and Ly is None:
            print("Pin length along y axis is not set (neither 'Ly' nor 'L'). Setting pin length to pin width.")
            Ly = c

    epad_rotation = 0.0
    epad_offset_x = 0.0
    epad_offset_y = 0.0

    if params['epad']:
        #if isinstance(params['epad, float):
        if not isinstance(params['epad'], list):
            sq_epad = False
            epad_r = params['epad']
        else:
            sq_epad = True
            D2 = params['epad'][0]
            E2 = params['epad'][1]
            if len(params['epad']) > 2:
                epad_rotation = params['epad'][2]
            if len(params['epad']) > 3:
                if isinstance (params['epad'][3], str):
                    if params['epad'][3] == '-topin':
                        epad_offset_x = (D/2-D2/2) * -1
                    elif params['epad'][3] == '+topin':
                        epad_offset_x = D/2-D2/2
                else:
                    epad_offset_x = params['epad'][3]
            if len(params['epad']) > 4:
                if isinstance (params['epad'][4], str):
                    if params['epad'][4] == '-topin':
                        epad_offset_y = (E/2-E2/2) * -1
                    elif params['epad'][4] == '+topin':
                        epad_offset_y = E/2-E2/2
                else:
                    epad_offset_y = params['epad'][4]
            if params['epad_offsetX'] is not None:
                 epad_offset_x += params['epad_offsetX']
            if params['epad_offsetY'] is not None:
                 epad_offset_y += params['epad_offsetY']
                    
    A = A1 + A2


    if m == 0:
        case = cq.Workplane("XY").box(D-A1, E-A1, A2)  #margin to see fused pins
    else:
        case = cq.Workplane("XY").box(D, E, A2)  #NO margin, pins don't emerge
    if ef!=0:
        case.edges("|X").fillet(ef)
        case.edges("|Z").fillet(ef)
    #translate the object
    case=case.translate((0,0,A2/2+A1)).rotate((0,0,0), (0,0,1), 0)

    # first pin indicator is created with a spherical pocket
    if (fp_d is not None):
        fp_dx = fp_d
        fp_dy = fp_d
    else:
        if params['fp_dx'] is not None:
            fp_dx = params['fp_dx']
        else:
            fp_dx = 0
        if params['fp_dy'] is not None:
            fp_dy = params['fp_dy']
        else:
            fp_dy = 0

    if ps == 'concave' or ps == 'cshaped':
        if npy != 0:
            fp_dx = fp_d+L-A1/2
        if npx != 0:
            fp_dy = fp_d+L-A1/2
    if fp_r == 0:
        global place_pinMark
        place_pinMark=False
        fp_r = 0.1
    if fp_s == False:
        pinmark = cq.Workplane(cq.Plane.XY()).workplane(offset=A ,centerOption="CenterOfMass").box(fp_r, E-fp_dy*2, fp_z*2) #.translate((E1/2,0,A1)).rotate((0,0,0), (0,0,1), 90)
        #translate the object  
        pinmark=pinmark.translate((-D/2+fp_r/2+fp_dx,0,0)) #.rotate((0,0,0), (0,1,0), 0)
    else:
        sphere_r = (fp_r*fp_r/2 + fp_z*fp_z) / (2*fp_z)
        sphere_z = A + sphere_r * 2 - fp_z - sphere_r
    
        pinmark=cq.Workplane("XZ", (-D/2+fp_dx+fp_r, -E/2+fp_dy+fp_r, fp_z)).rect(fp_r/2, -2*fp_z, False).revolve().translate((0,0,A))#+fp_z))

    #stop
    if (color_pin_mark==False) and (place_pinMark==True):
        case = case.cut(pinmark)
    #stop
    bpin_shape = dict()
    for axis, length in zip(['x','y'], [Lx, Ly]):
        if ps == 'square': #square pins
            bpin = cq.Workplane("XY"). \
                moveTo(b, 0). \
                lineTo(b, length). \
                lineTo(0, length). \
                lineTo(0, 0). \
                close().extrude(c).translate((-b/2,-E/2,0)). \
                rotate((0,0,0), (0,0,1), -180) #((b/2,E/2,A1/2), (0,0,1), 180)
                #close().extrude(c).translate((b/2,E/2,A1/2))
        elif ps == 'rounded':
            bpin = cq.Workplane("XY"). \
                moveTo(b, 0). \
                lineTo(b, length-b/2). \
                threePointArc((b/2,length),(0, length-b/2)). \
                lineTo(0, 0). \
                close().extrude(c).translate((-b/2,-E/2,0)). \
                rotate((0,0,0), (0,0,1), -180)            
                #close().extrude(c).translate((b/2,E/2,A1/2))
        elif ps == 'concave':
            pincut = cq.Workplane("XY").box(b, length, A2+A1*2).translate((0,E/2-length/2,A2/2+A1))
            bpin = cq.Workplane("XY").box(b, length, A2+A1*2).translate((0,E/2-length/2,A2/2+A1)).edges("|X").fillet(A1)
            bpin = bpin.faces(">Z").edges(">Y").workplane(centerOption="CenterOfMass").circle(b*0.3).cutThruAll()
        elif ps == 'cshaped':
            bpin = cq.Workplane("XY").box(b, length, A2+A1*2).translate((0,E/2-L/2,A2/2+A1)).edges("|X").fillet(A1)
        bpin_shape[axis] = bpin

    pins = []
    pincounter = 1
    if ps == 'custom':
        for pin_shape in pin_shapes:
            first_point = pin_shape[0]
            pin = cq.Workplane("XY"). \
                moveTo(first_point[0], first_point[1])
            for i in range(1, len(pin_shape)):
                point = pin_shape[i]
                pin = pin.lineTo(point[0], point[1])
            pin = pin.close().extrude(c)
            pins.append(pin)
        pincounter += 1
    else:
        # create top, bottom side pins
        first_pos_x = (npx-1)*e/2
        for i in range(npx):
            if pincounter not in excluded_pins:
                pin = bpin_shape['x'].translate((first_pos_x-i*e, -m, 0)). \
                rotate((0,0,0), (0,0,1), 180)
                pins.append(pin)
                if ps == 'concave':
                    pinsubtract = pincut.translate((first_pos_x-i*e, -m, 0)). \
                    rotate((0,0,0), (0,0,1), 180)
                    case = case.cut(pinsubtract)
            pincounter += 1
    
        first_pos_y = (npy-1)*e/2
        for i in range(npy):
            if pincounter not in excluded_pins:
                pin = bpin_shape['y'].translate((first_pos_y-i*e, (D-E)/2-m, 0)).\
                rotate((0,0,0), (0,0,1), 270)
                pins.append(pin)
                if ps == 'concave':
                    pinsubtract = pincut.translate((first_pos_y-i*e, (D-E)/2-m, 0)).\
                    rotate((0,0,0), (0,0,1), 270)
                    case = case.cut(pinsubtract)
            pincounter += 1

        for i in range(npx):
            if pincounter not in excluded_pins:
                pin = bpin_shape['x'].translate((first_pos_x-i*e, -m, 0))
                pins.append(pin)
                if ps == 'concave':
                    pinsubtract = pincut.translate((first_pos_x-i*e, -m, 0))
                    case = case.cut(pinsubtract)
            pincounter += 1
        
        for i in range(npy):
            if pincounter not in excluded_pins:
                pin = bpin_shape['y'].translate((first_pos_y-i*e, (D-E)/2-m, 0)).\
                rotate((0,0,0), (0,0,1), 90)
                pins.append(pin)
                if ps == 'concave':
                    pinsubtract = pincut.translate((first_pos_y-i*e, (D-E)/2-m, 0)).\
                    rotate((0,0,0), (0,0,1), 90)
                    case = case.cut(pinsubtract)
            pincounter += 1

    # create exposed thermal pad if requested
    if params['epad']:
        if sq_epad:
            if params['epad_n'] is not None and \
               params['epad_pitch'] is not None:
                for nx in range(1,params['epad_n'][0]+1):
                    for ny in range(1,params['epad_n'][1]+1):
                        offset_x = -((params['epad_n'][0]-1)*params['epad_pitch'][0])/2+(nx-1)*params['epad_pitch'][0]
                        offset_y = -((params['epad_n'][1]-1)*params['epad_pitch'][1])/2+(ny-1)*params['epad_pitch'][1]
                        epad = cq.Workplane("XY").\
                        moveTo(-D2/2+cce, -E2/2). \
                        lineTo(D2/2, -E2/2). \
                        lineTo(D2/2, E2/2). \
                        lineTo(-D2/2, E2/2). \
                        lineTo(-D2/2, -E2/2+cce). \
                        close().extrude(A1+A1/2). \
                        translate((epad_offset_x+offset_x,epad_offset_y+offset_y,0)). \
                        rotate((0,0,0), (0,0,1), epad_rotation) #+A1/2).translate((0,0,A1/2))
                        #close().extrude(A1+A1/10)
                        pins.append(epad)
            else:
                #pins.append(cq.Workplane("XY").box(D2, E2, A1+A1/10).translate((0,0,A1+A1/10)))
                #epad = cq.Workplane("XY", (0,0,A1/2)). \
                epad = cq.Workplane("XY").\
                moveTo(-D2/2+cce, -E2/2). \
                lineTo(D2/2, -E2/2). \
                lineTo(D2/2, E2/2). \
                lineTo(-D2/2, E2/2). \
                lineTo(-D2/2, -E2/2+cce). \
                close().extrude(A1+A1/2). \
                translate((epad_offset_x,epad_offset_y,0)). \
                rotate((0,0,0), (0,0,1), epad_rotation) #+A1/2).translate((0,0,A1/2))
                #close().extrude(A1+A1/10)
                pins.append(epad)
        else:
            if params['epad_n'] is not None and \
               params['epad_pitch'] is not None:
                for nx in range(1,params['epad_n'][0]):
                    for ny in range(1,params['epad_n'][1]):
                        offset_x = -((params['epad_n'][0]-1)*params['epad_pitch'][0])/2+(nx-1)*params['epad_pitch'][0]
                        offset_y = -((params['epad_n'][1]-1)*params['epad_pitch'][1])/2+(ny-1)*params['epad_pitch'][1]
                        epad = cq.Workplane("XY").\
                        circle(epad_r). \
                        extrude(A1). \
                        translate((offset_x,offset_y,A1/2))
                        pins.append(epad)
            else:
                #pins.append(cq.Workplane("XY").box(D2, E2, A1+A1/10).translate((0,0,A1+A1/10)))
                #epad = cq.Workplane("XY", (0,0,A1/2)). \
                epad = cq.Workplane("XY").\
                circle(epad_r). \
                extrude(A1) #+A1/2).translate((0,0,A1/2))
                #extrude(A1+A1/2).translate((0,0,A1/2))
                pins.append(epad)

    # merge all pins to a single object
    merged_pins = pins[0]
    for p in pins[1:]:
        merged_pins = merged_pins.union(p)
    pins = merged_pins

    #show(pins)
    #sleep
    # extract pins from case
    case = case.cut(pins)

    return (case, pins, pinmark)