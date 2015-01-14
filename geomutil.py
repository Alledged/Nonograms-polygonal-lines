import Point
import Rational


def intersection(a, b, c, d):
    """Compute point at which line defined by points a and b intersects line defined by c and d."""
    # define p parametrically as a*t - b*(1-t) and
    # then solve for t based on ratio of vectors cp and cd.
    
    # if statement checking the type of a, b, c, d and converting if necessary
    if(not isinstance(a, Point.Point)):
        # a is a vertex
        #print "convert a to Point"
        a = Point.Point((a.getCoords()[0], a.getCoords()[1]))

    if(not isinstance(b, Point.Point)):
        # b is a vertex
        #print "convert b to Point"
        b = Point.Point((b.getCoords()[0], b.getCoords()[1]))


    #print "is a instance of Point: ", isinstance(a, Point.Point)
    #print "is b instance of Point: ", isinstance(b, Point.Point)
    

    t = Rational.Rational( (c[1]-b[1])*(c[0]-d[0]) + (b[0]-c[0])*(c[1]-d[1]),
                           (b[0]-a[0])*(c[1]-d[1]) + (a[1]-b[1])*(c[0]-d[0]) )
        
    if t.isUndefined():
        #raise ValueError('lines are parallel')
        # own change
        return None
    else:
        p = a*t + b*(1-t)
        return p

def checkLinearity(firstPt, secondPt, thirdPt):
    """Consider turn in two dimensions when moving from firstPt to secondPt and then to thirdPt.

    Return value is:
        'left'     when thirdPt is left of travel
        'right'    when thirdPt is right of travel
        'forward'  when thirdPt is forward of travel
        'between'  when thirdPt is between first and second
        'behind'   when thirdPt is behind the first

    TypeError raised if these are not two-dimensional points.
    ValueError raised if firstPt equal secondPt.
    """
    if len(firstPt) == len(secondPt) == len(thirdPt) == 2:
        if firstPt == secondPt:
            raise ValueError('second point must be distinct from first')
        firstLeg = secondPt - firstPt
        secondLeg = thirdPt - secondPt
        area = firstLeg[0]*secondLeg[1] - firstLeg[1]*secondLeg[0]
        if area > 0:
            return 'left'
        elif area < 0:
            return 'right'
        elif firstLeg[0]*secondLeg[0] > 0 or firstLeg[1]*secondLeg[1] > 0:
            return 'forward'
        elif firstLeg.normPower() >= secondLeg.normPower():
            return 'between'
        else:
            return 'behind'
    else:
        raise TypeError('Only defined in two dimensions')
            
def leftTurn(firstPt, secondPt, thirdPt):
    """Returns True if a strict left turn, False if colinear or right turn."""
    return checkLinearity(firstPt, secondPt, thirdPt) == 'left'

def rightTurn(firstPt, secondPt, thirdPt):
    """Returns True if a strict right turn, False if colinear or left turn."""
    return checkLinearity(firstPt, secondPt, thirdPt) == 'right'

def colinear(firstPt, secondPt, thirdPt):
    """Returns True if three points are colinear, False otherwise."""
    return checkLinearity(firstPt, secondPt, thirdPt) in ('forward','between','behind')

def colinearForward(firstPt, secondPt, thirdPt):
    """Returns True if three points are colinear with thirdPt beyond secondPt relative to firstPt."""
    return checkLinearity(firstPt, secondPt, thirdPt) == 'forward'

def colinearBetween(firstPt, secondPt, thirdPt):
    """Returns True if three points are colinear with thirdPt between firstPt and secondPt (or equal to)."""
    return checkLinearity(firstPt, secondPt, thirdPt) == 'between'

def colinearBackward(firstPt, secondPt, thirdPt):
    """Returns True if three points are colinear with thirdPt behind firstPt relative to secondPt."""
    return checkLinearity(firstPt, secondPt, thirdPt) == 'backward'


#########################################################################################

