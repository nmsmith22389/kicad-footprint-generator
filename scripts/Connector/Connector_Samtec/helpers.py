import sys
import os

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))
import KicadModTree

def roundToBase(value, base):
    if base == 0:
        return value
    return round(value/base) * base

def markerArrow(x, y, width, line_width, layer="F.Fab", angle=0, close=True):
    """
    Draws a triangular marker arrow at the specified location.
    
    Args:
        x: x-coordinate of arrow tip
        y: y-coordinate of arrow tip
        width: width of the arrow
        line_width: width of lines forming the arrow
        layer: PCB layer string (default: "F.Fab")
        angle: orientation of the arrow in degrees (0° points up)
        close (bool): True to draw a line closing the triangle
    
    Returns:
        KicadModTree.Node object that generates the marker arrow
    """
    node = KicadModTree.Node()
    points = [(-width/2, width/2),
              (0, 0),
              (width/2, width/2)]

    if close:
        points.append((-width/2, width/2))

    node.append(KicadModTree.PolygoneLine(nodes = points,
                                          layer = layer,
                                          width = line_width))
    node.insert(KicadModTree.Rotation(angle))
    node.insert(KicadModTree.Translation(x,y))
    return node
