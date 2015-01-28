from Point import Point
import Rational
import geomutil
import matplotlib.pyplot as plt

# mine!
# list of 2D tuples of DCEL.Vertex points
BOUNDING_X = [-200, 200, 200, -200, -200]
BOUNDING_Y = [200, 200, -200, -200, 200]

try:
    set                                # Python 2.4 or later
except:
    try:
        from sets import Set as set    # Python 2.3 compatibility
    except:
        raise RuntimeError('cannot find set class')


"""Support for maintaining a planar subdivision.

Implemented using a doubly-connected edge list representation.

(we use notation from de Berg, van Kreveld, Overmars and Schwarzkopf,
although object-oriented)
"""

class Vertex:
    """Represents a vertex of the subdivision."""
    def __init__(self, coordinates, auxData=None):
        """Create vertex.

        Coordinates can be specified as a Point instance or a tuple.

        auxData can be anything (default None)
        """
        try:
            self._coords = Point(coordinates)
        except:
            raise TypeError('invalid coordinates')
        self._data = auxData
        self._edge = None

    def __hash__(self):
        """Allow vertex to serve as key of set or dictionary."""
        return hash(id(self))
#        return hash((self._coords[0], self._coords[1], id(self)))

    def getCoords(self):
        """Returns coordinates in the form of a Point instance copy."""
        return Point(self._coords)

    def setCoords(self):
        """
        Coordinates can be specified either as a Point instance or a tuple.
        """
        try:
            self._coords = Point(coordinates)
        except:
            raise TypeError('invalid coordinates')

    def getData(self):
        """Returns auxillary data."""
        return self._data

    def setData(self, auxData):
        """Sets auxillary data."""
        self._data = auxData

    def getIncidentEdge(self):
        """Returns an incident edge for this vertex (or else None)."""
        return self._edge
        
    def setIncidentEdge(self, edge):
        """Sets this vertex's incedent edge."""
        if not isinstance(edge,Edge):
            raise TypeError('parameter must be an Edge instance')
        self._edge = edge

    def getOutgoingEdges(self):
        """Returns a list of outgoing edges, ordered counterclockwise."""
        visited = set()
        out = []
        here = self._edge
        while here and here not in visited:
            out.append(here)
            visited.add(here)
            temp = here.getTwin()
            if temp:
                here = temp.getNext()
            else:  # inconsistency
                here = None
        return out

    def __repr__(self):
        return 'DCEL.Vertex with coords ' + str(self.getCoords())

class Edge:
    """Represents a (half) edge of the subdivision."""
    def __init__(self, auxData=None):
        """Creates edge structure."""
        self._data = auxData
        self._twin = None
        self._origin = None
        self._face = None
        self._next = None
        self._prev = None

    def __hash__(self):
        """Allow edge to serve as key of set or dictionary."""
        return hash(id(self))

    def getData(self):
        """Returns auxillary data."""
        return self._data

    def setData(self, auxData):
        """Sets auxillary data."""
        self._data = auxData

    def getTwin(self):
        """Returns the half edge's twin edge."""
        return self._twin

    def setTwin(self, twin):
        """Sets this edge's twin (but not the twin's twin)."""
        if not isinstance(twin,Edge):
            raise TypeError('twin must be an Edge instance')
        self._twin = twin

    def getNext(self):
        """Returns the next edge along the incident face."""
        return self._next

    def setNext(self, edge):
        """Sets the next edge along the incident face."""
        if not isinstance(edge,Edge):
            raise TypeError('next must be an Edge instance')
        self._next = edge

    def getPrev(self):
        """Returns the prev edge along the incident face."""
        return self._prev

    def setPrev(self, edge):
        """Sets the prev edge along the incident face."""
        if not isinstance(edge,Edge):
            raise TypeError('prev must be an Edge instance')
        self._prev = edge

    def getOrigin(self):
        """Returns the edge's origin vertex."""
        return self._origin

    def setOrigin(self, v):
        """Sets this edge's origin to Vertex v."""
        if not isinstance(v,Vertex):
            raise TypeError('origin must be a Vertex instance')
        self._origin = v

    def getDest(self):
        """Returns the edge's (implicit) destination vertex."""
        return self._twin._origin

    def getFace(self):
        """Returns the edge's incident face."""
        return self._face

    def getFaceBoundary(self):
        """Returns a list of edges, starting with this edge, traveling counterclockwise around the face."""
        visited = set()
        boundary = []
        here = self
        while here and here not in visited:
            boundary.append(here)
            visited.add(here)
            here = here.getNext()
        return boundary

    def setFace(self, face):
        """Sets this edge's incident face."""
        if not isinstance(face,Face):
            raise TypeError('face must be a Face instance')
        self._face = face


    def clone(self):
        """Returns a "cloned" edge (though the clone is not incorporated into the larger subdivision."""
        c = Edge()
        c._data,c._twin,c._origin,c._face,c._next,c._prev = \
            self._data,self._twin,self._origin,self._face,self._next,self._prev
        
    def __repr__(self):
        return 'DCEL.Edge from ' + str(self.getOrigin().getCoords()) + \
               ' to ' + str(self.getDest().getCoords())

