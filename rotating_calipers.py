# code from http://code.activestate.com/recipes/117225-convex-hull-and-diameter-of-2d-point-sets/

# convex hull (Graham scan by x-coordinate) and diameter of a set of points
# David Eppstein, UC Irvine, 7 Mar 2002

from __future__ import generators
from math import sqrt

def orientation(p,q,r):
    """docstring for orientation"""
    return (q[1]-p[1])*(r[0]-p[0]) - (q[0]-p[0])*(r[1]-p[1])

def hulls(points):
    """docstring for hulls"""
    U = []
    L = []
    points.sort()
    for p in points:
        while len(U) > 1 and orientation(U[-2],U[-1],p) <= 0:
            U.pop()
        while len(L) > 1 and orientation(L[-2],L[-1],p) >= 0:
            L.pop()
        U.append(p)
        L.append(p)
    return U,L

def rotating_calipers(points):
    """docstring for rotating_calipers"""
    U,L = hulls(points)
    i = 0
    j = len(L)-1
    while i < len(U) - 1 or j > 0:
        yield U[i],L[j]

        if i == len(U) - 1:
            j -= 1
        elif j == 0:
            i += 1
        elif (U[i+1][1]-U[i][1])*(L[j][0]-L[j-1][0])>(L[j][1]-L[j-1][1])*(U[i+1][0]-U[i][0]):
            i += 1
        else:
            j -= 1

def diameter(points):
    """docstring for diameter, change from the original 
    method, I am using the square root distance"""
    diam,pair = min([(sqrt((p[0]-q[0])**2 + (p[1]-q[1])**2),(p,q))
        for p,q in rotating_calipers(points)])
    return diam, pair
