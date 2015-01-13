import geomutil
import DCEL
import Point
from RedBlackTree import RedBlackTree as Tree

try:
    set                                # Python 2.4 or later
except:
    try:
        from sets import Set as set    # Python 2.3 compatibility
    except:
        raise RuntimeError('cannot find set class')

def segmentCmp(A,B):
    """Left to right (presuming that they share a common horizontal sweepline).

    A should be either a point or a tuple of two points (representing a segment)

    B should be a tuple of two points
    """
    if not isinstance(B,tuple) or len(B) !=2 or \
       not isinstance(B[0],Point.Point) or not isinstance(B[1],Point.Point):
        raise TypeError('B must be a tuple of two Point instances')
    if isinstance(A, tuple):
        orientA = geomutil.checkLineLine(A[0], A[1], B[0], B[1])
        orientB = geomutil.checkLineLine(B[0], B[1], A[0], A[1])
        if orientA == 'colinear':
            return 0
        elif orientA == 'left' or orientB == 'right':
            return -1
        elif orientA == 'right' or orientB == 'left':
            return +1
        else:
            # they cross each other
            # rely on the fact that first endpoint is higher endpoint
            if geomutil.leftTurn(B[1],B[0],A[0]):
                # A's upper endpoint is to the left of B
                answer = -1
            else:
                answer = +1
                
            return answer

    elif isinstance(A, Point.Point):
        orientation = geomutil.checkPointLine(A, B[0], B[1])
        if orientation == 'left':
            answer = -1   # point is left of segment
        elif orientation == 'right':
            answer = +1
        else:
            answer = 0   # point is on (or at least colinear with) line
        return answer

def checkForIntersection(startA, endA, startB, endB, currentPt):
    result = None
    try:
        intersection = geomutil.intersection(startA,endA,startB,endB)
        # only interested in intersections that are below currentPt, but on or above the two endpoints
        if geomutil.verticalCmp(intersection,currentPt) > 0 and \
           geomutil.verticalCmp(intersection,endA) <= 0 and \
           geomutil.verticalCmp(intersection,endB) <= 0:
            result = intersection   # only interested in intersections that are below currentPt
    except ValueError:
        pass   # might have been parallel

    return result

# serves as comparator for edges with a common origin
class EdgeByAngle:
    def __init__(self, origin):
        self._cmp = geomutil.AngleComparator(origin)

    def __call__(self, tupleA, tupleB):
        return self._cmp(tupleA[1],tupleB[1])

def buildGeneralSubdivision(edges, isolatedVertices=[]):
    """Constructs and returns a DCEL structure for an aribtrary collection of edges and vertices.

    edges             a sequence of edges, represented as (P,Q) tuples
                      for Point instances P and Q.
    
    isolatedVertices  a sequence of Point instances.
    """
    d = DCEL.DCEL()
    allEdges = []
    isolatedVertices = []

    events = Tree(geomutil.verticalCmp)    # key is Point;  data is sequence of downward endpoints

    sweep = Tree(segmentCmp)   # entries will have (startPt, endPt) key and
                               # associated data is (halfedge,endPt) for downward trajectory halfedge

    for pt in isolatedVertices:
        events.insert(v,[])

    for e in edges:
        top,bottom = e[0], e[1]
        if geomutil.verticalCmp(top,bottom) > 0:
            top,bottom = bottom,top
        try:
            existing = events.find(top)
            existing.append(bottom)      # bottom is associated data to indicate end of edge
        except KeyError:
            events.insert(top, [bottom]) # new event point

        if bottom not in events:
            events.insert(bottom, [])    # no associated data for bottom event

    while events:
        pt,data = events.removeMin()
        oldEdges = []
        newEdges = [end for end in data if end is not None]
        allOutgoing = []   # will consist of (edge,otherPt) tuples

        # first remove from sweepline those existing edges that contain this point
        matches = sweep.findAll(pt)
        for m in matches:
            sweep.remove(m[0])
            oldEdges.append(m[1])

        # with incident edges removed, find the remaining edges (if any) that surround it on sweepline
        leftNeigh = sweep.findLow(pt)
        rightNeigh = sweep.findHigh(pt)

        # need and official Vertex instance for this point
        v = DCEL.Vertex(pt)
        if leftNeigh is not None:
            v.setData(DCEL.visibilityTracker(leftNeigh[1][0]))    # keep track of the edge visibile toward left

        # set final destination for Edge structures incident from above
        for e,end in oldEdges:
            e.getTwin().setOrigin(v)
            allOutgoing.append((e.getTwin(),e.getOrigin().getCoords()))
            if end != pt:
                newEdges.append(end)   # lower portion of this edge must still be inserted

        # (re)insert sweepline segments for edges that go downward from this vertex

        newEdges.sort(geomutil.AngleComparator(pt))  # sort counterclockwise

        for end in newEdges:
            downward = DCEL.Edge()
            upward = DCEL.Edge()
            allEdges.append(downward)
            allEdges.append(upward)
            downward.setOrigin(v)
            downward.setTwin(upward)
            upward.setTwin(downward)
            sweep.insert( (pt,end), (downward,end))
            allOutgoing.append((downward,end))

        if len(allOutgoing) > 0:
            allOutgoing.sort(EdgeByAngle(pt))   #  order all incident edges in counterclockwise order
            v.setIncidentEdge(allOutgoing[0][0])
            for i in range(len(allOutgoing)):
                # properly connect i and i-1  (knowing that when i=0, i-1 is last edge)
                allOutgoing[i-1][0].setPrev(allOutgoing[i][0].getTwin())
                allOutgoing[i][0].getTwin().setNext(allOutgoing[i-1][0])

            # final issue is to look for any intersections between new neighbors on sweepline
            if newEdges:
                # compare leftmost new to leftNeigh and rightmost new to rightNeigh
                if leftNeigh is not None:
                    newEvent = checkForIntersection(leftNeigh[0][0],leftNeigh[0][1],
                                                    pt,newEdges[0],pt)
                    if newEvent is not None and newEvent not in events:
                        events.insert(newEvent,[])
    
                if rightNeigh is not None:
                    newEvent = checkForIntersection(rightNeigh[0][0], rightNeigh[0][1],
                                                    pt,newEdges[-1],pt)
                    if newEvent is not None and newEvent not in events:
                        events.insert(newEvent,[])
            else:
                # no edges below point;  compare leftNeigh and rightNeigh to each other
                if leftNeigh is not None and rightNeigh is not None:
                    newEvent = checkForIntersection(leftNeigh[0][0], leftNeigh[0][1],
                                                    rightNeigh[0][0], rightNeigh[0][1],pt)
                    if newEvent is not None and newEvent not in events:
                        events.insert(newEvent,[])
        else:
            isolatedVertices.append(v)

    # run algorithm to determine Faces
    d.rebuildFaces(allEdges,isolatedVertices)
    return d