class Face:
    """Represents a face of the subdivision."""
    def __init__(self, part_of_drawing=None):
        # changed auxData to part_of_drawing ( a boolean variable )
        """Create face structure.

        auxData can be anything (default None)
        """

        # use auxData as boolean to check if part of the main drawing
        self._part_of_drawing = part_of_drawing
        self._outer = None
        self._inner = set()
        self._isolated = set()

    def __hash__(self):
        """Allow face to serve as key of set or dictionary."""
        return hash(id(self))

    #def getData(self):
    #    """Returns auxillary data."""
    #    return self._data

    #def setData(self, auxData):
    #    """Sets auxillary data."""
    #    self._data = auxData

    def get_is_part_of_drawing(self):
        return self._part_of_drawing

    def set_is_part_of_drawing(self, value):
        self._part_of_drawing = value

    def getOuterComponent(self):
        """Returns an edge of the outer boundary (or else None)."""
        return self._outer

    def setOuterComponent(self, edge):
        """Resets the representative edge for the outer boundary."""
        if not isinstance(edge,Edge):
            raise TypeError('parameter must be an Edge instance')
        self._outer = edge

    def getOuterBoundary(self):
        """Returns a list of edges, traveling counterclockwise around the face."""
        if self._outer:
            return self._outer.getFaceBoundary()
        else:
            return []

    def getInnerComponents(self):
        """Returns a list of edges, each of which is a representative for an inner component."""
        return list(self._inner)

    def addInnerComponent(self, edge):
        """Adds this edge to the set of inner components (if not already there)."""
        if not isinstance(edge,Edge):
            raise TypeError('parameter must be an Edge instance')
        self._inner.add(edge)

    def removeInnerComponent(self, edge):
        """Removes the given edge from the set of inner components (if present)."""
        if not isinstance(edge,Edge):
            raise TypeError('parameter must be an Edge instance')
        self._inner.discard(edge)

    def getIsolatedVertices(self):
        """Returns a list of vertices that are isolated within the face."""
        return list(self._isolated)

    def addIsolatedVertex(self,vertex):
        """Adds this vertex to the face (if not already there)."""
        if not isinstance(vertex,Vertex):
            raise TypeError('parameter must be a Vertex instance')
        self._isolated.add(vertex)

    def removeIsolatedVertex(self,vertex):
        """Removes the given vertex from the set of isolated vertices (if present)."""
        if not isinstance(vertex,Vertex):
            raise TypeError('parameter must be a Vertex instance')
        self._isolated.discard(vertex)

    # my method -> 
    def get_area(self):
        """returns the area of the self.face"""
        # find the vertices bounding the face through using the edges
        area = -1
        bounding_vertices_x = []
        bounding_vertices_y = []

        # identify all points bounding the face in counterclockwise order
        # and store their x and y coordinates in two lists
        edges = self.getOuterBoundary()
        for edge in edges:
            bounding_vertices_x.append(edge.getOrigin().getCoords()[0])
            bounding_vertices_y.append(edge.getOrigin().getCoords()[1])

        part_p, part_m = 0, 0
        for i_p, i_m in zip(range(len(bounding_vertices_x)), range(len(bounding_vertices_y))):
            if i_p == len(bounding_vertices_x) - 1:
                part_p += bounding_vertices_x[i_p]*bounding_vertices_y[0]
            else:
                part_p += bounding_vertices_x[i_p]*bounding_vertices_y[i_p+1]

            if i_m == len(bounding_vertices_y) - 1:
                part_m += bounding_vertices_x[0]*bounding_vertices_y[i_m]
            else:
                part_m += bounding_vertices_x[i_m + 1]*bounding_vertices_y[i_m]

        # using a rational number from the Rational class (1/2)
        total = Rational.Rational(1, 2) * (part_p - part_m)
        return total

    # my method
    def get_ordered_vertices(self):
        """returns the an ordered list of the vertices bounding the edge"""
        current_edge = self.getOuterComponent()
        
        vertices_x = []
        vertices_y = []
        ordered_verts = []
        if (current_edge):
            ordered_verts.append(current_edge.getOrigin())
            starting_edge = current_edge
            while current_edge.getDest() != starting_edge.getOrigin():
                current_edge = current_edge.getNext()
                ordered_verts.append(current_edge.getOrigin())
            else:
                ordered_verts.append(current_edge.getOrigin())
        
            vertices_x = [v.getCoords()[0] for v in ordered_verts]
            vertices_y = [v.getCoords()[1] for v in ordered_verts]
            vertices_x.append(vertices_x[0])
            vertices_y.append(vertices_y[0])

            return (vertices_x, vertices_y)

        else:
            # return the empty list ??
            "EMPTY FACE"
            return None
        

    def plot_face(self):
        """plot the self.face and the bounding box"""
        #plt.plot(BOUNDING_X, BOUNDING_Y)
        #plt.axis([-250, 250, -250, 250])
        
        verts = self.get_ordered_vertices()
        if(verts != None):
            plt.plot(verts[0], verts[1])
            plt.show()
        else:
            print "EMPTY FACE"

