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
# (C) 2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) 2024 by C. Kuhlmann, gitlab @CKuhlmann

# import KicadModTree
# from KicadModTree.nodes.base import *
from __future__ import annotations

from KicadModTree.PolygonPoints import *
from KicadModTree.Vector import *
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.base.PolygonArc import PolygonArc, geometricArc

from collections import deque

from KicadModTree.nodes.base.Line import Line, geometricLine
from KicadModTree.nodes.base.Group import Group

from enum import Enum

from copy import copy

import uuid
from typing import TypedDict, Callable
from typing_extensions import Unpack


class CompoundPolygonPrimitives(Enum):
    point = PolygonPoints
    arc = PolygonArc


class NativePolygonArgs(TypedDict):
    polygon: list
    layer: str
    width: float
    stroke_type: str
    fill: str
    enforce_continuous: bool
    enforce_closed: bool

    remove_point_duplicates: bool
    remove_closing_duplicates: bool

    serialize_as_fp_poly: bool
    group_free_primitives: bool


class CompoundPolygon(Node):
    r"""Add a Compound Polygon to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *polygon* (``list(Vector2D, PolygonPoints, Line, geometricLine, Arc, PolygonArc)``) --
          outer nodes of the polygon
        * *layer* (``str``) --
          layer on which the line is drawn (default: 'F.Cu')
        * *width* (``float``) --
          width of the line (default: None, which means auto detection)
        * *stroke_type* (``str``),
            'solid', 'dash', 'dash_dot', 'dash_dot_dot', 'dot'
        * *fill* (``str``)
            'solid', 'none'

        * *x_mirror* (``[int, float](mirror offset)``) --
          mirror x direction around offset "point"
        * *y_mirror* (``[int, float](mirror offset)``) --
          mirror y direction around offset "point"

        * *enforce_continuous* (``bool``) --
          Enforce that all primitives build a continuous contour (default: True)
        * *enforce_closed* (``bool``) --
          Enforce that the primitives build a closed contour,
          i.e. first point of the first primitive is coincident with the last point
          of the last primitive (upt to 1 nm tolerance). (default: True)

        * *remove_point_duplicates* (``bool``) --
          will remove duplicate points in the ``polygon`` parameter geometries (default: True)
        * *remove_closing_duplicates* (``bool``) --
          will remove the closing point if it belogs to a polygon-line if the polygon is serializes as fp_poly.
          KiCad will close the polygon implicitly from last-to-first point for a fp_poly (default: True)

        * *serialize_as_fp_poly* (``bool``) --
          (default: True)
          if True, will serialize the compound polygon as fp_poly, leading to line-segment-appromimations of
          contained arcs in the FP editor (the file format already supports arcs, but the editor does not)
          if False, will break the polygon into free primitives, yielding true arcs in the FP editor but no
          single primitive. Grouping will be used.

        * *group_free_primitives* (``bool``) --
          Will create groups for free primitives if True (default: True)

    :Example:

    >>> from KicadModTree import *
    >>> Polygon(nodes=[[-2, 0], [0, -2], [4, 0], [0, 2]], layer='F.SilkS')
    """

    tolerance = 1e-9

    def _enforePolyContinuousIfDesired(self, lst):
        if (self.enforce_continuous
           and (not self._checkPointCoincidentWithAny(self._lastAppendedPolyGeomEndPoint, lst))):
            raise ValueError(f"Points {repr(lst)} are not continuously coincident with the previous "
                             + f" polygon point {repr(self._lastAppendedPolyGeomEndPoint)} but start a new segment "
                             + f"(may belong to complex geometry).")

    def _appendPolygonPointsTempToPolygonAndReset(self):
        r""" appends the temporyrily stored points, resets the temp list
             and returns a copy of the last point in the poly """
        if self._polygon_points_temp is None:
            return None
        if len(self._polygon_points_temp) <= 0:
            self._polygon_points_temp = None
            return None
        lst = []
        start = self._polygon_points_temp[0]
        lst.append(start)
        if len(self._polygon_points_temp) > 1:
            end = self._polygon_points_temp[-1]
            lst.append(end)
        else:
            end = None

        polygon_points_obj = PolygonPoints(nodes=self._polygon_points_temp)
        # force appending to prevent redirecting temp points into temp points
        # and then resetting temp to None, losing them
        self._appendGeometry(node=polygon_points_obj, force_append=True)

        self._polygon_points_temp = None
        pass

    def _rememberLastAppendedPrimitiveType(self, primitiveType: CompoundPolygonPrimitives):
        self._lastAppendedPrimitiveType = primitiveType

    def _appendPointToPolygonPointsTemp(self, point, rememberAsFirst=True, rememberAsRecent=False):
        point = Vector2D(point)
        if self._polygon_points_temp is None:
            self._polygon_points_temp = []

        self._polygon_points_temp.append(point)

        if rememberAsFirst:
            self._rememberFirstPolyPointIfUnset(point)
        if rememberAsRecent:
            self._rememberRecentAppendedPolyGeomEndPoint(point)

    def _rememberFirstPolyPointIfUnset(self, new_point: Vector2D):
        if self._firstPolyPoint is None:
            self._firstPolyPoint = Vector2D(new_point)

    def _rememberRecentAppendedPolyGeomEndPoint(self, new_end_point: Vector2D):
        self._lastAppendedPolyGeomEndPoint = Vector2D(new_end_point)
        self._rememberFirstPolyPointIfUnset(new_end_point)

    def _getGeomStart(self, node):
        if isinstance(node, PolygonPoints):
            pnts = node.getPoints()
            return pnts[0]
        elif isinstance(node, PolygonArc):
            startpnt = node.getStartPoint()
            # endpnt = node.getEndPoint()
            return startpnt
        else:
            NotImplementedError("Unknown geometry of type "+type(node))

    def _getGeomEnd(self, node):
        if isinstance(node, PolygonPoints):
            pnts = node.getPoints()
            return pnts[-1]
        elif isinstance(node, PolygonArc):
            # startpnt = node.getStartPoint()
            endpnt = node.getEndPoint()
            return endpnt
        else:
            NotImplementedError("Unknown geometry of type "+type(node))

    def _appendGeometry(self, node, force_append=False):
        if isinstance(node, PolygonPoints):
            points = node.getPoints()

            if (not (self.remove_point_duplicates)) or (force_append):
                self.polygon_geometries.append(node)
                self._rememberLastAppendedPrimitiveType(
                    CompoundPolygonPrimitives.point)
                self._rememberFirstPolyPointIfUnset(points[0])
                self._rememberRecentAppendedPolyGeomEndPoint(points[-1])
            else:
                pnt_cnt = len(points)
                for idx, pt in enumerate(points):
                    last_in_node = ((idx+1) == pnt_cnt)
                    self._appendPointToPolygonPointsTemp(
                        point=pt, rememberAsFirst=True, rememberAsRecent=last_in_node)
                    self._rememberLastAppendedPrimitiveType(
                        CompoundPolygonPrimitives.point)
                    # self._rememberFirstPolyPointIfUnset(points[0]) # done in _appendPointToPolygonPointsTemp
                # self._rememberRecentAppendedPolyGeomEndPoint(points[-1]) # done in _appendPointToPolygonPointsTemp

        elif isinstance(node, PolygonArc):
            startpnt = node.getStartPoint()
            endpnt = node.getEndPoint()
            self._rememberFirstPolyPointIfUnset(startpnt)
            self._rememberRecentAppendedPolyGeomEndPoint(endpnt)
            self.polygon_geometries.append(node)

            self._rememberLastAppendedPrimitiveType(
                CompoundPolygonPrimitives.arc)
        else:
            NotImplementedError("Unknown geometry of type "+type(node))

    def _checkPointsCoincident(self, a: Vector2D | None, b: Vector2D, tol=None) -> bool:
        if tol is None:
            tol = self.tolerance
        if b is None:
            return False  # only first point in poly will be initially unset, every other point needs to be valid
        if ((a is None) or (abs(a[0]-b[0]) <= tol) and (abs(a[1]-b[1]) <= tol)):
            return True
        return False

    def _checkPointCoincidentWithAny(self, a: Vector2D, lst: list[Vector2D]) -> bool:
        for b in lst:
            if self._checkPointsCoincident(a, b):
                return True
        return False

    def _polyGeometryChecksAndReturnIsReversed(self, new_geom_start: Vector2D, new_geom_end: Vector2D) -> bool:
        r"""
        checks geometry and returns True if start and end are reversed.
        Throws a ValueError if not continuous but this enforcement is requested.
        """
        self._enforePolyContinuousIfDesired([new_geom_start, new_geom_end])
        if ((self._lastAppendedPolyGeomEndPoint is not None)
                and (self._checkPointsCoincident(self._lastAppendedPolyGeomEndPoint, new_geom_end))):
            reversed = True
        else:
            reversed = False
        return reversed

    class _FinalGeom(object):
        def __init__(self) -> None:
            pass

    def _removeDuplicatePointsInList(self, points):
        prev: Vector2D = None
        unique_points: list[Vector2D] = []
        for pt in points:
            pt: Vector2D = Vector2D(pt)
            if (prev is not None) and (abs(prev.x - pt.x) < self.tolerance) and (abs(prev.y - pt.y) < self.tolerance):
                pass  # duplicate
            else:
                unique_points.append(pt)
        return unique_points

    def _handleAndAppendGeometry(self, node):
        node
        if isinstance(node, Vector2D):
            if ((self._lastAppendedPolyGeomEndPoint is not None)
                    and (self._checkPointsCoincident(self._lastAppendedPolyGeomEndPoint, node))):
                # first point was already present,ignore if type was a point primitive
                if ((self._rememberLastAppendedPrimitiveType != CompoundPolygonPrimitives.point)
                        or (not self.remove_point_duplicates)):
                    self._appendPointToPolygonPointsTemp(node)
                else:
                    pass  # duplicate of same prim type: skip
            else:
                self._appendPointToPolygonPointsTemp(node)

        elif isinstance(node, Line) or isinstance(node, geometricLine):
            if (not self.remove_point_duplicates):
                self._appendPolygonPointsTempToPolygonAndReset()
            node: geometricLine = node
            line_points = [node.start_pos, node.end_pos]
            if (self._polyGeometryChecksAndReturnIsReversed(node.start_pos, node.end_pos)):  # reversed
                line_points.reverse()

            if ((self._lastAppendedPolyGeomEndPoint is not None)
                    and self._checkPointsCoincident(self._lastAppendedPolyGeomEndPoint, line_points[0])):
                # first line point already present, remove if last type was a point primitive
                if self._lastAppendedPrimitiveType == CompoundPolygonPrimitives.point:
                    del line_points[0]

            self._appendGeometry(PolygonPoints(nodes=line_points))

        elif isinstance(node, PolygonPoints):
            if (not self.remove_point_duplicates):
                self._appendPolygonPointsTempToPolygonAndReset()
            points = node.getPoints()
            if (self.remove_point_duplicates):
                points = self._removeDuplicatePointsInList(points)
            if len(points) <= 0:
                return  # nothing to do here

            # reversed
            if (self._polyGeometryChecksAndReturnIsReversed(points[0], points[-1])):
                points.reverse()

            if self._lastAppendedPrimitiveType != CompoundPolygonPrimitives.point:
                self._enforePolyContinuousIfDesired(points)

            if ((self._lastAppendedPolyGeomEndPoint is not None)
                    and self._checkPointsCoincident(self._lastAppendedPolyGeomEndPoint, points[0])):
                # first line point already present, remove if last type was a point primitive.
                # Duplicate points _within_ this primitive need to be filtered beforehand

                if self._lastAppendedPrimitiveType == CompoundPolygonPrimitives.point:
                    if len(points) > 0:
                        del points[0]
                    else:
                        return
            self._appendGeometry(PolygonPoints(nodes=points))

        elif isinstance(node, Arc) or isinstance(node, PolygonArc):
            self._appendPolygonPointsTempToPolygonAndReset()
            node: PolygonArc = node
            startpnt = node.getStartPoint()
            endpnt = node.getEndPoint()
            # points = [start, end]
            if (self._polyGeometryChecksAndReturnIsReversed(startpnt, endpnt)):  # reversed
                # todo: consider redefining the arc from end over mid to start
                # is better than possibly losing some properties
                midpnt = node.getMidPoint()
                ctrpnt = node.getCenter()
                node = PolygonArc(center=ctrpnt, start=endpnt,
                                  midpoint=midpnt, end=startpnt)
                pass
            else:
                # equivalent of cast to geometric Arc since we cannot change layer or with within poly geometry
                midpnt = node.getMidPoint()
                ctrpnt = node.getCenter()
                node = PolygonArc(center=ctrpnt, start=startpnt,
                                  midpoint=midpnt, end=endpnt)

            # (self._lastAppendedPrimitiveType == CompoundPolygonPrimitives.point)
            # or (self._lastAppendedPrimitiveType == CompoundPolygonPrimitives.arc):
            if True:
                self._enforePolyContinuousIfDesired([startpnt, endpnt])

            self._appendGeometry(node)
        elif isinstance(node, CompoundPolygon._FinalGeom):
            self._appendPolygonPointsTempToPolygonAndReset()
        else:
            raise ValueError(
                f"Unknown/unsupported polygon geometry of class {repr(node)}")

    def PolyHasAnyArc(self) -> bool:
        for geom in self.nodes:
            if isinstance(geom, PolygonArc) or isinstance(geom, Arc) or isinstance(geom, geometricArc):
                return True
        for geom in self.polygon_geometries:
            if isinstance(geom, PolygonArc) or isinstance(geom, Arc) or isinstance(geom, geometricArc):
                return True
        return False

    def __init__(self, **kwargs: Unpack[NativePolygonArgs]):
        super().__init__()
        # Node.__init__(self)

        self.polyargs = copy(kwargs)
        self.polyargs.pop('polygon', None)
        self.polyargs.pop('nodes', None)

        self.enforce_continuous = kwargs.get('enforce_continuous', True)
        self.enforce_closed = kwargs.get('enforce_closed', True)

        self.serialize_as_fp_poly = kwargs.get('serialize_as_fp_poly', True)

        self.remove_point_duplicates = kwargs.get(
            'remove_point_duplicates', True)
        self.remove_closing_duplicates = (kwargs.get(
            'remove_closing_duplicates', True) and (self.serialize_as_fp_poly))

        self.group_free_primitives = kwargs.get('group_free_primitives', True)

        self._firstPolyPoint = None
        self._lastAppendedPolyGeomEndPoint = None
        self._lastAppendedPrimitiveType = None

        self.polygon_nodes_raw = kwargs.get("polygon", kwargs.get("nodes", []))

        self.polygon_geometries = deque(maxlen=None)

        self._polygon_points_temp = None
        for nd in self.polygon_nodes_raw:
            self._handleAndAppendGeometry(nd)
        # append any dangling temp points of the last segment
        self._handleAndAppendGeometry(CompoundPolygon._FinalGeom())

        self.closed_contour = (self._firstPolyPoint is not None) and self._checkPointsCoincident(
            self._firstPolyPoint, self._lastAppendedPolyGeomEndPoint)

        if self.enforce_closed:
            if not self.closed_contour:
                raise ValueError(f"CompoundPolygon has been configured to enforce a closed contour, "
                                 + f"but first point {str(self._firstPolyPoint)} is not conincident with "
                                 + f"last point {str(self._lastAppendedPolyGeomEndPoint)} "
                                 + f"for the provided primtives {str(self.polygon_nodes_raw)}.")

        if self.closed_contour and self.remove_closing_duplicates and (len(self.polygon_geometries) > 0):
            # check endpoint first
            if isinstance(self.polygon_geometries[-1], PolygonPoints):
                last_pt_geom: PolygonPoints = self.polygon_geometries.pop()
                last_pt_geom_points = deque(last_pt_geom.getPoints())
                last_pt_geom_points.pop()  # last point is doubled by first point, remove it from store
                if (len(last_pt_geom_points) > 0):  # only add if still points present
                    self.polygon_geometries.append(PolygonPoints(
                        nodes=last_pt_geom_points))  # re-add geom
                self._lastAppendedPolyGeomEndPoint = self._getGeomEnd(
                    self.polygon_geometries[-1])
            elif isinstance(self.polygon_geometries[0], PolygonPoints):
                first_pt_geom: PolygonPoints = self.polygon_geometries.popleft()
                first_pt_geom_points = deque(last_pt_geom.getPoints())
                # first point is doubled by last point (which is in a complex geometry where
                # removing points may not be possible), remove it from store
                first_pt_geom_points.popleft()
                if (len(first_pt_geom_points) > 0):  # only add if still points present
                    self.polygon_geometries.appendleft(PolygonPoints(
                        nodes=first_pt_geom_points))  # re-add geom
                self._firstPolyPoint = self._getGeomStart(
                    self.polygon_geometries[0])
            else:
                pass  # both start and end are part of complex geometry where removing points is not possible

        self.start = self._firstPolyPoint
        self.end = self._lastAppendedPolyGeomEndPoint

        # self.nodes = PolygonPoints(**kwargs)
        self.nodes = self.polygon_geometries

        self.layer = kwargs.get('layer', 'F.Cu')
        self.width = kwargs.get('width', None)
        self.stroke_type = kwargs.get('stroke_type', 'solid')
        self.fill = kwargs.get('fill', 'solid')

    def _serialize_PolygonPointsSegment(self, kicadFileHandler, polygonpoints: PolygonPoints):
        from KicadModTree.util.kicad_util import SexprSerializer

        node_points = []

        for n in polygonpoints:
            n_pos = self.getRealPosition(n)
            node_points.append([SexprSerializer.Symbol('xy'), n_pos.x, n_pos.y])

        return node_points

    def get_tstamp_from_sexpr(self, sexpr: list):
        for item in sexpr:
            if isinstance(item, list) or isinstance(item, tuple):
                if len(item) == 2 and item[0] == 'tstamp':
                    return item[1]
        return None

    def isSerializedAsFPPoly(self) -> bool:
        return (self.closed_contour and self.serialize_as_fp_poly)

    def _serialize_get_virtual_nodes(self):
        virt_nodes = []
        node = self

        group_ids = []

        for geom in node.polygon_geometries:
            if isinstance(geom, PolygonPoints):
                p1 = None
                for p2 in geom.getPoints():
                    if p1 is not None:
                        sub_node = Line(start=p1, end=p2,
                                        layer=node.layer, width=node.width)
                        sub_node.setTStampSeedFromNode(node)
                        tstamp_uuid = sub_node.getTStamp()
                        if tstamp_uuid is not None:
                            group_ids.append(str(tstamp_uuid))

                        virt_nodes.append(sub_node)

                    p1 = p2  # p2 becomes the new p1 of next segment

            elif isinstance(geom, PolygonArc):
                sub_node = Arc(start=geom.getStartPoint(), end=geom.getEndPoint(
                ), center=geom.getCenter(), layer=node.layer, width=node.width)

                sub_node.setTStampSeedFromNode(node)
                tstamp_uuid = sub_node.getTStamp()
                if tstamp_uuid is not None:
                    group_ids.append(str(tstamp_uuid))

                virt_nodes.append(sub_node)

            else:
                sub_node: Node = geom
                if not sub_node.hasValidSeedForTStamp():
                    sub_node.setTStampSeedFromNode(node)
                tstamp_uuid = sub_node.getTStamp()
                if tstamp_uuid is not None:
                    group_ids.append(str(tstamp_uuid))

                virt_nodes.append(sub_node)
        pass  # end for

        if (group_ids) and (node.group_free_primitives):  # group free primitives
            sub_node = Group(
                name=f"GroupForCompoundPolygon_{str(node.getTStamp())}", member_tstamps=group_ids)

            if not sub_node.hasValidSeedForTStamp():
                sub_node.setTStampSeedFromNode(node)
            tstamp_uuid = sub_node.getTStamp()

            virt_nodes.append(sub_node)

        return virt_nodes

    def getVirtualChilds(self):
        node = self

        if not node.isSerializedAsFPPoly():
            # explode to (grouped) virtual primitives
            return self._serialize_get_virtual_nodes()
        else:
            return []  # serialize using serialize_specific_node function to create fp_poly

    def serialize_specific_node(self, kicadFileHandler):
        from KicadModTree.util.kicad_util import SexprSerializer
        node = self

        if node.isSerializedAsFPPoly():

            node_points_sexpr = [SexprSerializer.Symbol('pts')]
            # node_points_sexpr.append(SexprSerializer.NEW_LINE)

            for geom in node.polygon_geometries:
                if isinstance(geom, PolygonPoints):
                    node_points_sexpr.extend(self._serialize_PolygonPointsSegment(
                        kicadFileHandler=kicadFileHandler, polygonpoints=geom))
                    # node_points_sexpr.append(SexprSerializer.NEW_LINE)
                elif isinstance(geom, PolygonArc):
                    node_points_sexpr.append(
                        kicadFileHandler._serialize_PolygonArc(geom))
                    # node_points_sexpr.append(SexprSerializer.NEW_LINE)
                else:
                    node_points_sexpr.append(
                        kicadFileHandler._callSerialize(geom))
                    # node_points_sexpr.append(SexprSerializer.NEW_LINE)

            sexpr = [SexprSerializer.Symbol('fp_poly'),
                 # SexprSerializer.NEW_LINE,
                 node_points_sexpr,
                 # SexprSerializer.NEW_LINE,
                 [SexprSerializer.Symbol('stroke')] + kicadFileHandler._serialize_Stroke(node),
                 [SexprSerializer.Symbol('fill'), SexprSerializer.Symbol(node.fill)],
                 [SexprSerializer.Symbol('layer'), SexprSerializer.Symbol(node.layer)],
                 # SexprSerializer.NEW_LINE,
                ]  # NOQA

            if node.hasValidTStamp():
                sexpr.append(kicadFileHandler._serialize_TStamp(node))

            return sexpr

        else:  # kicad 7 does not (yet) support open polygons or polylines, therefore convert to virtual nodes
            # for all primitives (see getVirtualChilds, serialize_get_virtual_nodes )
            sexpr = []  # no serialization here, see childs
            group_ids = []

            return None

    def rotate(self, angle, origin=(0, 0), use_degrees=True):
        r""" Rotate polygon around given origin

        :params:
            * *angle* (``float``)
                rotation angle
            * *origin* (``Vector2D``)
                origin point for the rotation. default: (0, 0)
            * *use_degrees* (``boolean``)
                rotation angle is given in degrees. default:True
        """

        self.nodes.rotate(angle=angle, origin=origin, use_degrees=use_degrees)
        return self

    def translate(self, distance_vector):
        r""" Translate polygon

        :params:
            * *distance_vector* (``Vector2D``)
                2D vector defining by how much and in what direction to translate.
        """

        self.nodes.translate(distance_vector)
        return self

    def calculateBoundingBox(self):
        return self.nodes.calculateBoundingBox()

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)
        render_text += " [nodes: ["

        node_strings = []
        for n in self.nodes:
            node_strings.append("[x: {x}, y: {y}]".format(x=n.x, y=n.y))

        if len(node_strings) <= 6:
            render_text += ", ".join(node_strings)
        else:
            # display only a few nodes of the beginning and the end of the polygon line
            render_text += ", ".join(node_strings[:3])
            render_text += ",... , "
            render_text += ", ".join(node_strings[-3:])

        render_text += "]"

        return render_text

    def cut(self, other):
        r""" Cut other polygon from this polygon

        More details see PolygonPoints.cut docstring.

        :param other: the other polygon
        """
        self.nodes.cut(other.nodes)
