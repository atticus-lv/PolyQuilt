# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import bmesh
import math
import copy
import mathutils
import collections
from mathutils import *
from ..utils import pqutil
from ..utils import draw_util
from ..utils.dpi import *

__all__ = ['ElementItem']

class EmptyElement :
    def __init__(self) :
        pass

    @property
    def index(self) -> int :        
        return 0

    @property
    def verts(self): 
        return []

class ElementItem :
    def __init__(self , qmesh , element : bmesh.types.BMVert , coord : Vector, hitPosition : Vector , dist = 0 ) :
        self.__type = type(element)
        self.__index = element.index
        self.__element = element
        self.__hitPosition: Vector = copy.copy(hitPosition)
        self.__coord: Vector = copy.copy(coord)
        self.__dist: float = dist
        self.__mirror = None
        self.__qmesh = qmesh
        self.__mirror = None
        self.__div = 0
        self.setup_mirror()

    def setup_mirror( self ) :
        if self.__qmesh is not None :
            is_mirror_mode = self.__qmesh.is_mirror_mode
            if self.__qmesh.is_mirror_mode :
                self.__mirror = self.__qmesh.find_mirror( self.element )
        else :
            self.__mirror = None

    def set_snap_div( self , div : int ) :
        self.__div = div
        if self.isEdge :
            p0 = self.__element.verts[0].co
            p1 = self.__element.verts[1].co
            dic = [ ( self.__coord - self.__qmesh.local_to_2d( p0.lerp( p1 , (i+1.0) / (div + 1.0) ) ) ).length for i in range(div ) ]
            if div > 0 :
                val = None
                dst = 1000000
                for i in range(div ) :
                    r = (i+1.0) / (div + 1.0)
                    p = p0.lerp( p1 , r )
                    v = self.__qmesh.local_to_2d( p )
                    l = ( self.__coord - v ).length
                    if l <= self.__qmesh.preferences.distance_to_highlight* dpm() :
                        if dst > l :
                            dst = l
                            val = p
                if val :
                    self.__hitPosition = self.__qmesh.local_to_world_pos(val)
                    self.__coord = self.__qmesh.world_to_2d( self.__hitPosition )

    @property
    def index(self):
        return self.__index

    @property
    def element(self):
        if self.isEdge :
            return self.__element if self.is_valid else None
        elif self.isVert :
            return self.__element if self.is_valid else None
        elif self.isFace :
            return self.__element if self.is_valid else None
        return None

    @property
    def mirror(self):
        return self.__mirror

    @property
    def hitPosition(self) -> Vector :
        return copy.copy(self.__hitPosition)

    @hitPosition.setter
    def hitPosition(self , value : Vector ) -> Vector :
         self.__hitPosition = copy.copy(value)

    @property
    def coord(self) -> Vector :
        return copy.copy(self.__coord)

    @property
    def normal(self) -> Vector :
        if self.isVert :
            return self.element.normal
        if self.isEdge :
            return ( self.element.verts[0].normal + self.element.verts[1].normal ) * 0.5
        if self.isFace :
            return self.element.normal

        return Vector(1,0,0)

    @property
    def dist(self) -> float:
        return self.__dist

    @property
    def isEmpty(self) -> bool:
        return self.type == EmptyElement

    @property
    def isNotEmpty(self) -> bool :
        return self.type != EmptyElement

    @property
    def is_valid(self) -> bool :
        if self.isEdge :
            return self.__element.is_valid and self.__element in self.__qmesh.bm.edges
        elif self.isVert :
            return self.__element.is_valid and self.__element in self.__qmesh.bm.verts
        elif self.isFace :
            return self.__element.is_valid and self.__element in self.__qmesh.bm.faces

        return True

    @property
    def isVert(self) -> bool :
        return self.type == bmesh.types.BMVert

    @property
    def isEdge(self) -> bool :
        return self.type == bmesh.types.BMEdge

    @property
    def isFace(self) -> bool :
        return self.type == bmesh.types.BMFace

    @property
    def is_x_zero(self) -> bool :
        dist = bpy.context.scene.tool_settings.double_threshold
        return all( [ abs(v.co.x) < dist for v in self.verts ] )

    @property
    def is_straddle_x_zero(self) -> bool :
        if self.__qmesh.is_mirror_mode and self.__mirror == None and self.element != None :
            if self.element == self.__qmesh.find_mirror( self.element , False ) :
                return True
        return False

    @property
    def verts( self ) -> bmesh.types.BMVert:
        if self.isEmpty :
            return []
        elif self.isVert :
            return [self.element]
        else :
            return self.element.verts

    @property
    def mirror_verts( self ) -> bmesh.types.BMVert:
        if self.__mirror is None :
            return []
        elif isinstance( self.__mirror , bmesh.types.BMVert ) :
            return [self.__mirror]
        else :
            return self.__mirror.verts

    @property
    def type(self):
        return self.__type

    @staticmethod
    def Empty():
        return ElementItem( None , EmptyElement() , None , None , 0.0 )

    @staticmethod
    def FormVert( qmesh , v ):
        p = pqutil.location_3d_to_region_2d( v.co )
        return ElementItem( qmesh , v , p , qmesh.local_to_world_pos(v.co) , 0.0 )

    @staticmethod
    def FormElement( qmesh ,e , co ):
        p = pqutil.location_3d_to_region_2d( co )
        return ElementItem( qmesh ,e , p , co , 0.0 )

    def Draw( self , obj , color , preferences , marker = False ) :
        if self.is_valid :
            size = preferences.highlight_vertex_size
            width = preferences.highlight_line_width
            alpha = preferences.highlight_face_alpha
            element = self.element
            draw_util.drawElementHilight3D( obj , element , size , width ,alpha, color )
            if self.isEdge :
                div_col = ( color[0] , color[1] , color[2] , color[3] * 0.5 )
                for i in range(self.__div) :
                    r = (i+1.0) / (self.__div + 1.0)
                    v = self.__qmesh.local_to_world_pos( element.verts[0].co.lerp( element.verts[1].co , r) )
                    draw_util.draw_pivots3D( (v,) , 0.75 , div_col )                
                draw_util.draw_pivots3D( (self.hitPosition,) , 1.0 , color )
                if marker and len(element.link_faces) <= 1 :
                    self.draw_extrude_marker()

            if self.mirror is not None and self.mirror.is_valid :
                color = ( color[0] , color[1] ,color[2] ,color[3] * 0.5 )
                draw_util.drawElementHilight3D( obj , self.mirror , size , width ,alpha , color )

    def draw_extrude_marker( self ) :
        element = self.element    
        with draw_util.push_pop_projection2D() :
            p1 = pqutil.location_3d_to_region_2d( self.hitPosition )
            v0 = pqutil.location_3d_to_region_2d(  self.__qmesh.local_to_world_pos(element.verts[0].co) )
            v1 = pqutil.location_3d_to_region_2d(  self.__qmesh.local_to_world_pos(element.verts[1].co) )
            length = (v0-v1).length
            center = ((v0 + v1 ) / 2)
            vec = (v1 - v0 ).normalized()
            norm = (mathutils.Matrix.Rotation(math.radians(90.0), 2, 'Z') @ vec).normalized()
            radius = min( [ length / 10 , dpm() * 4 ] )

            tangents = []
            for face in element.link_faces :
                for loop in [ l for l in face.loops if l.edge == element ]:
                    tangent = element.calc_tangent( loop )
                    p = pqutil.location_3d_to_region_2d(  self.__qmesh.local_to_world_pos (element.verts[0].co + tangent ) )
                    tangents.append( (p - v0).normalized() )

            can_extrude = False
            if len( [ t for t in tangents if t.dot( norm ) > 0 ] ) <= 0 :
                offset = center + norm * 2 * dpm()
                if (p1 - center).length <= radius :
                    vs = [ offset + vec * radius , offset - vec * radius , offset + norm * radius ]
                    draw_util.draw_poly2D( vs , (1,1,1,1) )
                else :
                    radius = radius * 0.9
                    vs = [ offset + vec * radius , offset - vec * radius , offset + norm * radius , offset + vec * radius ]
                    draw_util.draw_lines2D( vs , (1,1,1,0.5) , 1.0 )
                    can_extrude = True

            if len( [ t for t in tangents  if t.dot( norm ) < 0 ] ) <= 0 :
                offset = center - norm * 2 * dpm()
                if (p1 - center).length <= radius :
                    vs = [ offset + vec * radius , offset - vec * radius , offset - norm * radius ]
                    draw_util.draw_poly2D( vs , (1,1,1,1) )
                else :
                    radius = radius * 0.9
                    vs = [ offset + vec * radius , offset - vec * radius , offset - norm * radius , offset + vec * radius ]
                    draw_util.draw_lines2D( vs , (1,1,1,0.5) , 1.0 )
                    can_extrude = True
        return can_extrude

    def can_extrude( self ) :
        element = self.element            
        if self.isEdge and len(element.link_faces) <= 1 :            
            p1 = pqutil.location_3d_to_region_2d( self.hitPosition )
            v0 = pqutil.location_3d_to_region_2d(  self.__qmesh.local_to_world_pos(element.verts[0].co) )
            v1 = pqutil.location_3d_to_region_2d(  self.__qmesh.local_to_world_pos(element.verts[1].co) )
            length = (v0-v1).length
            center = ((v0 + v1 ) / 2)
            vec = (v1 - v0 ).normalized()
            norm = (mathutils.Matrix.Rotation(math.radians(90.0), 2, 'Z') @ vec).normalized()
            radius = min( [ length / 10 , dpm() * 5 ] )

            return (p1 - center).length <= radius
        return False