def verticalCmp(A, B):
    """A comparator for points, ordering from top to bottom, with tie-breaker left-to-right.

    Based on this ordering, returns -1 if A "above" B,  0 if A == B, +1 if A "below" B.
    """
    # MINE -> check if A and B are not None
    if(A and B):
        primary = -cmp(A[1],B[1])    # bigger Y should come earlier in order
        if primary == 0:
            return cmp(A[0],B[0])
        return primary

#########################################################################################

def checkPointLine(pt, linePtA, linePtB):
    """Checks with Point pt is "left", "on", or "right" of a line.

    linePtA and linePtB determine the line.  In case of a horizontal
    line, the"left" will be below the line by convention.
    """
    if linePtA == linePtB:
        raise ValueError('points defining a line must be distinct.')
    if verticalCmp(linePtA, linePtB) > 0:
        linePtA,linePtB = linePtB,linePtA
    # now linePtA is guaranteed to be the higher one
    orient = checkLinearity(linePtB,linePtA,pt)
    if orient == 'left':
        return orient
    elif orient == 'right':
        return orient
    else:
        return 'on'
    
#########################################################################################

def checkLineLine(segA, segB, lineA, lineB):
    """Checks whether segment is "left", "right", "cross" or "colinear" relative to line.

    In case line is norizontal, its "left" is below the line by convention.
    """
    orientA = checkPointLine(segA,lineA,lineB)
    orientB = checkPointLine(segB,lineA,lineB)
    if orientA == orientB == "on":
        return "colinear"
    elif orientA == 'left':
        if orientB == 'right':
            return 'cross'
        else:
            return 'left'
    elif orientA == 'on':
        return orientB   # must be 'left' or 'right'
    else:   # orientA == 'right'
        if orientB == 'left':
            return 'cross'
        else:
            return 'right'

#########################################################################################

# based on viewpoint from reference to origin to dataPt
_regionOrder = {'between':0, 'behind':1, 'right':2, 'forward':3, 'left':4}
_regionFlipped = {'between':0, 'behind':1, 'left':2, 'forward':3, 'right':4}

class AngleComparator:
    """An instance is a callable object determining how two points compare in order relative to a given ray."""
    def __init__(self, origin, reference=None, useCounterClockwise=True):
        """Creates the comparator.

        origin is presumed to be a 2D point that serves as the center of the rotation.
        reference is presumed to be a different 2D point defining starting direction.

        Order is counterclockwise around origin by default.

        By default, reference is set to be vertically above origin.
        ValueError is raised of reference == origin.
        """
        if reference is None:
            reference = origin + Point.Point2D(0,1)
        if origin == reference:
            raise ValueError('reference point cannot be same as origin')
        self._origin = origin
        self._ref = reference
        if useCounterClockwise:
            self._flip = 1
        else:
            self._flip = -1

    def useClockwise(self):
        """Uses clockwise ordering about the origin."""
        self._flip = -1

    def useCounterClockwise(self):
        """Uses counterclockwise ordering about the origin."""
        self._flip = 1

    def __call__(self, A, B):
        """A comparator for angular order, returing -1 if A < B, 0 if identical, +1 if A > B.

        When angle from origin to A differs from that to B, ordering
        is natural.  In the case when A, B, and origin are colinear, A
        is considered less than B if it is nearer to origin.
        """
        if A == B:
            answer = 0  # only case where we will do so
        elif A == self._origin:
            answer = -1
        else:
            checkA = checkLinearity(self._ref, self._origin, A)
            checkB = checkLinearity(self._ref, self._origin, B)
            if checkA != checkB:
                # different halfplanes
                if self._flip == -1:
                    answer = cmp(_regionFlipped[checkA],_regionFlipped[checkB])
                else:
                    answer = cmp(_regionOrder[checkA],_regionOrder[checkB])
            else:
                # same halfplane
                finalCheck = checkLinearity(A,self._origin,B)
                if finalCheck == 'right':
                    answer = -1 * self._flip
                elif finalCheck == 'left':
                    answer = +1 * self._flip
                else:   # colinear
                    answer = cmp( (self._origin-A).normPower(), (self._origin-B).normPower())

        return answer