class _Queue:
    """Standard for a FIFO queue."""
    def __init__(self):
        self._size = 0
        self._front = 0
        self._data = [None] * 10

    def __len__(self):
        return self._size

    def getFront(self):
        if self._size == 0:
            raise RuntimeError('Queue is empty')
        else:
            return self._data[self._front]
        
    def push(self, obj):
        if self._size == len(self._data):
            # expand and copy data
            newdata = 2 * len(self._data) * [None]
            for i in range(self._size):
                newdata[i] = self._data[(self._front + i) % self._size]
            self._front = 0
            self._data = newdata
        # add new item
        self._data[(self._front + self._size) % len(self._data)] = obj
        self._size += 1

    def pop(self):
        if self._size == 0:
            raise RuntimeError('Queue is empty')
        obj = self._data[self._front]
        self._front = (1+self._front) % len(self._data)
        self._size -= 1
        return obj

class DCEL:
    """Represents the subdivision as a whole."""
    def __init__(self):
        """Creates a new subdivision.

        Initially, the subdivision has a single unbounded face and no edges or vertices.
        """
        self._exterior = Face()
        
    def getExteriorFace(self):
        """Return a reference to the original exterior face.
        """
        return self._exterior

    def getFaces(self):
        """Return a list of all faces.

        Guarantees that resulting list is ordered, starting with the
        external face, such that a hole occurs after its containing face.
        """
        # perform a search starting from exterior face
        result = []
        known = set()
        fringe = _Queue()
        fringe.push(self._exterior)
        known.add(self._exterior)
        while fringe:
            f = fringe.pop()
            result.append(f)

            for e in f.getOuterBoundary():
                neigh = e.getTwin().getFace()
                if neigh and neigh not in known:
                    known.add(neigh)
                    fringe.push(neigh)

            for inner in f.getInnerComponents():
                for e in inner.getFaceBoundary():
                    neigh = e.getTwin().getFace()
                    if neigh and neigh not in known:
                        known.add(neigh)
                        fringe.push(neigh)
        return result

    def getEdges(self):
        """Return a set/list of all edges."""
        edges = set()
        for f in self.getFaces():
            edges.update(f.getOuterBoundary())
            for inner in f.getInnerComponents():
                edges.update(inner.getFaceBoundary())
       # adding list() to return a list
        return list(edges)

    def getVertices(self):
        """Return a set/list of all vertices."""
        verts = set()
        for f in self.getFaces():
            verts.update(f.getIsolatedVertices())
            verts.update([e.getOrigin() for e in f.getOuterBoundary()])
            for inner in f.getInnerComponents():
                verts.update([e.getOrigin() for e in inner.getFaceBoundary()])
        # adding list() to return a list
        return list(verts)

    def rebuildFaces(self, allEdges, isolatedVertices=[]):
        """Reconstructs the implicit face complexes for the underlying edges.
        
        NOTE:  this causes any previously existing Face instances to be irrelevant.
    
        For this to work, the caller must guarantee one of two conditions:
        (1) That the overall edge structure is connected
    
        or
    
        (2) For any disconnected portion, the leftmost vertex on the
            bounding chain must have auxillary data that identifies the
            half-edge which is visibile immediately to its left.  This is
            done by having the vertex support a getData() object that
            itself supports a getVisibleEdge() method.
    
            Isolated vertices must also identify their left-visible edge.
        """
        # clean start
        self._exterior = face = Face()

        if allEdges:
            # start by finding leftmost vertex, which must lie on external boundary
            leftmost = allEdges[0]
            for e in allEdges:
                if e.getOrigin().getCoords() < leftmost.getOrigin().getCoords():
                    leftmost = e

            # make sure we have upward oriented half edge
            if geomutil.verticalCmp(e.getOrigin().getCoords(),e.getDest().getCoords()) < 0:
                e = e.getTwin()
    
            edgeSet = set(allEdges)
        
        
            # build up chains
            innerChains = []
            while edgeSet:
                chain = [edgeSet.pop()]
                leftmost = chain[0]
                while chain[-1].getNext() != chain[0]:
                    edgeSet.remove(chain[-1].getNext())
                    chain.append(chain[-1].getNext())
                    if chain[-1].getOrigin().getCoords() < leftmost.getOrigin().getCoords() \
                           or (chain[-1].getOrigin().getCoords() == leftmost.getOrigin().getCoords() and \
                               geomutil.verticalCmp(chain[-1].getDest().getCoords(),leftmost.getDest().getCoords()) < 0):
                        leftmost = chain[-1]

