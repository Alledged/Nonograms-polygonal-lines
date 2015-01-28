# script calucates the minimum bounding box for a convex
# polygon in order to get the width

import math
from shapely.geometry import Polygon
import shapely.affinity
import DCEL



def calculate_width(face):
    """Calculates the width of a DCEL.face object and returns it"""
    edges = face.getOuterBoundary()
    vertices = [] # list of tuples of coordinates 
    for edge in edges:
        vertices.append(edge.getOrigin().getCoords()) 
    # construct polygon 
    polygon = Polygon(vertices) 
    width = 1000
    for i in range(len(vertices)):
        if i == len(vertices) - 1:
            orientation = math.atan2(vertices[i][1]-vertices[0][1],vertices[i][0]-vertices[0][0])
        else:
            orientation = math.atan2(vertices[i+1][1]-vertices[i][1], vertices[i+1][0]-vertices[i][0])
    
        poly_new = shapely.affinity.rotate(polygon, -1.0*orientation, polygon.centroid, use_radians=True)
        minx, miny, maxx, maxy = poly_new.bounds
        x_l = maxx-minx
        y_l = maxy-miny
        if x_l < y_l and x_l < width:
            width = x_l
        elif y_l < x_l and y_l < width:
            width = y_l
        elif y_l == x_l and y_l < width:
            width = y_l
    return width 
    