#########################################################################################

def angleKey(A, B, C=Point.Point(0,0)):
    """Using line BC as the reference, returns a key which can be used for sorting A by angle of BA.

    Primary order is between, forward, left, behind, right.
    Ties are broken by length of AB, from shortest to longest.
    """
    if B == C:
        raise ValueError('second and third points cannot be equal')
    if len(A) == len(B) == len(C) == 2:
        firstLeg = B - A
        secondLeg = C - B
        firstNorm = firstLeg.normPower()
        secondNorm = secondLeg.normPower()
        area = Rational.Rational(firstLeg[0]*secondLeg[1] - firstLeg[1]*secondLeg[0])
        if area > 0:
            dot = Rational.Rational(firstLeg * secondLeg)
            if dot < 0:
                sign = -1
            else:
                sign = 1
            return (2, sign * (dot * dot) / (firstNorm*secondNorm), firstNorm)
        elif area < 0:
            dot = Rational.Rational(firstLeg * secondLeg)
            if dot < 0:
                sign = -1
            else:
                sign = 1
            return (4, -sign * (dot * dot) / (firstNorm*secondNorm), firstNorm)
        elif firstLeg[0]*secondLeg[0] > 0 or firstLeg[1]*secondLeg[1] > 0:
            return (3, firstNorm)     # A is behind BC
        elif firstNorm >= secondNorm:
            return (1, firstNorm)     # A is forward beyond BC
        else:
            return (0, firstNorm)     # A is between B and C
    else:
        raise ValueError('Only defined in two dimensions')


#########################################################################################

if __name__ == '__main__':
    a = Point.Point(0,0)
    b = Point.Point(2,0)
    c = Point.Point(2,2)
    d = Point.Point(0,2)
    e = Point.Point(5,0)
    
    if not checkLinearity(a,b,c) == 'left':
        print 'error: checkLinearity(a,b,c) returned', checkLinearity(a,b,c)
    if not checkLinearity(a,b,d) == 'left':
        print 'error: checkLinearity(a,b,d) returned', checkLinearity(a,b,d)
    if not checkLinearity(a,b,a) == 'between':
        print 'error: checkLinearity(a,b,a) returned', checkLinearity(a,b,a)
    if not checkLinearity(a,b,b) == 'between':
        print 'error: checkLinearity(a,b,b) returned', checkLinearity(a,b,b)
    if not checkLinearity(a,b,e) == 'forward':
        print 'error: checkLinearity(a,b,e) returned', checkLinearity(a,b,e)
    if not checkLinearity(a,c,b) == 'right':
        print 'error: checkLinearity(a,c,b) returned', checkLinearity(a,c,b)
    if not checkLinearity(a,c,e) == 'right':
        print 'error: checkLinearity(a,c,e) returned', checkLinearity(a,c,e)
    if not checkLinearity(a,c,d) == 'left':
        print 'error: checkLinearity(a,c,d) returned', checkLinearity(a,c,d)
        
    import Plot2D
    import RandomGeom
    import cs1graphics
    import time
    n = 25
    scale = 1000
    center = Point.Point(scale//2, scale//2)
    radius = 400
    gen = RandomGeom.RandomGeom()
    points = gen.randPointSetInBall(n, center, radius)
    (can,view) = Plot2D.Plot2D(points, 800, 800)
    
    origin = points.pop()
    ref = points[0]
    path = cs1graphics.Path(cs1graphics.Point(origin[0],origin[1]),cs1graphics.Point(ref[0],ref[1]))
    path.setBorderColor('red')
    path.setDepth(1)
    view.add(path)

    order = [ (angleKey(p,origin,ref), p) for p in points]
    order.sort()

    for junk,p in order:
        for i in junk: print i,
        print
        path = cs1graphics.Path(cs1graphics.Point(origin[0],origin[1]),cs1graphics.Point(p[0],p[1]))
        time.sleep(0.5)
        view.add(path)