#                print 'CHAIN:'
#                for e in chain:
#                    print e
                    
                # we have a chain with an identified leftmost origin edge
                # determine if this is inner or outer chain
                if geomutil.leftTurn(leftmost.getPrev().getOrigin().getCoords(),
                                     leftmost.getOrigin().getCoords(),
                                     leftmost.getDest().getCoords()):
                    # this is OUTER boundary
                    f = Face()
                    f.setOuterComponent(leftmost)
                    for e in chain:
                        e.setFace(f)
                else:
                    # this is an INNER boundary;  table it for now
                    innerChains.append((leftmost.getOrigin().getCoords(),leftmost))  # decorated tuple
        
            
            innerChains.sort()     # process inner holes left to right (NOTE:  should really do toplogical sort)
        
            # now go back and assign inner boundaries based on the neighboring
            # information hidden in the vertex data
            for junk,inner in innerChains:      # undecorate
                leftmost = inner
        
                neighborEdge = None
                try:
                    neighborEdge = leftmost.getOrigin().getData().getVisibleEdge()
                except:
                    pass
    
                if neighborEdge is None:
                    face = self.getExteriorFace()
                else:
                    face = neighborEdge.getFace()
                    
                for e in inner.getFaceBoundary():
                    e.setFace(face)
                face.addInnerComponent(inner)
        
        
            for v in isolatedVertices:
                neighborEdge = None
                try:
                    data = v.getData().getVisibleEdge()
                except:
                    pass
                if neighbor is None:
                    face = self.getExteriorFace()
                else:
                    face = neighbor.getFace()
                face.addIsolatdVertex(v)


    def validate(self):
        """Throws an exception if inconsitency is detected.

        Note: the lack of an exception does not guarantee the lack of an undetected inconsistency.
        """
        for e in self.getEdges():
            if e.getTwin().getTwin() is not e:
                raise RuntimeError('edge '+str(e)+' found with inconsistent twin')
            if e not in e.getOrigin().getOutgoingEdges():
                raise RuntimeError('edge '+str(e)+" not found in origin's outgoing edges")
            if e.getPrev().getNext() is not e:
                raise RuntimeError('edge '+str(e)+' has prev '+str(e.getPrev())+' with inconsistent next')
            if e.getNext().getPrev() is not e:
                raise RuntimeError('edge '+str(e)+' has next '+str(e.getNext())+' with inconsistent prev')
            if e.getFace() is None:
                raise RuntimeError('edge '+str(e)+' has no incident face')
            
        for v in self.getVertices():
            for e in v.getOutgoingEdges():
                if e.getOrigin() is not v:
                    raise RuntimeError('vertex '+str(v)+' has inconsistent outgoing edge '+str(e))

        for f in self.getFaces():
            for e in f.getOuterBoundary():
                if e.getFace() is not f:
                    raise RuntimeError('edge '+str(e)+' found with inconsistent face '+str(f))
            for inner in f.getInnerComponents():
                for e in inner.getFaceBoundary():
                    if e.getFace() is not f:
                        raise RuntimeError('edge '+str(e)+' found with inconsistent face '+str(f))
            if f is not self.getExteriorFace() and f.getOuterComponent() is None:
                raise RuntimeError('non-exterior face '+str(f)+' found withough any outer component')

        # my method
    def plot_whole_dcel(self):
        """Plots the whole dcel and the bounding box"""
        #plt.plot(BOUNDING_X, BOUNDING_Y)
        #plt.axis([-250, 250, -250, 250])

        edges = self.getEdges()
        plt.axis([0, 15, 0, 15])
        for edge in edges:
            plt.plot([edge.getOrigin().getCoords()[0], edge.getDest().getCoords()[0]], 
            [edge.getOrigin().getCoords()[1], edge.getDest().getCoords()[1]]) # colour for each face may be changed
        plt.show()

def buildSimplePolygon(points):
    """Constructs and returns a DCEL structure for a simple polygon.

    points    a counterclockwise sequence of Point instances.
    """
    d = DCEL()
    if points:
        exterior = d.getExteriorFace()
        interior = Face()
        verts = []
        for p in points:
            verts.append(Vertex(p))

        innerEdges = []
        outerEdges = []
        for i in range(len(verts)):
            e = Edge()
            e.setOrigin(verts[i])
            verts[i].setIncidentEdge(e)
            e.setFace(interior)
            t = Edge()
            t.setOrigin(verts[(i+1)%len(verts)])
            t.setFace(exterior)
            t.setTwin(e)
            e.setTwin(t)
            innerEdges.append(e)
            outerEdges.append(t)

        for i in range(len(verts)):
            innerEdges[i].setNext(innerEdges[(i+1)%len(verts)])
            innerEdges[i].setPrev(innerEdges[i-1])
            outerEdges[i].setNext(outerEdges[i-1])
            outerEdges[i].setPrev(outerEdges[(i+1)%len(verts)])

        interior.setOuterComponent(innerEdges[0])
        exterior.addInnerComponent(outerEdges[0])   # polygon is a hole in the exterior region
    return d




class visibilityTracker:
    """Simple class that can be used as auxillary data when tracking visible edges.

    This is convenience for use with DCEL.rebuildFaces routine.
    """
    def __init__(self, leftVisibleEdge=None):
        self._visible = leftVisibleEdge

    def getVisibleEdge(self):
        return self._visible

from intersections import buildGeneralSubdivision   # implementation provided separately


try:
    import cs1graphics as _graphics

    class GraphicsData:
        """Sample class for DCEL auxillary data that can be used to control the rendered image of a feature."""
        def __init__(self, color='black'):
            self._color = color
            self._feature = None

        def getColor(self):
            return self._color

        def setColor(self,color):
            self._color = color


    def renderDCEL(dcel, randomColor=False, vertRadius=3, edgeWidth=2):
        """Generates a cs1graphics.Layer for the given DCEL.

        Returns a layer and a dictionary that can be used to lookup
        the graphics features associated with each DCEL feature.

        By default, faces are transparent.  When randomColor parameter
        is True, unspecified face colors are assigned randomly.

        If the auxillary data for a vertex happens to support a
        getColor method, that color is used (default black).

        If the auxillary data for an edge happens to support a
        getColor method, that color is used (default black).

        If the auxillary data for the face happens to support a
        getColor method, that color is used for interior (default Transparent).
        """
        def convertPoint(dcelPt):
            temp = dcelPt.getCoords()
            return _graphics.Point(float(temp[0]),float(temp[1]))

        edges = set()
        vertices = set()
        faces = dcel.getFaces()

        featLookup = {}
        l = _graphics.Layer()
        l.flip(90)
        depth = 1000
        for f in faces:
            poly = _graphics.Polygon()
            featLookup[f] = poly
            for e in f.getOuterBoundary():
                poly.addPoint(convertPoint(e.getOrigin()))
                vertices.add(e.getOrigin())
                vertices.add(e.getDest())
                if e.getTwin() not in edges:
                    edges.add(e)

            for inner in f.getInnerComponents():
                for e in inner.getFaceBoundary():
                    vertices.add(e.getOrigin())
                    vertices.add(e.getDest())
                    if e.getTwin() not in edges:
                        edges.add(e)

            for v in f.getIsolatedVertices():
                vertices.add(v)

            if f is not dcel.getExteriorFace() and poly.getNumberOfPoints() > 0:
                color = 'Transparent'
                try:
                    color = f.getData().getColor()
                except:
                    if randomColor:
                        color = _graphics.Color.randomColor()
                if color != 'Transparent':
                    poly.setFillColor(color)
                    poly.setBorderWidth(0)
                    poly.setBorderColor('Transparent')
                    poly.setDepth(depth)
                    depth -= 1
                    l.add(poly)


        for e in edges:
            if e.getTwin() in featLookup:
                featLookup[e] = featLookup[e.getTwin()]
            else:
                path = _graphics.Path(convertPoint(e.getOrigin()),
                                      convertPoint(e.getDest()))
                featLookup[e] = path
                try:
                    color = e.getData().getColor()
                except:
                    color = 'black'
    
                path.setBorderColor(color)
                path.setDepth(depth)
                path.setBorderWidth(edgeWidth)
                l.add(path)

        depth -= 1

        for v in vertices:
            vert = _graphics.Circle(vertRadius, convertPoint(v))
            featLookup[v] = vert
            
            try:
                color = v.getData().getColor()
            except:
                color = 'black'
            vert.setDepth(depth)
            vert.setFillColor(color)
            l.add(vert)
            
        return l,featLookup
                
        
    
except:
    pass
